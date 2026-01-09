# skene-growth

PLG (Product-Led Growth) analysis toolkit for codebases. Analyze your code, detect growth opportunities, and generate documentation of your stack.

## Quick Start

**No installation required** - just run with [uvx](https://docs.astral.sh/uv/):

```bash
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

## Installation

### Option 1: uvx (Recommended)

Zero installation - runs instantly (requires API key):

```bash
uvx skene-growth analyze . --api-key "your-openai-api-key"
uvx skene-growth generate
uvx skene-growth inject
uvx skene-growth validate ./growth-manifest.json
```

> **Note:** The `analyze` command requires an API key. By default, it uses OpenAI (get a key at https://platform.openai.com/api-keys). You can also use Gemini with `--provider gemini`.

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

# Enable docs mode (collects product overview and features)
uvx skene-growth analyze . --docs
```

**Output:** `./skene-context/growth-manifest.json`

The `--docs` flag enables documentation mode which produces a v2.0 manifest with additional fields for generating richer documentation.

### `generate` - Generate documentation

```bash
# Generate docs from manifest (auto-detected)
uvx skene-growth generate

# Specify manifest and output directory
uvx skene-growth generate -m ./manifest.json -o ./docs
```

**Output:** Markdown documentation in `./skene-docs/`

### `inject` - Generate growth loop injection plan

```bash
# Generate injection plan using built-in growth loops
uvx skene-growth inject

# Use custom growth loops from CSV
uvx skene-growth inject --csv loops.csv

# Specify manifest
uvx skene-growth inject -m ./manifest.json
```

**Output:** `./skene-injection-plan.json`

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

# LLM provider to use: "openai" (default) or "gemini"
provider = "openai"

# Model to use (default: gpt-4o-mini for OpenAI, gemini-2.0-flash for Gemini)
# model = "gpt-4o"

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
    provider="openai",  # or "gemini"
    api_key=SecretStr("your-api-key"),
    model_name="gpt-4o-mini",  # or "gemini-2.0-flash" for Gemini
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

### Growth Loop Catalog

```python
from skene_growth import GrowthLoopCatalog

catalog = GrowthLoopCatalog()

# Get all loops
all_loops = catalog.get_all()

# Get by category
referral_loops = catalog.get_by_category("referral")
activation_loops = catalog.get_by_category("activation")

# Get specific loop
invite_loop = catalog.get_by_id("user-invites")

# Load custom loops from CSV
catalog.load_from_csv("my-loops.csv")
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

### Injection Planner

```python
from skene_growth import InjectionPlanner, GrowthLoopCatalog, GrowthManifest

manifest = GrowthManifest.parse_file("growth-manifest.json")
catalog = GrowthLoopCatalog()
planner = InjectionPlanner()

# Generate quick plan (no LLM required)
plan = planner.generate_quick_plan(manifest, catalog)

# Save plan
planner.save_plan(plan, "injection-plan.json")
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

## Built-in Growth Loops

The catalog includes these growth loop templates:

| Loop | Category | Description |
|------|----------|-------------|
| User Invites | Referral | Users invite others to join |
| Social Sharing | Acquisition | Share content on social media |
| Onboarding Completion | Activation | Guide users to key actions |
| Usage Streaks | Retention | Encourage regular usage |
| Upgrade Prompts | Revenue | Prompt upgrades at limits |
| User-Generated Content | Acquisition | Content that attracts users |
| Re-engagement Notifications | Retention | Bring back inactive users |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SKENE_API_KEY` | API key for LLM provider |
| `SKENE_PROVIDER` | LLM provider to use: `openai` (default) or `gemini` |

## Requirements

- Python 3.11+
- **API key** (required for `analyze` command):
  - OpenAI (default): https://platform.openai.com/api-keys
  - Gemini: https://aistudio.google.com/apikey

## License

MIT
