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

With the `--docs` flag, it also collects:

- **Product Overview** - Tagline, value proposition, target audience
- **Features** - User-facing feature documentation with descriptions and examples

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

# Enable docs mode (collects product overview and features)
uvx skene-growth analyze . --docs

# Specify business type for custom growth template
uvx skene-growth analyze . --business-type "design-agency"
uvx skene-growth analyze . --business-type "b2b-saas"

# Generate product documentation alongside analysis
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
- `--docs`: Enable documentation mode (collects product overview and features)
- `--product-docs`: Generate user-friendly product documentation
- `--business-type`: Specify business type for custom growth template

The `--docs` flag enables documentation mode which produces a v2.0 manifest with additional fields. The `--product-docs` flag generates a user-friendly product documentation file with features and roadmap.

### `validate` - Validate a manifest

```bash
uvx skene-growth validate ./growth-manifest.json
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
| `./.skene-growth.toml` | Project-level config (checked into repo) |
| `~/.config/skene-growth/config.toml` | User-level config (personal settings) |

### Sample Config File

```toml
# .skene-growth.toml

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

1. User config (`~/.config/skene-growth/config.toml`)
2. Project config (`./.skene-growth.toml`)
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

### Docs Mode Schema (v2.0)

When using `--docs` flag, the manifest includes additional fields:

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


## License

MIT
