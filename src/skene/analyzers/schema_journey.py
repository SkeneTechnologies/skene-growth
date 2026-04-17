"""
Schema journey analyzer.

Iteratively discovers the data schema of a codebase and emits a YAML document
shaped like Skene's introspected schema (schema-qualified tables, typed
nullable columns, and FK-style relationships).

Pipeline:
1. DDL prime — detect SQL migrations / ORM schema files and feed their
   contents directly so authoritative ``CREATE TABLE`` statements drive the
   initial state.
2. Grep loop — repeatedly ``rg`` for schema-related patterns and let the LLM
   extend or refine the accumulated schema, suggesting the next keyword.
3. Finalize — one normalization pass that enforces ``schema.table`` names
   and resolves ``relationships``.
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from skene.llm import LLMClient
from skene.output import debug, status, warning

SEED_KEYWORDS: list[str] = [
    "CREATE TABLE",
    "ALTER TABLE",
    "REFERENCES ",
    "FOREIGN KEY",
    "pgTable(",
    "pgSchema(",
    "@Entity",
    "@Table",
    "@ManyToOne",
    "@OneToMany",
    "__tablename__",
    "ForeignKey(",
    "models.Model",
    "db_table",
    "model ",
    "@relation",
    "new Schema(",
    "mongoose.model",
    "BaseModel",
]

DEFAULT_EXCLUDES: list[str] = [
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "coverage",
    ".cache",
]

DDL_GLOBS: list[str] = [
    "**/migrations/*.sql",
    "**/migrations/**/*.sql",
    "**/supabase/migrations/*.sql",
    "**/db/migrate/*.sql",
    "**/drizzle/*.sql",
    "**/schema.sql",
    "prisma/schema.prisma",
    "**/prisma/schema.prisma",
    "**/drizzle/schema.ts",
    "**/db/schema.ts",
    "**/schema/*.ts",
]

DDL_MAX_FILES = 12
DDL_MAX_CHARS_PER_FILE = 12_000


@dataclass
class SchemaState:
    """Accumulated schema knowledge across iterations."""

    tables: dict[str, dict[str, Any]] = field(default_factory=dict)
    explored_keywords: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)

    def to_document(self) -> dict[str, Any]:
        """Return a serialisable dict ready for YAML dump."""
        return {
            "schema_format": "introspection",
            "tables": [
                {"name": name, **payload} for name, payload in sorted(self.tables.items())
            ],
            "notes": list(self.notes),
        }


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

OUTPUT_SHAPE_DOCS = """\
Output shape (STRICT):
{
  "tables": {
    "<schema>.<table>": {
      "description": "one-line description grounded in the snippets",
      "source_files": ["path/to/file"],
      "columns": [
        {
          "name": "id",
          "type": "uuid",
          "nullable": false,
          "primary_key": true,
          "description": "optional"
        }
      ],
      "relationships": [
        {
          "from": "user_id",
          "to": "<schema>.<other_table>.id",
          "kind": "many_to_one | one_to_one | one_to_many | many_to_many"
        }
      ]
    }
  },
  "next_keyword": "<one NEW grep keyword; '' if done>",
  "notes": ["observations that don't fit under tables"]
}

Hard rules:
- Every table key MUST be schema-qualified (default "public." when no schema is obvious).
  Respect explicit schemas found in snippets (e.g. "auth.users", "supabase_migrations.xxx").
- Only include persistent data models (DB tables, Prisma/Drizzle/SQLAlchemy/TypeORM/Django models, CREATE TABLE).
  Do NOT include DTOs, request/response wrappers, config objects, React components, or utility classes.
- "columns[].nullable" MUST be a boolean. Default false if the snippet says NOT NULL.
- "relationships[].to" MUST reference a real column like "public.users.id". Omit if you cannot ground it.
- Never invent columns or tables that are not supported by the snippets.
- EXCLUDE any table whose schema is "skene_growth" or whose name starts with
  "skene_growth" (e.g. ``skene_growth_event_log``). These belong to Skene's
  own instrumentation, not the application being analysed.
