# skene-growth

PLG (Product-Led Growth) analysis toolkit for codebases. Analyze your code, detect growth opportunities, and generate documentation.

## Quick Start

**No installation required** - just run with [uvx](https://docs.astral.sh/uv/):

```bash
# Analyze your codebase
uvx skene-growth analyze . --api-key "your-gemini-api-key"

# Or set the API key as environment variable
export SKENE_API_KEY="your-gemini-api-key"
uvx skene-growth analyze .
```

Get a free Gemini API key at: https://aistudio.google.com/apikey

## What It Does

skene-growth scans your codebase and generates a **growth manifest** containing:

- **Tech Stack Detection** - Framework, language, database, auth, deployment
- **Growth Hubs** - Features with growth potential (signup flows, sharing, invites, billing)
- **GTM Gaps** - Missing features that could drive user acquisition and retention

## Installation

### Option 1: uvx (Recommended)

Zero installation - runs instantly:

```bash
uvx skene-growth analyze .
uvx skene-growth generate
uvx skene-growth inject
uvx skene-growth validate ./growth-manifest.json
```

### Option 2: pip install

```bash
pip install skene-growth

# With Gemini support (for LLM-powered analysis)
pip install skene-growth[gemini]
```

## CLI Commands

### `analyze` - Analyze a codebase

```bash
# Analyze current directory
uvx skene-growth analyze .

# Analyze specific path with custom output
uvx skene-growth analyze ./my-project -o manifest.json

# With verbose output
uvx skene-growth analyze . -v
```

**Output:** `./skene-context/growth-manifest.json`

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
# api_key = "your-gemini-api-key"

# LLM provider to use (default: gemini)
provider = "gemini"

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
from skene_growth import ManifestAnalyzer, CodebaseExplorer
from skene_growth.llm import create_llm_client

# Initialize
codebase = CodebaseExplorer("/path/to/repo")
llm = create_llm_client("gemini", "your-api-key")

# Run analysis
analyzer = ManifestAnalyzer()
result = await analyzer.run(
    codebase=codebase,
    llm=llm,
    request="Analyze this codebase for growth opportunities",
)

# Access results
print(result.data["tech_stack"])
print(result.data["growth_hubs"])
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
| `SKENE_API_KEY` | API key for LLM provider (Gemini) |
| `SKENE_PROVIDER` | LLM provider to use (default: gemini) |

## Requirements

- Python 3.11+
- Gemini API key (for LLM-powered analysis)

## License

MIT
