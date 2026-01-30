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
- **Current Growth Features** - Existing features with growth potential (signup flows, sharing, invites, billing)
- **Revenue Leakage** - Potential revenue issues (missing monetization, weak pricing tiers, overly generous free tiers)
- **Growth Opportunities** - Missing features that could drive user acquisition and retention

With the `--product-docs` flag, it also collects:

- **Product Overview** - Tagline, value proposition, target audience
- **Features** - User-facing feature documentation with descriptions and examples
- **Product Docs** - Generates user-friendly product-docs.md file

After the manifest is created, skene-growth generates a **custom growth template** (JSON)
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

> **Note:** The `analyze` command requires an API key. By default, it uses OpenAI (get a key at https://platform.openai.com/api-keys). You can also use Gemini with `--provider gemini`, Anthropic with `--provider anthropic` or `--provider claude`, or local LLMs with `--provider lmstudio` or `--provider ollama` (experimental).

### Option 2: pip install

```bash
pip install skene-growth
```

## How to use?

skene-growth follows a flexible workflow:

1. **Analyze** - Establishes the foundation by analyzing your codebase and generating a comprehensive growth manifest. This creates the general AI context about your codebase structure, technology stack, user journey, and growth opportunities. The output includes current growth features, revenue leakage issues, growth opportunities, and a custom growth template tailored to your business type.

2. **Plan** - Generates a growth plan using Council of Growth Engineers analysis. This command uses an LLM to analyze your manifest and template to produce a detailed growth plan with 3-5 selected high-impact growth loops, implementation roadmap, and recommendations.

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

# Use Anthropic (Claude) - both "anthropic" and "claude" work
uvx skene-growth analyze . --provider anthropic --api-key "your-anthropic-api-key"
uvx skene-growth analyze . --provider claude --api-key "your-anthropic-api-key"

# Use LM Studio (local server)
uvx skene-growth analyze . --provider lmstudio --model "your-loaded-model"

# Use Ollama (local server) - Experimental
uvx skene-growth analyze . --provider ollama --model "llama2"

# Specify business type for custom growth template
uvx skene-growth analyze . --business-type "design-agency"
uvx skene-growth analyze . --business-type "b2b-saas"

# Generate product documentation (collects product overview and features)
uvx skene-growth analyze . --product-docs

# Exclude folders from analysis (can be used multiple times)
uvx skene-growth analyze . --exclude tests --exclude vendor --exclude migrations
uvx skene-growth analyze . -e planner -e docs
```

**Output:**
- `./skene-context/growth-manifest.json` (structured data)
- `./skene-context/growth-template.json` (if --business-type specified)
- `./skene-context/product-docs.md` (if --product-docs flag used)

**Growth Templates:** The system generates custom templates tailored to your business type, with
lifecycle stages and keywords specific to your user journey. If no business type is specified,
the LLM infers it from your codebase.

**Flags:**
- `--product-docs`: Generate user-friendly product documentation (collects product overview, features, and generates product-docs.md)
- `--business-type`: Specify business type for custom growth template
- `-e, --exclude`: Folder names to exclude from analysis (can be used multiple times). Excludes any folder containing the specified name anywhere in the path. Can also be configured in `.skene-growth.config` file.

The `--product-docs` flag enables enhanced analysis mode which collects product overview and feature documentation, producing a v2.0 manifest with additional fields and a user-friendly product-docs.md file.

### `validate` - Validate a manifest

```bash
uvx skene-growth validate ./growth-manifest.json
```

### `plan` - Generate growth plan

Generate a growth plan using Council of Growth Engineers analysis. This command uses an LLM to analyze your manifest and template to produce actionable growth recommendations.

**Prerequisites:**
- `growth-manifest.json` file (generated by the `analyze` command)
- `growth-template.json` file (generated by the `analyze` command)
- API key for LLM provider

```bash
# Generate growth plan (auto-detects manifest and template)
uvx skene-growth plan --api-key "your-key"

# Specify context directory containing manifest and template
uvx skene-growth plan --context ./my-context --api-key "your-key"
# Or use short form:
uvx skene-growth plan -c ./my-context --api-key "your-key"

# Specify all files explicitly
uvx skene-growth plan --manifest ./manifest.json --template ./template.json

# Use different provider/model
uvx skene-growth plan --provider gemini --model gemini-2.0-flash
```

**Output:**
- `./skene-context/growth-plan.md` (default) or custom path specified with `-o`

**Flags:**
- `--manifest`: Path to growth-manifest.json (auto-detected if not specified)
- `--template`: Path to growth-template.json (auto-detected if not specified)
- `-c, --context`: Directory containing growth-manifest.json and growth-template.json (detected at working directory if not specified)
- `-o, --output`: Output path for growth plan (markdown format)
- `--api-key`: API key for LLM provider (or set SKENE_API_KEY env var)
- `-p, --provider`: LLM provider to use (openai, gemini, anthropic/claude, ollama)
- `-m, --model`: LLM model name
- `-v, --verbose`: Enable verbose output

**Council of Growth Engineers Analysis:**
The plan command uses a "Council of Growth Engineers" system prompt that acts as an elite advisory board of growth strategists. It provides:
- Assessment of current state and opportunities
- 3-5 selected high-impact growth loops with detailed implementation steps
- Week-by-week implementation roadmap
- Key callouts on what to avoid and what to prioritize
- Specific metrics and measurement strategies

### `config` - Manage configuration

```bash
# Show current configuration
uvx skene-growth config

# Create a config file in current directory
uvx skene-growth config --init
```

## Excluding Folders from Analysis

You can exclude specific folders from analysis to skip test files, vendor directories, documentation, or any other folders you don't want analyzed.

### How Exclusion Works

Exclusion matches folders in three ways:
1. **Exact folder name match** - Excluding `"tests"` matches exactly `"tests"`
2. **Substring match in folder names** - Excluding `"test"` matches `"tests"`, `"test_utils"`, `"integration_tests"`, etc.
3. **Path pattern matching** - Excluding `"tests/unit"` matches any path containing that pattern

### Examples

```bash
# Exclude test folders and vendor directories
uvx skene-growth analyze . --exclude tests --exclude vendor

# Exclude multiple folders (short form)
uvx skene-growth analyze . -e planner -e migrations -e docs

# Exclude path patterns
uvx skene-growth analyze . --exclude "tests/unit" --exclude "vendor/legacy"
```

### Default Exclusions

By default, skene-growth excludes common build and cache directories:
- `.git`, `.svn`, `.hg` (version control)
- `__pycache__`, `.pytest_cache` (Python cache)
- `node_modules` (Node.js dependencies)
- `.idea`, `.vscode` (IDE configs)
- `venv`, `.venv` (Python virtual environments)
- `dist`, `build` (build outputs)
- `.next`, `.nuxt` (framework builds)
- `coverage`, `.cache` (test/build artifacts)

Your custom exclusions are merged with these defaults.

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

# LLM provider to use: "openai" (default), "gemini", "anthropic"/"claude", "lmstudio", or "ollama" (experimental)
provider = "openai"

# Model to use (provider-specific defaults apply if not set)
# openai: gpt-4o-mini | gemini: gemini-2.0-flash | anthropic: claude-haiku-4-5-20251001 | ollama: llama2
# model = "gpt-4o-mini"

# Default output directory
output_dir = "./skene-context"

# Enable verbose output
verbose = false

# Folders to exclude from analysis (folder names or path patterns)
# Excludes any folder containing these names anywhere in the path
# Examples: "test" will exclude "tests", "test_utils", "integration_tests"
# Path patterns like "tests/unit" will exclude any path containing that pattern
exclude_folders = ["tests", "vendor", "migrations", "docs"]
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

# Create explorer with default exclusions
explorer = CodebaseExplorer("/path/to/repo")

# Exclude specific folders from analysis
explorer = CodebaseExplorer(
    "/path/to/repo",
    exclude_folders=["tests", "vendor", "migrations"]
)

# Get directory tree (excluded folders are automatically filtered)
tree = await explorer.get_directory_tree(".", max_depth=3)

# Search for files (excluded folders are automatically filtered)
files = await explorer.search_files(".", "**/*.py")

# Read file contents
content = await explorer.read_file("src/main.py")

# Read multiple files
contents = await explorer.read_multiple_files(["src/a.py", "src/b.py"])

# Check if a path should be excluded
from pathlib import Path
should_exclude = explorer.should_exclude(Path("src/tests/unit.py"))
```

### Analyzers

```python
from pydantic import SecretStr
from skene_growth import ManifestAnalyzer, CodebaseExplorer
from skene_growth.llm import create_llm_client

# Initialize
codebase = CodebaseExplorer("/path/to/repo")
llm = create_llm_client(
    provider="openai",  # or "gemini", "anthropic"/"claude", "lmstudio", or "ollama" (experimental)
    api_key=SecretStr("your-api-key"),
    model_name="gpt-4o-mini",  # or "gemini-2.0-flash" / "claude-haiku-4-5-20251001" / local model
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
print(manifest["current_growth_features"])
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
  "current_growth_features": [
    {
      "feature_name": "User Invites",
      "file_path": "src/components/InviteModal.tsx",
      "detected_intent": "referral",
      "confidence_score": 0.85,
      "growth_potential": ["viral_coefficient", "user_acquisition"]
    }
  ],
  "revenue_leakage": [
    {
      "issue": "Free tier allows unlimited usage without conversion prompts",
      "file_path": "src/pricing/tiers.py",
      "impact": "high",
      "recommendation": "Add usage limits or upgrade prompts to encourage paid conversions"
    }
  ],
  "growth_opportunities": [
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
  "current_growth_features": [ ... ],
  "revenue_leakage": [ ... ],
  "growth_opportunities": [ ... ],
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
| `SKENE_PROVIDER` | LLM provider to use: `openai` (default), `gemini`, `anthropic`/`claude`, `lmstudio`, or `ollama` (experimental) |
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