- Prefer merging into an existing table over duplicating. Use the exact same "schema.table" casing.
- "next_keyword" must not repeat any keyword already explored.
- Return ONLY the JSON object. No prose, no markdown, no code fences.
"""


DDL_PROMPT_HEAD = """\
You are reverse-engineering the data schema of a codebase.

The following files are authoritative schema sources (SQL migrations, Prisma/Drizzle
schemas, etc). Extract the tables, columns, and foreign-key relationships exactly
as written. Prefer this DDL over anything else you may see later.

Files:
```
{files}
```

"""


REFINE_PROMPT_HEAD = """\
You are reverse-engineering the data schema of a codebase. You are on iteration {iteration} of {total}.

Schema built so far (YAML — authoritative; extend it, do not contradict without strong evidence):
```yaml
{current_schema}
```

Keywords already explored: {explored}

The user just ran grep for "{keyword}" and found these snippets (file:line prefixes preserved):

```
{snippets}
```

"""


FINALIZE_PROMPT_HEAD = """\
You are finalising the reverse-engineered schema below. Do two things:

1. Normalise every table name to "schema.table". Default schema is "public" unless
   the current key or a snippet clearly says otherwise (e.g. "auth.users").
2. For every relationship, make sure "to" is of the form "<schema>.<table>.<column>"
   AND that target table is present in the "tables" map. Drop relationships whose
   target cannot be grounded.

Schema to finalise (YAML):
```yaml
{current_schema}
```

"""


FINALIZE_SHAPE_DOCS = """\
Return ONLY a JSON object of this shape:
{
  "tables": { "<schema>.<table>": { ...same table shape as before... } },
  "notes": ["any follow-up observations"]
}

Rules:
- Do not invent new tables or columns. You may only rename keys to add schema prefixes,
  rewrite relationship targets, and drop unresolvable relationships.
