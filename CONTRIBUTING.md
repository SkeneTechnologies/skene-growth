# Contributing to Skene

Thank you for contributing to Skene! This guide covers the conventions you need to follow when working on the codebase.

## Getting Started

```bash
# Clone and install
git clone git@github.com:SkeneTechnologies/skene.git
cd skene
uv sync

# Run tests
uv run pytest tests/

# Run the CLI
uv run skene --help
```

## Output and Logging

All terminal output and logging goes through the centralised `skene.output` module. **Do not** create your own `Console()` instances, use `print()`, or configure stdlib `logging` in application code.

### The rules

1. **Import from `skene.output`**, never from `rich.console` directly (except for type hints).

   ```python
   from skene.output import status, success, error, warning, debug
   ```

2. **Use the right function for the message type:**

   | Function    | When to use                                  | Visible in quiet mode? |
   |-------------|----------------------------------------------|------------------------|
   | `status()`  | Progress updates, informational messages      | No                     |
   | `success()` | Something completed successfully              | No                     |
   | `warning()` | Non-fatal problems                            | No                     |
   | `error()`   | Errors (always shown)                         | Yes                    |
   | `debug()`   | Diagnostic detail (only shown with `--debug`) | No                     |

3. **For Rich UI** (Tables, Panels, Markdown, progress bars), import the shared console:

   ```python
   from skene.output import console

   console.print(table)          # Tables, Panels, etc.
   console.print(Markdown(text)) # Rendered markdown
   ```

   Only use `console.print()` when you need Rich formatting that the output functions don't support.

4. **Never use:**
   - `print()` — bypasses the shared console and logging
   - `Console()` — creates a separate instance that ignores verbosity
   - `logging.getLogger()` — we use loguru via `skene.output`, not stdlib logging

5. **Everything is logged to file.** Every call to `status()`, `success()`, etc. also writes to `~/.local/state/skene/skene.log` via loguru, regardless of verbosity level. This is intentional.

### Verbosity levels

The CLI has three verbosity levels controlled by `--quiet` and `--debug` flags:

- **Quiet** (`--quiet`): only `error()` prints to screen
- **Normal** (default): `status()`, `success()`, `warning()`, `error()` print to screen
- **Debug** (`--debug`): all of the above plus `debug()` prints to screen

When adding a new command, wire up verbosity in the command function:

```python
from skene.output import set_debug, set_quiet

if quiet:
    set_quiet()
elif resolved_debug:
    set_debug()
```

## Code Style

- Run the following before submitting a PR:
  ```bash
  uv run ruff check .
  uv run ruff format --check .
  uv run pytest tests/
  ```
- Keep changes focused — don't refactor surrounding code unless it's part of your task
- Prefer editing existing files over creating new ones

## Pull Requests

- Create a feature branch from `main`
- Keep PRs focused on a single change
- Include a test plan in the PR description
