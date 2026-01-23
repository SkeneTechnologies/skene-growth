# skene-growth

PLG (Product-Led Growth) analysis toolkit for codebases. Analyze your code, detect growth opportunities, and generate documentation of your stack.

## Quick Start

**No installation required** - just run with [uvx](https://docs.astral.sh/uv/):

```bash
#install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Analyze your codebase
uvx skene-growth analyze . --api-key "your-openai-api-key"

# Or set the API key as environment variable
export SKENE_API_KEY="your-openai-api-key"
uvx skene-growth analyze .
```

Get an OpenAI API key at: https://platform.openai.com/api-keys

## What It Does

skene-growth scans your codebase and generates a **growth manifest** containing:

- **Tech Stack Detection** - Framework, language, database, auth, deployment
- **Growth Hubs** - Features with growth potential (signup flows, sharing, invites, billing)
- **GTM Gaps** - Missing features that could drive user acquisition and retention

With the `--product-docs` flag, it also collects:

- **Product Overview** - Tagline, value proposition, target audience
- **Features** - User-facing feature documentation with descriptions and examples
- **Product Docs** - Generates user-friendly product-docs.md file

After the manifest is created, skene-growth generates a **custom growth template** (JSON + Markdown)
tailored to your business type using LLM analysis. The templates use examples in `src/templates/` as 
reference but create custom lifecycle stages and keywords specific to your product.

## Installation

### Option 1: uvx (Recommended)

Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Zero installation - runs instantly (requires API key):

```bash
uvx skene-growth analyze . --api-key "your-openai-api-key"
uvx skene-growth validate ./growth-manifest.json
```

> **Note:** The `analyze` command requires an API key. By default, it uses OpenAI (get a key at https://platform.openai.com/api-keys). You can also use Gemini with `--provider gemini`, Anthropic with `--provider anthropic`, or local LLMs with `--provider lmstudio` or `--provider ollama` (experimental).

### Option 2: pip install

```bash
pip install skene-growth
```

## How to use?

skene-growth follows a four-step workflow designed to progressively build AI context, track growth objectives, and generate actionable implementation plans:

1. **Analyze** - Establishes the foundation by analyzing your codebase and generating a comprehensive growth manifest. This creates the general AI context about your codebase structure, technology stack, user journey, and growth opportunities. The output includes growth hubs, GTM gaps, and a custom growth template tailored to your business type.

2. **Objectives** - Uses the manifest and template to generate 3 prioritized growth objectives. This step focuses the AI's attention on specific, actionable goals based on your lifecycle stages and identified gaps. You can guide the objective selection with prompts to emphasize particular areas like onboarding or retention.

3. **Daily Logs** - Tracks the current status of your objectives by fetching metrics from configured data sources. This provides real-time feedback to the AI about how your objectives are performing, enabling data-driven decision making and progress monitoring.

4. **Plan** - Generates a growth plan by selecting and mapping growth loops to your codebase. When objectives and daily logs are available, it uses LLM-based intelligent selection to choose 3 targeted loops. Otherwise, it performs comprehensive mapping of all applicable loops from the catalog. The output is an actionable implementation plan with specific steps and success metrics.

Together, these commands create a continuous feedback loop: analyze establishes context, objectives define focus, daily logs provide status updates, and plan generates actionable implementation steps to keep your growth strategy aligned with actual performance.

## CLI Commands

### `analyze` - Analyze a codebase

Requires an API key (set via `--api-key`, `SKENE_API_KEY` env var, or config file).

```bash
# Analyze current directory (uses OpenAI by default)
uvx skene-growth analyze . --api-key "your-openai-api-key"

# Using environment variable
export SKENE_API_KEY="your-openai-api-key"
uvx skene-growth analyze .

# Analyze specific path with custom output
uvx skene-growth analyze ./my-project -o manifest.json

# With verbose output
uvx skene-growth analyze . -v

# Use a specific model
uvx skene-growth analyze . --model gpt-4o

# Use Gemini instead of OpenAI
uvx skene-growth analyze . --provider gemini --api-key "your-gemini-api-key"

# Use Anthropic (Claude)
uvx skene-growth analyze . --provider anthropic --api-key "your-anthropic-api-key"

# Use LM Studio (local server)
uvx skene-growth analyze . --provider lmstudio --model "your-loaded-model"

# Use Ollama (local server) - Experimental
uvx skene-growth analyze . --provider ollama --model "llama2"

# Specify business type for custom growth template
uvx skene-growth analyze . --business-type "design-agency"
uvx skene-growth analyze . --business-type "b2b-saas"

# Generate product documentation (collects product overview and features)
uvx skene-growth analyze . --product-docs
```

**Output:**
- `./skene-context/growth-manifest.json` (structured data)
- `./skene-context/growth-manifest.md` (analysis summary)
- `./skene-context/growth-template.json` (if --business-type specified)
- `./skene-context/growth-template.md` (if --business-type specified)
- `./skene-context/product-docs.md` (if --product-docs flag used)

**Growth Templates:** The system generates custom templates tailored to your business type, with
lifecycle stages and keywords specific to your user journey. If no business type is specified,
the LLM infers it from your codebase.

**Flags:**
- `--product-docs`: Generate user-friendly product documentation (collects product overview, features, and generates product-docs.md)
- `--business-type`: Specify business type for custom growth template

The `--product-docs` flag enables enhanced analysis mode which collects product overview and feature documentation, producing a v2.0 manifest with additional fields and a user-friendly product-docs.md file.

### `validate` - Validate a manifest

```bash
uvx skene-growth validate ./growth-manifest.json
```

### `objectives` - Generate growth objectives

Generate 3 prioritized growth objectives from your manifest and template. This command reads existing `growth-manifest.json` and `growth-template.json` files, then uses an LLM to generate targeted growth objectives based on lifecycle stages and identified gaps.

**Prerequisites:**
- Run `skene-growth analyze` first to generate `growth-manifest.json` and `growth-template.json`
- These files should be in `./skene-context/` or you can specify their paths

```bash
# Generate objectives (auto-detects manifest and template from ./skene-context/)
uvx skene-growth objectives --api-key "your-api-key"

# Specify quarter label
uvx skene-growth objectives --quarter "Q1 2024"

# With prompt to focus on specific areas
uvx skene-growth objectives -p "I want all objectives to focus on onboarding"
uvx skene-growth objectives --prompt "Prioritize retention metrics"

# With specific manifest and template files
uvx skene-growth objectives --manifest ./my-manifest.json --template ./my-template.json

# Use different provider/model
uvx skene-growth objectives --provider gemini --model gemini-2.0-flash

# Custom output path
uvx skene-growth objectives -o ./my-objectives.md
```

**Output:**
- `./skene-context/growth-objectives.md` (default) or custom path specified with `-o`

**Flags:**
- `-p, --prompt`: Prompt text to influence objective selection (e.g., "Focus on onboarding" or "Prioritize retention metrics")
- `-q, --quarter`: Quarter label (e.g., "Q1", "Q2 2024")
- `-o, --output`: Output path for growth-objectives.md (default: `./skene-context/growth-objectives.md`)
- `--manifest`: Path to growth-manifest.json (auto-detected if not specified)
- `--template`: Path to growth-template.json (auto-detected if not specified)
- `--api-key`: API key for LLM provider (or set SKENE_API_KEY env var)
- `--provider`: LLM provider to use (openai, gemini, anthropic, ollama)
- `-m, --model`: LLM model name
- `-v, --verbose`: Enable verbose output

### `plan` - Generate growth plan

Generate a growth plan by mapping growth loops to codebase. This command has conditional behavior based on available context files.

**Conditional Behavior:**
- If `objectives.md` AND `daily_logs/` exist: Uses LLM-based intelligent selection (selects 3 loops)
- Otherwise: Uses comprehensive mapping (all applicable loops from catalog)

**Prerequisites:**
- `growth-manifest.json` file (generated by the `analyze` command)
- For LLM mode: `growth-objectives.md` file AND `daily_logs/` directory

```bash
# Generate growth plan (auto-detects mode based on available files)
uvx skene-growth plan

# Use custom loops from CSV
uvx skene-growth plan --csv loops.csv

# Specify manifest and use LLM mode
uvx skene-growth plan --manifest ./manifest.json --api-key "your-key"

# Use different provider/model
uvx skene-growth plan --provider gemini --model gemini-2.0-flash

# Specify custom paths
uvx skene-growth plan --objectives ./my-objectives.md --daily-logs ./my-logs
```

**Output:**
- `./skene-context/skene-growth-plan.md` (default) or custom path specified with `-o`

**Flags:**
- `-m, --manifest`: Path to growth-manifest.json (auto-detected if not specified)
- `--objectives`: Path to growth-objectives.md (auto-detected if not specified)
- `--daily-logs`: Path to daily_logs directory (auto-detected if not specified)
- `--csv`: Path to custom growth loops CSV file (uses built-in if not specified)
- `-o, --output`: Output path for growth plan (markdown format)
- `--api-key`: API key for LLM provider (or set SKENE_API_KEY env var, required for LLM mode)
- `-p, --provider`: LLM provider to use (openai, gemini, anthropic, ollama)
- `-m, --model`: LLM model name
- `-v, --verbose`: Enable verbose output

### `daily-logs` - Fetch and store daily metrics

Fetch data from sources defined in `skene.json` and store in daily logs. The command reads the `skene.json` configuration file to find configured data sources, then fetches metrics for each objective defined in `growth-objectives.md`. If sources are not configured, you'll be prompted to manually add daily status.

**Prerequisites:**
- `growth-objectives.md` file (generated by the `objectives` command)
- `skene.json` file in skene-context directory (auto-created with example comments on first run)

```bash
# Use default skene-context directory
uvx skene-growth daily-logs

# Specify custom skene-context path
uvx skene-growth daily-logs --context ./my-context
```

**Output:**
- `./skene-context/daily_logs/daily_logs_YYYY_MM_DD.json` (dated log files)

**Configuration:**

The `skene.json` file is automatically created in your skene-context directory (or config-defined root) when you first run `daily-logs` if it doesn't exist. The file includes example comments explaining the structure and what should be configured. Edit this file to define your data sources:

- **sources**: Array of data source configurations (APIs, databases, files) - these are what `daily-logs` uses to fetch metrics
- **objectives**: Array of growth objectives to track (references to growth-objectives file)
- **config**: Optional configuration for data fetching (timeouts, retries, etc.)

**Example skene.json structure:**

```json
{
  "sources": [
    {
      "name": "analytics_api",
      "type": "api",
      "endpoint": "https://api.example.com/analytics",
      "auth": {
        "type": "bearer",
        "token_env": "ANALYTICS_API_TOKEN"
      }
    }
  ],
  "objectives": [
    {
      "id": "user_acquisition",
      "source": "analytics_api",
      "metric": "new_users",
      "period": "daily"
    }
  ],
  "config": {
    "timeout": 30,
    "retries": 3
  }
}
```

When you run `daily-logs`, it reads the `sources` array from `skene.json` to determine where to fetch data from. Each objective in your `growth-objectives.md` can reference a source by name to pull its metrics.

**Flags:**
- `-c, --context`: Path to skene-context directory (default: `./skene-context` or config-defined `output_dir`)
- `--list-metrics`: List metrics that need values (useful for AI/non-interactive mode)
- `--values`: JSON string with metric values: `'{"metric_id": "value", ...}'` (automatically enables non-interactive mode)

**Non-interactive mode (for AI assistants):**

When running `daily-logs` in non-interactive mode (e.g., via AI chat), use these steps:

1. **List required metrics:**
   ```bash
   uvx skene-growth daily-logs --list-metrics
   ```
   This outputs the metrics that need values, including their IDs, names, and targets.

2. **Provide values and run:**
   ```bash
   # Using JSON string (--values automatically enables non-interactive mode)
   uvx skene-growth daily-logs --values '{"user_acquisition": "150", "retention_rate": "95%"}'
   ```

   The values format is a JSON object with metric IDs as keys:
   ```json
   {
     "user_acquisition": "150",
     "retention_rate": "95%",
     "daily_active_users": "1,234"
   }
   ```

### `config` - Manage configuration

```bash
# Show current configuration
uvx skene-growth config

# Create a config file in current directory
uvx skene-growth config --init
```

## Configuration

skene-growth supports configuration files for storing defaults:

### Configuration Files

| Location | Purpose |
|----------|---------|
| `./.skene-growth.config` | Project-level config (checked into repo) |
| `~/.config/skene-growth/config` | User-level config (personal settings) |

### Sample Config File

```toml
# .skene-growth.config

# API key for LLM provider (can also use SKENE_API_KEY env var)
# api_key = "your-api-key"

# LLM provider to use: "openai" (default), "gemini", "anthropic", "lmstudio", or "ollama" (experimental)
provider = "openai"

# Model to use (provider-specific defaults apply if not set)
# openai: gpt-4o-mini | gemini: gemini-2.0-flash | anthropic: claude-sonnet-4-20250514 | ollama: llama2
# model = "gpt-4o-mini"

# Default output directory
output_dir = "./skene-context"

# Enable verbose output
verbose = false
```

### Configuration Priority

Settings are loaded in this order (later overrides earlier):

1. User config (`~/.config/skene-growth/config`)
2. Project config (`./.skene-growth.config`)
3. Environment variables (`SKENE_API_KEY`, `SKENE_PROVIDER`)
4. CLI arguments

## Python API

### CodebaseExplorer

Safe, sandboxed access to codebase files:

```python
from skene_growth import CodebaseExplorer

explorer = CodebaseExplorer("/path/to/repo")

# Get directory tree
tree = await explorer.get_directory_tree(".", max_depth=3)

# Search for files
files = await explorer.search_files(".", "**/*.py")

# Read file contents
content = await explorer.read_file("src/main.py")

# Read multiple files
contents = await explorer.read_multiple_files(["src/a.py", "src/b.py"])
```

### Analyzers

```python
from pydantic import SecretStr
from skene_growth import ManifestAnalyzer, CodebaseExplorer
from skene_growth.llm import create_llm_client

# Initialize
codebase = CodebaseExplorer("/path/to/repo")
llm = create_llm_client(
    provider="openai",  # or "gemini", "anthropic", "lmstudio", or "ollama" (experimental)
    api_key=SecretStr("your-api-key"),
    model_name="gpt-4o-mini",  # or "gemini-2.0-flash" / "claude-sonnet-4-20250514" / local model
)

# Run analysis
analyzer = ManifestAnalyzer()
result = await analyzer.run(
    codebase=codebase,
    llm=llm,
    request="Analyze this codebase for growth opportunities",
)

# Access results (the manifest is in result.data["output"])
manifest = result.data["output"]
print(manifest["tech_stack"])
print(manifest["growth_hubs"])
```

### Documentation Generator

```python
from skene_growth import DocsGenerator, GrowthManifest

# Load manifest
manifest = GrowthManifest.parse_file("growth-manifest.json")

# Generate docs
generator = DocsGenerator()
context_doc = generator.generate_context_doc(manifest)
product_doc = generator.generate_product_docs(manifest)
```

## Growth Manifest Schema

The `growth-manifest.json` output contains:

```json
{
  "version": "1.0",
  "project_name": "my-app",
  "description": "A SaaS application",
  "tech_stack": {
    "framework": "Next.js",
    "language": "TypeScript",
    "database": "PostgreSQL",
    "auth": "NextAuth.js",
    "deployment": "Vercel"
  },
  "growth_hubs": [
    {
      "feature_name": "User Invites",
      "file_path": "src/components/InviteModal.tsx",
      "detected_intent": "referral",
      "confidence_score": 0.85,
      "growth_potential": ["viral_coefficient", "user_acquisition"]
    }
  ],
  "gtm_gaps": [
    {
      "feature_name": "Social Sharing",
      "description": "No social sharing for user content",
      "priority": "high"
    }
  ],
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### Product Docs Schema (v2.0)

When using `--product-docs` flag, the manifest includes additional fields:

```json
{
  "version": "2.0",
  "project_name": "my-app",
  "description": "A SaaS application",
  "tech_stack": { ... },
  "growth_hubs": [ ... ],
  "gtm_gaps": [ ... ],
  "product_overview": {
    "tagline": "The easiest way to collaborate with your team",
    "value_proposition": "Simplify team collaboration with real-time editing and sharing.",
    "target_audience": "Remote teams and startups"
  },
  "features": [
    {
      "name": "Team Workspaces",
      "description": "Create dedicated spaces for your team to collaborate on projects.",
      "file_path": "src/features/workspaces/index.ts",
      "usage_example": "<WorkspaceCard workspace={workspace} />",
      "category": "Collaboration"
    }
  ],
  "generated_at": "2024-01-15T10:30:00Z"
}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SKENE_API_KEY` | API key for LLM provider |
| `SKENE_PROVIDER` | LLM provider to use: `openai` (default), `gemini`, `anthropic`, `lmstudio`, or `ollama` (experimental) |
| `LMSTUDIO_BASE_URL` | LM Studio server URL (default: `http://localhost:1234/v1`) |
| `OLLAMA_BASE_URL` | Ollama server URL (default: `http://localhost:11434/v1`) - Experimental |

## Requirements

- Python 3.11+
- **API key** (required for `analyze` command, except local LLMs):
  - OpenAI (default): https://platform.openai.com/api-keys
  - Gemini: https://aistudio.google.com/apikey
  - Anthropic: https://platform.claude.com/settings/keys
  - LM Studio: No API key needed (runs locally at http://localhost:1234)
  - Ollama (experimental): No API key needed (runs locally at http://localhost:11434)

## Troubleshooting

### LM Studio: Context length error

If you see an error like:
```
Error code: 400 - {'error': 'The number of tokens to keep from the initial prompt is greater than the context length...'}
```

This means the model's context length is too small for the analysis. To fix:

1. In LM Studio, unload the current model
2. Go to **Developer > Load**
3. Click on **Context Length: Model supports up to N tokens**
4. Reload to apply changes

See: https://github.com/lmstudio-ai/lmstudio-bug-tracker/issues/237

### LM Studio: Connection refused

If you see a connection error, ensure:
- LM Studio is running
- A model is loaded and ready
- The server is running on the default port (http://localhost:1234)

If using a different port or host, set the `LMSTUDIO_BASE_URL` environment variable:
```bash
export LMSTUDIO_BASE_URL="http://localhost:8080/v1"
```

### Ollama: Connection refused (Experimental)

**Note:** Ollama support is experimental and has not been fully tested. Please report any issues.

If you see a connection error, ensure:
- Ollama is running (`ollama serve`)
- A model is pulled and available (`ollama list` to check)
- The server is running on the default port (http://localhost:11434)

If using a different port or host, set the `OLLAMA_BASE_URL` environment variable:
```bash
export OLLAMA_BASE_URL="http://localhost:8080/v1"
```

To get started with Ollama:
```bash
# Install Ollama (see https://ollama.com)
# Pull a model
ollama pull llama2

# Run the server (usually runs automatically)
ollama serve
```


## MCP Server

skene-growth includes an MCP server for integration with AI assistants.

Add this to your AI assistant configuration file:

```json
{
  "mcpServers": {
    "skene-growth": {
      "command": "uvx",
      "args": ["--from", "skene-growth[mcp]", "skene-growth-mcp"],
      "env": {
        "SKENE_API_KEY": "your-openai-api-key"
      }
    }
  }
}
```

See [docs/mcp-server.md](docs/mcp-server.md) for more detailed instructions.

## License

MIT