- Return ONLY the JSON object. No prose, no markdown, no code fences.
"""


# ---------------------------------------------------------------------------
# Grep helpers
# ---------------------------------------------------------------------------


def _build_grep_command(
    pattern: str,
    path: Path,
    excludes: list[str],
    context_lines: int,
) -> list[str]:
    """Return a command list that runs rg or grep for the given pattern."""
    rg = shutil.which("rg")
    if rg:
        cmd = [rg, "-F", "-iIn", "--no-heading", f"-C{context_lines}"]
        for ex in excludes:
            cmd += ["--glob", f"!**/{ex}/**"]
        cmd += ["--", pattern, str(path)]
        return cmd

    grep = shutil.which("grep")
    if grep:
        cmd = [grep, "-F", "-riIn", f"-C{context_lines}"]
        for ex in excludes:
            cmd.append(f"--exclude-dir={ex}")
        cmd += ["-e", pattern, str(path)]
        return cmd

    return []


def grep_for_keyword(
    keyword: str,
    path: Path,
    *,
    excludes: list[str],
    max_matches: int = 40,
    context_lines: int = 2,
    timeout: int = 30,
) -> list[str]:
    """Run grep for ``keyword`` and return a list of snippet blocks."""
    cmd = _build_grep_command(keyword, path, excludes, context_lines)
    if not cmd:
        warning("Neither ripgrep (rg) nor grep found on PATH; cannot run schema grep")
        return []

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        debug(f"grep timed out for keyword={keyword!r}")
        return []

    if proc.returncode not in (0, 1):
        debug(f"grep failed for keyword={keyword!r}: {proc.stderr[:200]}")
        return []

    raw = proc.stdout
    blocks = [b.strip() for b in re.split(r"^--$", raw, flags=re.MULTILINE) if b.strip()]
    return blocks[:max_matches]


def _path_is_excluded(p: Path, excludes: list[str]) -> bool:
    parts = {part.lower() for part in p.parts}
    return any(ex.lower() in parts for ex in excludes)


def discover_ddl_files(path: Path, excludes: list[str]) -> list[Path]:
    """Return up to ``DDL_MAX_FILES`` authoritative schema files under ``path``."""
    found: list[Path] = []
    seen: set[Path] = set()
    for pattern in DDL_GLOBS:
        for match in path.glob(pattern):
            if not match.is_file() or match in seen:
                continue
            if _path_is_excluded(match, excludes):
                continue
            seen.add(match)
            found.append(match)
            if len(found) >= DDL_MAX_FILES:
                return found
    return found


def _read_file_snippet(file: Path, base: Path, max_chars: int) -> str:
    try:
        content = file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if len(content) > max_chars:
        content = content[:max_chars] + "\n-- [truncated] --"
    try:
        rel = file.relative_to(base)
    except ValueError:
        rel = file
    return f"# ===== {rel} =====\n{content}"


# ---------------------------------------------------------------------------
# LLM response parsing / merging
# ---------------------------------------------------------------------------

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", re.MULTILINE)


def _parse_json(text: str) -> dict[str, Any] | None:
    """Best-effort JSON extraction from an LLM response."""
    text = (text or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass

    m = _JSON_FENCE_RE.search(text)
    if m:
        try:
            data = json.loads(m.group(1))
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            pass

    return None


def _is_skene_growth_table(name: str) -> bool:
    """True when a normalised ``schema.table`` belongs to Skene's own growth plane.

    Skene-managed objects (``skene_growth`` schema, ``skene_growth_event_log``
    table, etc.) describe instrumentation installed by Skene itself and are
    never part of the analysed product's application schema, so they are
    excluded from ``schema.yaml``.
    """
    n = (name or "").lower()
    if not n:
        return False
    schema, _, table = n.partition(".")
    if schema == "skene_growth" or schema.startswith("skene_growth_"):
        return True
    return table.startswith("skene_growth")


def _relationship_targets_skene_growth(rel: dict[str, Any]) -> bool:
    """True when a relationship ``to`` points into the Skene-managed schema."""
    target = rel.get("to")
    if not isinstance(target, str):
        return False
    parts = target.split(".")
    if len(parts) < 2:
        return False
    table_ref = ".".join(parts[:-1]) if len(parts) >= 3 else parts[0]
    return _is_skene_growth_table(table_ref)


def _normalise_table_name(raw: str, default_schema: str = "public") -> str:
    """Ensure the table key is ``schema.table``; default to ``public.`` when missing."""
    name = (raw or "").strip().strip('"').strip("`")
    if not name:
        return name
    if "." in name:
        # Accept "schema.table" only; strip further qualifiers like DB names.
        parts = name.split(".")
        if len(parts) >= 2 and parts[-2] and parts[-1]:
            return f"{parts[-2]}.{parts[-1]}".lower()
    return f"{default_schema}.{name}".lower()


def _coerce_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("true", "1", "yes", "y"):
            return True
        if v in ("false", "0", "no", "n"):
            return False
    return default


def _merge_tables(state: SchemaState, tables: dict[str, Any]) -> None:
    """Fold newly extracted tables into the running state in place."""
    if not isinstance(tables, dict):
        return

    for raw_name, payload in tables.items():
        if not isinstance(raw_name, str) or not isinstance(payload, dict):
            continue

        name = _normalise_table_name(raw_name)
        if not name:
            continue
        if _is_skene_growth_table(name):
            continue

        existing = state.tables.setdefault(
            name,
            {
                "description": "",
                "source_files": [],
                "columns": [],
                "relationships": [],
            },
        )

        if desc := payload.get("description"):
            if isinstance(desc, str) and (
                not existing.get("description") or len(desc) > len(existing["description"])
            ):
                existing["description"] = desc

        for col in payload.get("columns") or []:
            if not isinstance(col, dict):
                continue
            cname = col.get("name")
            if not isinstance(cname, str) or not cname:
                continue
            entry = {
                "name": cname,
                "type": col.get("type") or "unknown",
                "nullable": _coerce_bool(col.get("nullable"), default=True),
                "primary_key": _coerce_bool(col.get("primary_key"), default=False),
            }
            if col.get("description"):
                entry["description"] = col["description"]
            existing_col = next(
                (c for c in existing["columns"] if c.get("name") == cname),
                None,
            )
            if existing_col is None:
                existing["columns"].append(entry)
            else:
                # Upgrade with any newly-known detail (never overwrite with "unknown").
                if entry["type"] != "unknown" and existing_col.get("type") == "unknown":
                    existing_col["type"] = entry["type"]
                if entry["primary_key"]:
                    existing_col["primary_key"] = True
                if existing_col.get("nullable") is None:
                    existing_col["nullable"] = entry["nullable"]
                if "description" in entry and "description" not in existing_col:
                    existing_col["description"] = entry["description"]

        for src in payload.get("source_files") or []:
            if isinstance(src, str) and src not in existing["source_files"]:
                existing["source_files"].append(src)

        for rel in payload.get("relationships") or []:
            if not isinstance(rel, dict):
                continue
            rel_from = rel.get("from")
            rel_to = rel.get("to")
            if not isinstance(rel_from, str) or not isinstance(rel_to, str):
                continue
            norm_rel = {
                "from": rel_from,
                "to": rel_to,
                "kind": rel.get("kind") or "many_to_one",
            }
            if _relationship_targets_skene_growth(norm_rel):
                continue
            if norm_rel not in existing["relationships"]:
                existing["relationships"].append(norm_rel)


def _apply_finalisation(state: SchemaState, parsed: dict[str, Any]) -> None:
    """Apply the finalize-pass output over the running state."""
    tables = parsed.get("tables")
    if isinstance(tables, dict) and tables:
        new_state: dict[str, dict[str, Any]] = {}
        for raw_name, payload in tables.items():
            if not isinstance(payload, dict):
                continue
            name = _normalise_table_name(raw_name)
            if _is_skene_growth_table(name):
                continue
            new_state[name] = {
                "description": payload.get("description", "") or "",
                "source_files": list(payload.get("source_files") or []),
                "columns": [c for c in (payload.get("columns") or []) if isinstance(c, dict)],
                "relationships": [
                    r
                    for r in (payload.get("relationships") or [])
                    if isinstance(r, dict) and not _relationship_targets_skene_growth(r)
                ],
            }
        # Preserve any source_files the finalize pass forgot.
        for name, prev in state.tables.items():
            if _is_skene_growth_table(name):
                continue
            merged = new_state.setdefault(
                name,
                {"description": "", "source_files": [], "columns": [], "relationships": []},
            )
            for src in prev.get("source_files", []):
                if src not in merged["source_files"]:
                    merged["source_files"].append(src)
        state.tables = new_state

    for n in parsed.get("notes") or []:
        if isinstance(n, str) and n not in state.notes:
            state.notes.append(n)


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------


def _join_blocks(blocks: list[str], max_chars: int) -> str:
    joined = "\n\n---\n\n".join(blocks)
    if len(joined) > max_chars:
        joined = joined[:max_chars] + "\n\n...[truncated]"
    return joined


def _next_keyword(queue: list[str], explored: set[str]) -> str | None:
    while queue:
        k = queue.pop(0)
        if k and k.strip() and k not in explored:
            return k
    return None


def write_schema_yaml(path: Path, state: SchemaState) -> None:
    """Write the accumulated schema state to a YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "version": datetime.now().strftime("%Y.%m.%d"),
        "generated_by": "skene analyse-journey",
        **state.to_document(),
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, sort_keys=False, default_flow_style=False)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


