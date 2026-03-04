# Quickstart

Get from zero to a deployed growth loop.

> **Prerequisites**
>
> - Python 3.11 or later
> - [uv](https://docs.astral.sh/uv/) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
> - An API key from OpenAI, Google Gemini, or Anthropic -- OR a local LLM running via [LM Studio](https://lmstudio.ai/) or [Ollama](https://ollama.com/)

## Setup

### Create and configure

```bash
# Create a config file with sensible defaults
uvx skene-growth config --init

# Set up your LLM provider and API key interactively
uvx skene-growth config
```

The interactive setup walks you through provider, model, and API key selection. The config is saved to `.skene-growth.config` with restrictive permissions (`0600` on Unix).

> **Tip:** You can skip config setup entirely by passing `--api-key` and `--provider` flags directly to each command, or by setting the `SKENE_API_KEY` and `SKENE_PROVIDER` environment variables.

## Analyze, plan, build

### Analyze your codebase

```bash
uvx skene-growth analyze .
```

Scans your codebase and generates files in `./skene-context/`:

- **`growth-manifest.json`** -- structured data about your tech stack, existing growth features, and growth opportunities
- **`growth-template.json`** -- a business-type-aware growth template with prioritized recommendations
- **`feature-registry.json`** -- persistent registry tracking features across analysis runs

The analysis uses your configured LLM to understand your codebase structure, detect the technology stack (framework, language, database, hosting), identify existing growth features, and surface new growth opportunities.

### Generate a growth plan

```bash
uvx skene-growth plan
```

Reads `growth-manifest.json` and `growth-template.json` from `./skene-context/` (auto-detected) and generates a `growth-plan.md` file in the same directory.

The plan is produced by a "Council of Growth Engineers" analysis -- multiple specialized perspectives evaluate your codebase and converge on a prioritized growth strategy. The output includes an executive summary, prioritized growth opportunities, a technical execution section with the recommended "next build", and an implementation todo list.

For activation-focused analysis instead of general growth:

```bash
uvx skene-growth plan --activation
```

### Build an implementation prompt

```bash
uvx skene-growth build
```

This command:

1. Reads `growth-plan.md` from `./skene-context/` (auto-detected)
2. Extracts the Technical Execution section (the recommended next build, exact logic, data triggers, sequence)
3. Uses your LLM to generate a focused implementation prompt
4. Asks where you want to send it:
   - **Cursor** -- opens via deep link
   - **Claude** -- launches in terminal
   - **Show** -- prints the full prompt to the terminal

The prompt and a growth loop definition (JSON) are saved to `./skene-context/` for later use.

> **Tip:** Use `--target` to skip the interactive menu. This is useful for scripting:
> ```bash
> uvx skene-growth build --target file   # Just save the prompt, no interaction
> ```

## Verify and deploy

### Check implementation status

After implementing the growth loop (using Cursor, Claude, or manually), verify that all requirements are met:

```bash
uvx skene-growth status
```

This loads the growth loop definitions from `./skene-context/growth-loops/` and uses AST parsing to verify that required files, functions, and patterns are present in your codebase. Each loop is marked **COMPLETE** or **INCOMPLETE** with details on what's missing.

For LLM-powered semantic matching to find alternative implementations:

```bash
uvx skene-growth status --find-alternatives --api-key "your-key"
```

### Push to Supabase and upstream

If your project uses Supabase, initialize the base schema and push growth loop telemetry:

```bash
# One-time: create base schema migration (event_log, enrichment_map, etc.)
uvx skene-growth init

# Generate telemetry triggers and push
uvx skene-growth push
```

To also push artifacts to Skene Cloud upstream:

```bash
uvx skene-growth login --upstream https://skene.ai/workspace/my-app
uvx skene-growth push
```

## What you get

Your `./skene-context/` directory contains:

| File | Description |
|---|---|
| `growth-manifest.json` | Structured analysis of your codebase: tech stack, current growth features, opportunities |
| `growth-template.json` | Business-type-aware growth template with prioritized recommendations |
| `feature-registry.json` | Persistent registry tracking features across analysis runs with growth loop mappings |
| `growth-plan.md` | Full growth plan with executive summary, priorities, and technical execution details |
| `implementation-prompt.md` | Ready-to-use prompt for your AI coding assistant |
| `growth-loops/*.json` | Growth loop definitions with telemetry specs, feature links, and verification requirements |

## Alternative: Quick one-liner

If you want to try the analysis without setting up a config file first, pass your API key inline:

```bash
uvx skene-growth analyze . --api-key "your-key"
```

This uses the default provider (openai) and model (gpt-4o). To use a different provider:

```bash
uvx skene-growth analyze . --api-key "your-key" --provider gemini --model gemini-3-flash-preview
```

## Alternative: Free preview (no API key)

If you want to see what skene-growth does before configuring an LLM, simply run `analyze` without an API key:

```bash
uvx skene-growth analyze .
```

When no API key is configured and you are not using a local provider, the command falls back to a sample growth analysis preview demonstrating the kind of strategic insights available with full API-powered analysis.

## Next steps

- [Analyze command in depth](../guides/analyze.md) -- all flags, output customization, excluding folders
- [Plan command in depth](../guides/plan.md) -- context directories, activation mode, custom manifest paths
- [Build command in depth](../guides/build.md) -- prompt generation, Cursor/Claude integration
- [Push command in depth](../guides/push.md) -- Supabase migrations and upstream deployment
- [Status command in depth](../guides/status.md) -- growth loop validation and alternative matching
- [Features](../guides/features.md) -- managing and exporting the feature registry
- [Login](../guides/login.md) -- authenticating with Skene Cloud upstream
- [Configuration reference](../guides/configuration.md) -- config files, environment variables, precedence rules
- [LLM providers](../guides/llm-providers.md) -- setup for OpenAI, Gemini, Anthropic, LM Studio, Ollama, and generic endpoints
