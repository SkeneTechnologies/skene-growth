# Tech Debt Cleanup Plan

## Overview

The codebase accumulated tech debt from heavy use of gen AI coding tools. This plan addresses the main issues in priority order.

## 1. Remove chat command and MCP server

**Status:** To do

We decided we don't want the chat command or MCP server functionality.

**Files to delete:**
- `src/skene/cli/chat.py` (344 lines)
- `src/skene/mcp/server.py` (93 lines)
- `src/skene/mcp/registry.py` (466 lines)
- `src/skene/mcp/tools.py` (1,030 lines)
- `src/skene/mcp/cache.py` (345 lines)
- `src/skene/mcp/__init__.py` (26 lines)
- `tests/mcp/` directory

**Code to remove in other files:**
- Chat command definition in `cli/main.py` (~lines 741-840)
- `_run_chat_default` helper in `cli/main.py`
- `skene_growth_mcp_entry()` in `cli/main.py`
- `skene-mcp` and `skene-growth-mcp` entry points from `pyproject.toml`
- `mcp` optional dependency from `pyproject.toml`
- Chat/MCP references in `cli/__init__.py` docstring
- MCP-related docs (`docs/integrations/`, `docs/guides/chat.md`)
- Deprecated `generate` command (26 lines) — remove while we're here

**Total: ~2,300+ lines removed.**

## 2. Split `cli/main.py` into per-command files

**Status:** To do

The file is 2,081 lines with 11 commands. Each command should live in its own module.

**Proposed structure:**
```
cli/
├── __init__.py
├── app.py               # Typer app creation, entry points, shared config resolution helper
├── commands/
│   ├── __init__.py
│   ├── analyze.py
│   ├── plan.py
│   ├── build.py         # build + _build_async
│   ├── status.py
│   ├── push.py
│   ├── validate.py
│   ├── config.py
│   ├── login.py         # login + logout
│   └── features.py
├── analysis_helpers.py  # keep as-is
├── auth.py              # keep as-is
├── config_manager.py    # keep as-is
├── output_writers.py    # keep as-is
├── prompt_builder.py    # keep as-is
├── sample_report.py     # keep as-is
```

**Extract shared helper** for the config resolution block duplicated 5-6 times, the local-provider check (4 occurrences), and the generic-provider validation (4 occurrences).

## 3. Move hardcoded prompts to Jinja2 templates

**Status:** To do

~20+ prompt strings scattered across 8 files. Centralize into template files.

**Proposed structure:**
```
src/skene/prompts/
├── __init__.py           # load_prompt(name, **vars) helper
├── templates/
│   ├── tech_stack.j2
│   ├── growth_features.j2
│   ├── manifest.j2
│   ├── industry.j2
│   ├── product_overview.j2
│   ├── features.j2
│   ├── council_role.j2
│   ├── executive_summary.j2
│   ├── plan_section.j2
│   ├── technical_execution.j2
│   ├── activation_memo.j2
│   ├── objectives.j2
│   ├── todo_list.j2
│   ├── cursor_prompt.j2
│   ├── parse_steps.j2
│   └── growth_template.j2
```

Benefits: version-controllable prompts, easy diffing, Jinja2 variables for dynamic parts, separation of prompt engineering from Python code.

## 4. Create `types.py` for shared type aliases

**Status:** To do

Replace messy inline type hints like `tuple[str, dict[str, int] | None]` with named types.

**Create `src/skene/types.py`:**
```python
from typing import TypeAlias, Callable, Any

UsageStats: TypeAlias = dict[str, int]
LLMResponse: TypeAlias = tuple[str, UsageStats | None]
StepCallback: TypeAlias = Callable[[int, str, str, UsageStats | None], None]
GrowthLoopData: TypeAlias = dict[str, Any]
GrowthLoopList: TypeAlias = list[GrowthLoopData]
EventPayload: TypeAlias = dict[str, Any]
```

Update `LLMClient` base class and all 6 provider implementations.

## 5. Rename/reorganize template folders

**Status:** To do

Three "template" directories exist with confusing naming:
- `src/skene/docs/templates/` — Jinja2 output templates → **keep as-is** (scoped under `docs/`)
- `src/skene/templates/` — Python module for LLM-driven template generation → **rename to `src/skene/template_generator/`**
- `src/templates/` — Static JSON example data → **move to `src/skene/template_generator/examples/`**

## 6. Continue output cleanup

**Status:** In progress (branch `feat/output-cleanup`)

Already planned in `docs/plans/output-cleanup.md`. Centralized output module exists. Continue migration of remaining files.

## 7. Other cleanup

- **`benchmarks/run.py` (7,833 lines)** — split into modules (lower priority)
- **`skene-context/` at project root** — self-analysis data, consider `.gitignore`-ing
- **`pypi-shim/` package** — verify still needed
- **Dead code sweep** — final pass after above refactors