async def _ddl_prime_step(
    *,
    path: Path,
    llm: LLMClient,
    excludes: list[str],
    state: SchemaState,
    max_snippet_chars: int,
) -> None:
    ddl_files = await asyncio.to_thread(discover_ddl_files, path, excludes)
    if not ddl_files:
        status("Priming: no migration / ORM schema files found, skipping")
        return

    status(f"Priming: reading schema file(s)")
    parts: list[str] = []
    for f in ddl_files:
        snippet = _read_file_snippet(f, path, DDL_MAX_CHARS_PER_FILE)
        if snippet:
            parts.append(snippet)
    combined = "\n\n".join(parts)
    if len(combined) > max_snippet_chars * 2:
        combined = combined[: max_snippet_chars * 2] + "\n\n[truncated]"

    prompt = DDL_PROMPT_HEAD.format(files=combined) + OUTPUT_SHAPE_DOCS
    try:
        response = await llm.generate_content(prompt)
    except Exception as e:
        warning(f"Priming LLM call failed: {e}")
        return

    parsed = _parse_json(response)
    if parsed is None:
        warning("Could not parse priming response")
        return

    before = len(state.tables)
    _merge_tables(state, parsed.get("tables") or {})
    added = len(state.tables) - before
    status(f"Priming: {added} new table(s), {len(state.tables)} total")

    for n in parsed.get("notes") or []:
        if isinstance(n, str) and n not in state.notes:
            state.notes.append(n)


