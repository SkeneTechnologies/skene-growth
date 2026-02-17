# PyPI Publishing Guide

This guide covers publishing the `skene-growth-stack` package to PyPI.

## Package Information

- **Package Name:** `skene-growth-stack`
- **Current Version:** 0.1.7.3 (see `pyproject.toml`)
- **PyPI URL:** https://pypi.org/project/skene-growth-stack/ (after publishing)
- **Install Command:** `pip install skene-growth-stack[mcp]`

## Prerequisites

### 1. Install Build Tools

```bash
pip install --upgrade build twine
```

### 2. Create PyPI Account

1. Go to [pypi.org/account/register](https://pypi.org/account/register/)
2. Verify email address
3. Enable 2FA (recommended)

### 3. Create API Token

1. Go to [pypi.org/manage/account/token](https://pypi.org/manage/account/token/)
2. Create token with scope: "Entire account" (for first publish)
3. Save token securely (starts with `pypi-`)

### 4. Configure Credentials

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # Your API token
```

**Important:** Set secure permissions:
```bash
chmod 600 ~/.pypirc
```

## Publishing Process

### Step 1: Update Version

Edit `pyproject.toml`:

```toml
[project]
name = "skene-growth-stack"
version = "0.1.8"  # Increment version
```

**Version Scheme:**
- **Patch:** Bug fixes (0.1.7 → 0.1.8)
- **Minor:** New features (0.1.8 → 0.2.0)
- **Major:** Breaking changes (0.2.0 → 1.0.0)

### Step 2: Clean Previous Builds

```bash
cd python/skene-growth
rm -rf dist/ build/ *.egg-info
```

### Step 3: Build Package

```bash
python3 -m build
```

**Expected Output:**
```
Successfully built skene-growth-stack-0.1.8.tar.gz
Successfully built skene_growth_stack-0.1.8-py3-none-any.whl
```

**Verify artifacts:**
```bash
ls dist/
# skene-growth-stack-0.1.8.tar.gz
# skene_growth_stack-0.1.8-py3-none-any.whl
```

### Step 4: Test Package Locally

```bash
# Install from local build
pip install dist/skene-growth-stack-0.1.8.tar.gz[mcp]

# Test CLI
skene-growth-stack --version

# Test MCP server
skene-growth-stack-mcp --help

# Uninstall
pip uninstall skene-growth-stack
```

### Step 5: Upload to TestPyPI (Optional)

Test the upload process first:

```bash
# Upload to test server
python3 -m twine upload --repository testpypi dist/*

# Install from test server
pip install --index-url https://test.pypi.org/simple/ skene-growth-stack[mcp]

# Test functionality
skene-growth-stack analyze .
```

### Step 6: Upload to PyPI (Production)

```bash
python3 -m twine upload dist/*
```

**Expected Output:**
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading skene-growth-stack-0.1.8.tar.gz
Uploading skene_growth_stack-0.1.8-py3-none-any.whl
```

### Step 7: Verify Publication

```bash
# Wait 1-2 minutes for PyPI indexing

# Install from PyPI
pip install skene-growth-stack[mcp]

# Verify installation
skene-growth-stack --version
# Expected: skene-growth 0.1.8

# Test MCP server
skene-growth-stack-mcp
# Expected: MCP server starts
```

## Package Structure

```
python/skene-growth/
├── src/
│   └── skene_growth/
│       ├── __init__.py
│       ├── cli/
│       │   └── main.py          # CLI entry point
│       ├── mcp/
│       │   ├── __init__.py
│       │   ├── __main__.py
│       │   ├── server.py        # MCP server
│       │   └── tools.py         # MCP tools
│       ├── analyzers/
│       ├── codebase/
│       ├── llm/
│       └── ...
├── pyproject.toml               # Package metadata
├── README.md                    # Package description
└── LICENSE                      # MIT license
```

## Entry Points

The package provides two CLI commands:

### 1. Main CLI (`skene-growth-stack`)

```python
# Defined in pyproject.toml
[project.scripts]
skene-growth-stack = "skene_growth.cli.main:app"
```

**Usage:**
```bash
skene-growth-stack analyze .
skene-growth-stack plan
skene-growth-stack objectives
```

### 2. MCP Server (`skene-growth-stack-mcp`)

```python
# Defined in pyproject.toml
[project.scripts]
skene-growth-stack-mcp = "skene_growth.mcp:main"
```

**Usage:**
```bash
# Start MCP server (stdio mode)
skene-growth-stack-mcp

# Or via uvx (recommended)
uvx skene-growth-stack[mcp]
```

## Optional Dependencies

The package has optional MCP dependencies:

```toml
[project.optional-dependencies]
mcp = [
    "mcp>=1.0.0",
    "xxhash>=3.0",
]
```

**Install with MCP:**
```bash
pip install skene-growth-stack[mcp]
```

**Install without MCP:**
```bash
pip install skene-growth-stack
```

## MCP Integration

### Claude Code Configuration

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "skene-growth": {
      "command": "uvx",
      "args": ["skene-growth-stack[mcp]"],
      "env": {}
    }
  }
}
```

**Restart Claude Code** to load the MCP server.

### Verify MCP Integration

In Claude Code, ask:
> "Show me all available Skene tools"

Expected: Lists 11 tools:
- `analyze_codebase`
- `analyze_growth_hubs`
- `analyze_tech_stack`
- `generate_daily_log`
- `generate_documentation`
- `detect_billing_opportunities`
- `detect_dead_code`
- `estimate_tech_debt`
- `scan_entropy`
- `get_manifest`
- `refresh_manifest`

## Troubleshooting

### Build Fails

**Error:** `ModuleNotFoundError: No module named 'build'`

**Solution:**
```bash
pip install --upgrade build
```

### Upload Fails

**Error:** `HTTPError: 403 Forbidden`

**Solution:**
- Verify API token in `~/.pypirc`
- Check token has correct permissions
- Ensure package name isn't taken (search PyPI)

### Version Conflict

**Error:** `File already exists`

**Solution:**
- You cannot reupload the same version
- Increment version in `pyproject.toml`
- Rebuild: `python3 -m build`

### Import Error After Install

**Error:** `ModuleNotFoundError: No module named 'skene_growth'`

**Solution:**
```bash
# Check installation
pip show skene-growth-stack

# Reinstall
pip uninstall skene-growth-stack
pip install skene-growth-stack[mcp]
```

### MCP Server Doesn't Start

**Error:** `command not found: skene-growth-stack-mcp`

**Solution:**
```bash
# Ensure MCP extras installed
pip install skene-growth-stack[mcp]

# Check entry point
which skene-growth-stack-mcp

# If not in PATH, use full path
~/.local/bin/skene-growth-stack-mcp
```

## CI/CD Publishing (GitHub Actions)

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build package
        run: python -m build
        working-directory: python/skene-growth

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: python -m twine upload dist/*
        working-directory: python/skene-growth
```

**Setup:**
1. Go to GitHub repo → Settings → Secrets
2. Add secret: `PYPI_API_TOKEN` (value: your PyPI token)
3. Create a release → Workflow auto-publishes

## Version Management

### Pre-release Versions

For testing:
```toml
version = "0.1.8a1"  # Alpha
version = "0.1.8b1"  # Beta
version = "0.1.8rc1" # Release candidate
```

### Post-release Versions

For hotfixes:
```toml
version = "0.1.8.post1"
```

## Package Metadata

Update in `pyproject.toml`:

```toml
[project]
name = "skene-growth-stack"
description = "PLG analysis toolkit for codebases"
keywords = ["plg", "growth", "codebase", "analysis"]
authors = [{ name = "Skene Technologies" }]

[project.urls]
Homepage = "https://www.skene.ai"
Documentation = "https://github.com/SkeneTechnologies/skene#readme"
Repository = "https://github.com/SkeneTechnologies/skene"
```

## Post-Publication Checklist

- [ ] Package appears on PyPI: https://pypi.org/project/skene-growth-stack/
- [ ] Install works: `pip install skene-growth-stack[mcp]`
- [ ] CLI works: `skene-growth-stack --version`
- [ ] MCP server works: `skene-growth-stack-mcp`
- [ ] MCP integration works in Claude Code
- [ ] README displays correctly on PyPI
- [ ] All 11 MCP tools accessible
- [ ] Documentation links work

## Update Website

After publishing, update `packages/website/src/app/page.tsx`:

```tsx
<code className="font-mono text-sm">
  <span className="text-peach">$</span> pip install skene-growth-stack[mcp]
</code>
```

## Support

- **PyPI Help:** https://pypi.org/help/
- **Twine Docs:** https://twine.readthedocs.io/
- **Packaging Guide:** https://packaging.python.org/
- **Skene GitHub:** https://github.com/SkeneTechnologies/skene

## Quick Reference

```bash
# Build
python3 -m build

# Test upload
python3 -m twine upload --repository testpypi dist/*

# Production upload
python3 -m twine upload dist/*

# Install
pip install skene-growth-stack[mcp]

# Verify
skene-growth-stack --version
skene-growth-stack-mcp --help
```

## One-Liner Publishing

```bash
cd python/skene-growth && rm -rf dist/ && python3 -m build && python3 -m twine upload dist/*
```

That's it! Your package is live on PyPI. 🚀
