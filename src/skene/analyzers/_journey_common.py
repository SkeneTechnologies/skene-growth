"""
Shared helpers for the journey pipeline (schema → growth → plan).

Consolidates utilities that previously lived as underscore-prefixed imports
across ``schema_journey``, ``growth_from_schema`` and ``plan_engine``:

- ripgrep / grep runner
- JSON extraction from LLM responses
- file-snippet reading and discovery
- ``skene_growth*`` filter (Skene's own instrumentation, never part of an
  application schema)
- ``DEFAULT_EXCLUDES`` list used by every grep in the pipeline
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from skene.output import debug, warning

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


# ---------------------------------------------------------------------------
# Skene-managed table filter
# ---------------------------------------------------------------------------


def is_skene_growth_table(name: str) -> bool:
    """True when a normalised ``schema.table`` belongs to Skene's own growth plane.

    Skene-managed objects (``skene_growth`` schema, ``skene_growth_event_log``
    table, etc.) describe instrumentation installed by Skene itself and are
    never part of the analysed product's application schema.
    """
    n = (name or "").lower()
    if not n:
        return False
    schema, _, table = n.partition(".")
    if schema == "skene_growth" or schema.startswith("skene_growth_"):
        return True
    return table.startswith("skene_growth")


def relationship_targets_skene_growth(rel: dict[str, Any]) -> bool:
    """True when a relationship ``to`` points into a Skene-managed table."""
    target = rel.get("to")
    if not isinstance(target, str):
        return False
    parts = target.split(".")
    if len(parts) < 2:
        return False
    table_ref = ".".join(parts[:-1]) if len(parts) >= 3 else parts[0]
    return is_skene_growth_table(table_ref)


def source_targets_skene_growth(source: str) -> bool:
    """True when an engine feature ``source`` (``schema.table.op``) is Skene-managed."""
    parts = (source or "").split(".")
    if len(parts) < 2:
        return False
    return is_skene_growth_table(".".join(parts[:2]))


# ---------------------------------------------------------------------------
# Grep
# ---------------------------------------------------------------------------


def _build_grep_command(
    pattern: str,
    path: Path,
    excludes: list[str],
    context_lines: int,
) -> list[str]:
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
    """Run ripgrep (or grep) for ``keyword`` and return snippet blocks."""
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

    blocks = [b.strip() for b in re.split(r"^--$", proc.stdout, flags=re.MULTILINE) if b.strip()]
    return blocks[:max_matches]


def join_blocks(blocks: list[str], max_chars: int) -> str:
    """Concatenate grep snippet blocks, truncating to ``max_chars``."""
    joined = "\n\n---\n\n".join(blocks)
    if len(joined) > max_chars:
        joined = joined[:max_chars] + "\n\n...[truncated]"
    return joined


# ---------------------------------------------------------------------------
# File discovery / snippet reading
# ---------------------------------------------------------------------------


def _path_is_excluded(p: Path, excludes: list[str]) -> bool:
    parts = {part.lower() for part in p.parts}
    return any(ex.lower() in parts for ex in excludes)


def discover_files_by_globs(
    path: Path,
    globs: list[str],
    excludes: list[str],
    max_files: int,
) -> list[Path]:
    """Return up to ``max_files`` files under ``path`` matching any of ``globs``."""
    found: list[Path] = []
    seen: set[Path] = set()
    for pattern in globs:
        for match in path.glob(pattern):
            if not match.is_file() or match in seen:
                continue
            if _path_is_excluded(match, excludes):
                continue
            seen.add(match)
            found.append(match)
            if len(found) >= max_files:
                return found
    return found


def read_file_snippet(file: Path, base: Path, max_chars: int) -> str:
    """Return a labelled, length-capped snippet of ``file`` for prompt inclusion."""
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
# JSON extraction from LLM responses
# ---------------------------------------------------------------------------

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", re.MULTILINE)


def parse_json(text: str) -> dict[str, Any] | None:
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