async def _finalize_step(
    *,
    llm: LLMClient,
    state: SchemaState,
) -> None:
    if not state.tables:
        return

    status("Finalising schema (schema-qualify names, resolve relationships)")
    prompt = (
        FINALIZE_PROMPT_HEAD.format(
            current_schema=yaml.safe_dump(state.to_document(), sort_keys=False) or "{}",
        )
        + FINALIZE_SHAPE_DOCS
    )
    try:
        response = await llm.generate_content(prompt)
    except Exception as e:
        warning(f"Finalize LLM call failed: {e}")
        return

    parsed = _parse_json(response)
    if parsed is None:
        warning("Could not parse finalize response")
        return

    _apply_finalisation(state, parsed)


async def analyse_journey(
    *,
    path: Path,
    llm: LLMClient,
    output_path: Path,
    iterations: int = 6,
    excludes: list[str] | None = None,
    max_snippet_chars: int = 8000,
    max_matches_per_keyword: int = 40,
) -> SchemaState:
    """Iteratively build a Skene-shaped schema document for a codebase.

    Phases:
    1. DDL prime — feeds authoritative migration / ORM schema files to the LLM.
    2. Grep loop — up to ``iterations`` keyword-driven refinement passes.
    3. Finalize — one normalisation pass (schema-qualified names, relationships).

    The document is written to ``output_path`` even on failure.
    """
    excludes = list(excludes) if excludes else list(DEFAULT_EXCLUDES)
    state = SchemaState()
    queue: list[str] = list(SEED_KEYWORDS)

    try:
        await _ddl_prime_step(
            path=path,
            llm=llm,
            excludes=excludes,
            state=state,
            max_snippet_chars=max_snippet_chars,
        )

        for i in range(1, iterations + 1):
            keyword = _next_keyword(queue, state.explored_keywords)
            if keyword is None:
                status(f"analyse-journey: keyword queue exhausted at iteration {i - 1}")
                break

            state.explored_keywords.add(keyword)

            blocks = await asyncio.to_thread(
                grep_for_keyword,
                keyword,
                path,
                excludes=excludes,
                max_matches=max_matches_per_keyword,
            )

            if not blocks:
                status(f"[{i}/{iterations}] grep {keyword!r} → 0 matches, skipping")
                continue

            status(f"[{i}/{iterations}] grep {keyword!r} → {len(blocks)} matches, analysing")

            prompt = (
                REFINE_PROMPT_HEAD.format(
                    iteration=i,
                    total=iterations,
                    current_schema=yaml.safe_dump(state.to_document(), sort_keys=False) or "{}",
                    explored=sorted(state.explored_keywords),
                    keyword=keyword,
                    snippets=_join_blocks(blocks, max_chars=max_snippet_chars),
                )
                + OUTPUT_SHAPE_DOCS
            )

            try:
                response = await llm.generate_content(prompt)
            except Exception as e:
                warning(f"LLM call failed for keyword {keyword!r}: {e}")
                continue

            parsed = _parse_json(response)
            if parsed is None:
                warning(f"Could not parse LLM response for keyword {keyword!r}")
                continue

            before = len(state.tables)
            _merge_tables(state, parsed.get("tables") or {})
            added = len(state.tables) - before
            status(f"         → {added} new table(s), {len(state.tables)} total")

            for n in parsed.get("notes") or []:
                if isinstance(n, str) and n not in state.notes:
                    state.notes.append(n)

            next_keyword = parsed.get("next_keyword")
            if isinstance(next_keyword, str):
                next_keyword = next_keyword.strip()
                if next_keyword and next_keyword not in state.explored_keywords:
                    queue.append(next_keyword)

        await _finalize_step(llm=llm, state=state)
    finally:
        write_schema_yaml(output_path, state)

    return state
