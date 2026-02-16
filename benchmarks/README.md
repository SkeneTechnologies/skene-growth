# skene-growth Benchmarking Suite

Compare `skene-growth` pipeline output quality across LLM providers and models.

## Quick Start

```bash
# 1. Set API key(s) for the models you want to test
export GOOGLE_API_KEY="your-key"

# 2. Run with default config (uses tests/fixtures/sample_repo)
uv run benchmarks/run.py --skip-judge

# 3. Check results
ls benchmarks/results/
cat benchmarks/results/*/summary.md
```

## Configuration

Edit `benchmarks/config.toml` to configure codebases and models:

```toml
[settings]
runs_per_combo = 1

[[codebases]]
name = "my-project"
path = "./benchmarks/codebases/my-project"

[[models]]
name = "gemini-flash"
provider = "gemini"
model = "gemini-2.5-flash-preview-05-20"
api_key_env = "GOOGLE_API_KEY"

[[models]]
name = "claude-sonnet"
provider = "anthropic"
model = "claude-sonnet-4-5"
api_key_env = "ANTHROPIC_API_KEY"
```

API keys are read from environment variables specified by `api_key_env` — never hardcoded.

## CLI Options

```bash
uv run benchmarks/run.py [OPTIONS]

Options:
  --config PATH      Path to TOML config file (default: benchmarks/config.toml)
  --skip-judge       Skip LLM-as-judge evaluation (recommended for now)
  --evaluate-only    Re-evaluate existing results (not yet implemented)
```

## Output Structure

Each run creates a timestamped directory:

```
benchmarks/results/<timestamp>/
├── summary.json              # Machine-readable results
├── summary.md                # Human-readable comparison report
└── <codebase-name>/
    └── <model-name>/
        └── run-<n>/
            ├── growth-manifest.json
            ├── growth-template.json
            ├── growth-plan.md
            ├── .skene-build-prompt.md
            ├── growth-loops/*.json
            ├── cli-output.log        # Full CLI stdout/stderr
            └── metadata.json         # Timing and exit codes
```

## Evaluation

### Structural checks (implemented)

Deterministic checks that run automatically:
- Pipeline completion (all steps exit code 0)
- File existence (manifest, template, plan, build prompt, growth loops)
- JSON validity
- Schema conformance (manifest validated against `GrowthManifest` model)
- Markdown minimum length

### LLM-as-judge (planned)

Future: uses a separate LLM to score output quality on criteria like completeness, actionability, and specificity.

## Adding Codebases

See `benchmarks/codebases/README.md` for instructions on populating sample codebases.
