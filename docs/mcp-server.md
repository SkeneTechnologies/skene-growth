# MCP Server

skene-growth provides an [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that exposes codebase analysis capabilities to AI assistants like Claude Desktop and Claude Code.

## What It Does

The MCP server lets AI assistants analyze codebases directly through tool calls:

- **Explore codebase structure** - Get directory trees, search for files by pattern
- **Detect tech stack** - Framework, language, database, auth, deployment
- **Identify growth hubs** - Features with growth potential (invitations, sharing, referrals, payments)
- **Generate manifests** - Structured JSON output for product analysis
- **Create growth templates** - Custom PLG templates with lifecycle stages and metrics

## Installation

Install with the `mcp` optional dependency:

```bash
# With pip
pip install skene-growth[mcp]

# With uv
uv pip install skene-growth[mcp]
```

## Configuration

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "skene-growth": {
      "command": "skene-growth-mcp",
      "env": {
        "SKENE_API_KEY": "your-openai-api-key"
      }
    }
  }
}
```

Or using uvx (no installation required):

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

### Claude Code

Add to your Claude Code settings (`.mcp.json` in project or `~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "skene-growth": {
      "command": "skene-growth-mcp",
      "env": {
        "SKENE_API_KEY": "your-openai-api-key"
      }
    }
  }
}
```

## Available Tools

Tools are organized into tiers by speed and complexity:

### Tier 1: Quick Tools (< 1s, no LLM)

| Tool | Description |
|------|-------------|
| `get_codebase_overview` | Directory tree, file counts by extension, detected config files |
| `search_codebase` | Search files by glob pattern (e.g., `**/*.py`, `src/**/*.ts`) |

### Tier 2: Analysis Tools (5-15s, uses LLM)

| Tool | Description |
|------|-------------|
| `analyze_tech_stack` | Detect framework, language, database, auth, deployment |
| `analyze_product_overview` | Extract product info from README and docs |
| `analyze_growth_hubs` | Find viral/growth features (invites, sharing, referrals) |
| `analyze_features` | Document user-facing features |

### Tier 3: Generation Tools (5-15s)

| Tool | Description |
|------|-------------|
| `generate_manifest` | Create GrowthManifest from cached analysis results |
| `generate_growth_template` | Create PLG template with lifecycle stages and metrics |
| `write_analysis_outputs` | Write JSON/Markdown files to `./skene-context/` |

### Utility Tools

| Tool | Description |
|------|-------------|
| `get_manifest` | Read existing manifest from disk |
| `clear_cache` | Clear cached analysis results |

## Typical Workflow

The tools are designed to be called in sequence:

```
1. get_codebase_overview      → Understand project structure
2. analyze_tech_stack         → Detect technologies (cached)
3. analyze_growth_hubs        → Find growth features (cached)
4. generate_manifest          → Combine into manifest (uses cache)
5. generate_growth_template   → Create PLG template (optional)
6. write_analysis_outputs     → Save to disk
```

Results from Tier 2 tools are cached, so `generate_manifest` can combine them without re-running the LLM calls.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SKENE_API_KEY` | API key for LLM provider | (required) |
| `SKENE_PROVIDER` | LLM provider: `openai`, `gemini`, `anthropic`, `lmstudio`, `ollama` | `openai` |
| `SKENE_MODEL` | Model to use | Provider default |
| `SKENE_CACHE_DIR` | Cache directory | `~/.cache/skene-growth-mcp` |
| `SKENE_CACHE_TTL` | Cache TTL in seconds | `3600` |
| `SKENE_CACHE_ENABLED` | Enable/disable caching | `true` |

## Using Local LLMs

For LM Studio or Ollama, no API key is needed:

```json
{
  "mcpServers": {
    "skene-growth": {
      "command": "skene-growth-mcp",
      "env": {
        "SKENE_PROVIDER": "lmstudio",
        "SKENE_MODEL": "your-loaded-model"
      }
    }
  }
}
```

## Running Manually

```bash
# Via entry point
skene-growth-mcp

# Via Python module
python -m skene_growth.mcp
```

The server communicates via stdio (standard input/output) as per the MCP protocol.
