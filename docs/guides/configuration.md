# Configuration

How to configure skene-growth using config files, environment variables, and CLI flags.

## Configuration priority

Settings are loaded in this order (later overrides earlier):

```
1. User config     ~/.config/skene-growth/config     (lowest priority)
2. Project config  ./.skene-growth.config
3. Env variables   SKENE_API_KEY, SKENE_PROVIDER, etc.
4. CLI flags       --api-key, --provider, etc.        (highest priority)
```

## Config file locations

| Location | Purpose |
|----------|---------|
| `./.skene-growth.config` | Project-level config (per-project settings) |
| `~/.config/skene-growth/config` | User-level config (personal defaults) |

Both files use TOML format. The user-level path respects `XDG_CONFIG_HOME` if set.

## Creating a config file

```bash
# Create .skene-growth.config in the current directory
uvx skene-growth config --init
```

This creates a sample config file with restrictive permissions (`0600` on Unix).

## Interactive editing

Running `config` without flags opens interactive editing:

```bash
uvx skene-growth config
```

This prompts you for:

1. **LLM provider** — numbered list: openai, gemini, anthropic, lmstudio, ollama, generic
2. **Model** — numbered list of provider-specific models, or enter a custom name
3. **Base URL** — only if `generic` provider is selected
4. **API key** — password input (masked), with option to keep existing value

## Viewing current config

```bash
uvx skene-growth config --show
```

Displays all current configuration values and their sources.

## Config options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_key` | string | — | API key for LLM provider |
| `provider` | string | `"openai"` | LLM provider name |
| `model` | string | Per provider | LLM model name |
| `base_url` | string | — | Base URL for OpenAI-compatible endpoints |
| `output_dir` | string | `"./skene-context"` | Default output directory |
| `verbose` | boolean | `false` | Enable verbose output |
| `debug` | boolean | `false` | Enable debug logging |
| `exclude_folders` | list | `[]` | Folder names to exclude from analysis |

### Default models by provider

| Provider | Default model |
|----------|--------------|
| `openai` | `gpt-4o` |
| `gemini` | `gemini-3-flash-preview` |
| `anthropic` | `claude-sonnet-4-5` |
| `ollama` | `llama3.3` |
| `generic` | `custom-model` |

## Sample config file

```toml
# .skene-growth.config

# API key (can also use SKENE_API_KEY env var)
# api_key = "your-api-key"

# LLM provider: openai, gemini, anthropic, claude, lmstudio, ollama, generic
provider = "openai"

# Model (defaults per provider if not set)
# model = "gpt-4o"

# Base URL for OpenAI-compatible endpoints (required for generic provider)
# base_url = "https://your-api.com/v1"

# Default output directory
output_dir = "./skene-context"

# Enable verbose output
verbose = false

# Enable debug logging (logs LLM I/O to .skene-growth/debug/)
debug = false

# Folders to exclude from analysis
# Matches by: exact name, substring in folder names, path patterns
exclude_folders = ["tests", "vendor"]
```

## Environment variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SKENE_API_KEY` | API key for LLM provider | `sk-...` |
| `SKENE_PROVIDER` | Provider name | `gemini` |
| `SKENE_BASE_URL` | Base URL for generic provider | `http://localhost:8000/v1` |
| `SKENE_DEBUG` | Enable debug mode | `true` |
| `LMSTUDIO_BASE_URL` | LM Studio server URL | `http://localhost:1234/v1` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434/v1` |

## Excluding folders

Custom exclusions from both the config file and `--exclude` CLI flags are merged with the built-in defaults.

### Default exclusions

The following directories are always excluded: `node_modules`, `.git`, `__pycache__`, `.venv`, `venv`, `dist`, `build`, `.next`, `.nuxt`, `coverage`, `.cache`, `.idea`, `.vscode`, `.svn`, `.hg`, `.pytest_cache`.

### How matching works

Exclusion matches in three ways:

1. **Exact name** — `"tests"` matches a folder named exactly `tests`
2. **Substring** — `"test"` matches `tests`, `test_utils`, `integration_tests`
3. **Path pattern** — `"tests/unit"` matches any path containing that pattern

### Examples

```bash
# CLI flags (merged with config file exclusions)
uvx skene-growth analyze . --exclude tests --exclude vendor

# Short form
uvx skene-growth analyze . -e planner -e migrations -e docs
```

```toml
# In .skene-growth.config
exclude_folders = ["tests", "vendor", "migrations", "docs"]
```

## Next steps

- [LLM providers](llm-providers.md) — Detailed setup for each provider
- [CLI reference](../reference/cli.md) — All commands and flags
