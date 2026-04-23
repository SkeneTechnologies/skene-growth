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
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from skene.analyzers._journey_common import (
    DEFAULT_EXCLUDES,
    discover_files_by_globs,
    grep_for_keyword,
    is_skene_growth_table,
    join_blocks,
    parse_json,
    read_file_snippet,
    relationship_targets_skene_growth,
)
from skene.llm import LLMClient
from skene.output import status, warning

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
            "tables": [{"name": name, **payload} for name, payload in sorted(self.tables.items())],
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
# Normalisation / merging
# ---------------------------------------------------------------------------


def _normalise_table_name(raw: str, default_schema: str = "public") -> str:
    """Ensure the table key is ``schema.table``; default to ``public.`` when missing."""
    name = (raw or "").strip().strip('"').strip("`")
    if not name:
        return name
    if "." in name:
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
        if not name or is_skene_growth_table(name):
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
            if isinstance(desc, str) and (not existing.get("description") or len(desc) > len(existing["description"])):
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
            if relationship_targets_skene_growth(norm_rel):
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
            if is_skene_growth_table(name):
                continue
            new_state[name] = {
                "description": payload.get("description", "") or "",
                "source_files": list(payload.get("source_files") or []),
                "columns": [c for c in (payload.get("columns") or []) if isinstance(c, dict)],
                "relationships": [
                    r
                    for r in (payload.get("relationships") or [])
                    if isinstance(r, dict) and not relationship_targets_skene_growth(r)
                ],
            }
        for name, prev in state.tables.items():
            if is_skene_growth_table(name):
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
# I/O
# ---------------------------------------------------------------------------


def write_schema_yaml(path: Path, state: SchemaState) -> None:
    """Write the accumulated schema state to a YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "generated_at": datetime.now().isoformat(),
        "generated_by": "skene analyse-journey",
        **state.to_document(),
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, sort_keys=False, default_flow_style=False)


def _next_keyword(queue: list[str], explored: set[str]) -> str | None:
    """Pop the next unexplored keyword off the queue."""
    lowered_explored = {e.lower() for e in explored}
    while queue:
        k = queue.pop(0)
        if k and k.strip() and k.lower() not in lowered_explored:
            return k
    return None


# ---------------------------------------------------------------------------
# Pipeline stages
# ---------------------------------------------------------------------------


async def _ddl_prime_step(
    *,
    path: Path,
    llm: LLMClient,
    excludes: list[str],
    state: SchemaState,
    max_snippet_chars: int,
) -> None:
    ddl_files = await asyncio.to_thread(discover_files_by_globs, path, DDL_GLOBS, excludes, DDL_MAX_FILES)
    if not ddl_files:
        status("Priming: no migration / ORM schema files found, skipping")
        return

    status(f"Priming: reading {len(ddl_files)} schema file(s)")
    parts = [read_file_snippet(f, path, DDL_MAX_CHARS_PER_FILE) for f in ddl_files]
    combined = "\n\n".join(p for p in parts if p)
    if len(combined) > max_snippet_chars * 2:
        combined = combined[: max_snippet_chars * 2] + "\n\n[truncated]"

    prompt = DDL_PROMPT_HEAD.format(files=combined) + OUTPUT_SHAPE_DOCS
    try:
        response = await llm.generate_content(prompt)
    except Exception as e:
        warning(f"Priming LLM call failed: {e}")
        return

    parsed = parse_json(response)
    if parsed is None:
        warning("Could not parse priming response")
        return

    before = len(state.tables)
    _merge_tables(state, parsed.get("tables") or {})
    status(f"Priming: {len(state.tables) - before} new table(s), {len(state.tables)} total")

    for n in parsed.get("notes") or []:
        if isinstance(n, str) and n not in state.notes:
            state.notes.append(n)


async def _finalize_step(*, llm: LLMClient, state: SchemaState) -> None:
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

    parsed = parse_json(response)
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
                status(f"Keyword queue exhausted at iteration {i - 1}")
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
                    snippets=join_blocks(blocks, max_chars=max_snippet_chars),
                )
                + OUTPUT_SHAPE_DOCS
            )

            try:
                response = await llm.generate_content(prompt)
            except Exception as e:
                warning(f"LLM call failed for keyword {keyword!r}: {e}")
                continue

            parsed = parse_json(response)
            if parsed is None:
                warning(f"Could not parse LLM response for keyword {keyword!r}")
                continue

            before = len(state.tables)
            _merge_tables(state, parsed.get("tables") or {})
            status(f"         → {len(state.tables) - before} new table(s), {len(state.tables)} total")

            for n in parsed.get("notes") or []:
                if isinstance(n, str) and n not in state.notes:
                    state.notes.append(n)

            next_keyword = parsed.get("next_keyword")
            if isinstance(next_keyword, str):
                next_keyword = next_keyword.strip()
                if next_keyword and next_keyword.lower() not in {e.lower() for e in state.explored_keywords}:
                    # LLM-suggested keyword jumps to the head of the queue — it
                    # was picked because the model thinks it's most productive
                    # right now.
                    queue.insert(0, next_keyword)

        await _finalize_step(llm=llm, state=state)
    finally:
        write_schema_yaml(output_path, state)

    return state
