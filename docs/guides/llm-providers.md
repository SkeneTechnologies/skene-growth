# LLM Providers

How to configure skene-growth with different LLM providers, including cloud APIs and local models.

## Provider comparison

| Provider | Provider flag | Default model | API key required | Notes |
|----------|--------------|---------------|-----------------|-------|
| OpenAI | `openai` | `gpt-4o` | Yes | Default provider |
| Gemini | `gemini` | `gemini-3-flash-preview` | Yes | Uses v1beta API |
| Anthropic | `anthropic` or `claude` | `claude-sonnet-4-5` | Yes | Both aliases work |
| LM Studio | `lmstudio` | `custom-model` | No | Local, requires running server |
| Ollama | `ollama` | `llama3.3` | No | Local, requires running server |
| Generic | `generic` | `custom-model` | Depends | Any OpenAI-compatible endpoint |

## Setting the provider

There are three ways to configure your provider, model, and API key:

```bash
# 1. CLI flags (highest priority)
uvx skene-growth analyze . --provider gemini --model gemini-3-flash-preview --api-key "your-key"

# 2. Environment variables
export SKENE_API_KEY="your-key"
export SKENE_PROVIDER="gemini"

# 3. Config file (.skene-growth.config)
uvx skene-growth config  # Interactive setup
```

See [Configuration](configuration.md) for the full priority order.

## OpenAI

The default provider. Get an API key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

Any OpenAI model can be used via `--model`. The default is `gpt-4o`.

```bash
uvx skene-growth analyze . --provider openai --api-key "sk-..."

# gpt-4o is the default, but you can specify any OpenAI model
uvx skene-growth analyze . --model gpt-4o-mini --api-key "sk-..."
```

## Gemini

Google's Gemini models via the v1beta API. Get an API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

Any Gemini model can be used via `--model`. The default is `gemini-3-flash-preview`.

```bash
uvx skene-growth analyze . --provider gemini --api-key "your-gemini-key"

# Use a specific model
uvx skene-growth analyze . --provider gemini --model gemini-2.5-pro --api-key "your-gemini-key"
```

> **Note**: The v1beta API requires the `-preview` suffix on Gemini 3.x models.

## Anthropic / Claude

Anthropic's Claude models. Get an API key at [console.anthropic.com](https://console.anthropic.com/). Both `anthropic` and `claude` work as provider names.

Any Claude model can be used via `--model`. The default is `claude-sonnet-4-5`.

```bash
uvx skene-growth analyze . --provider anthropic --api-key "sk-ant-..."

# Or use the "claude" alias
uvx skene-growth analyze . --provider claude --api-key "sk-ant-..."

# Use a specific model
uvx skene-growth analyze . --provider claude --model claude-haiku-4-5 --api-key "sk-ant-..."
```

## LM Studio

Run models locally with [LM Studio](https://lmstudio.ai/). No API key required.

Use `--model` to specify whichever model you have loaded in LM Studio. If omitted, skene-growth sends `custom-model` as the model name (LM Studio typically ignores this and uses whichever model is currently loaded).

```bash
# Make sure LM Studio is running with a model loaded
uvx skene-growth analyze . --provider lmstudio

# Specify the model name if needed
uvx skene-growth analyze . --provider lmstudio --model "your-loaded-model"
```

**Default server URL**: `http://localhost:1234/v1`

To use a custom port, set the `LMSTUDIO_BASE_URL` environment variable:

```bash
export LMSTUDIO_BASE_URL="http://localhost:8080/v1"
```

The provider also accepts `lm-studio` and `lm_studio` as aliases.

See [Troubleshooting](../troubleshooting.md) for common LM Studio issues.

## Ollama

Run models locally with [Ollama](https://ollama.com/). No API key required.

Use `--model` to specify whichever model you have pulled in Ollama. The default is `llama3.3`.

```bash
# Pull a model first
ollama pull llama3.3

# Make sure Ollama is running
ollama serve

# Analyze
uvx skene-growth analyze . --provider ollama

# Specify a model
uvx skene-growth analyze . --provider ollama --model mistral
```

**Default server URL**: `http://localhost:11434/v1`

To use a custom port, set the `OLLAMA_BASE_URL` environment variable:

```bash
export OLLAMA_BASE_URL="http://localhost:8080/v1"
```

See [Troubleshooting](../troubleshooting.md) for common Ollama issues.

## Generic (OpenAI-compatible)

Connect to any OpenAI-compatible API endpoint. Requires `--base-url` or the `SKENE_BASE_URL` environment variable.

```bash
# With API key
uvx skene-growth analyze . --provider generic --base-url "https://your-api.com/v1" --api-key "your-key" --model "your-model"

# Local endpoint without API key
uvx skene-growth analyze . --provider generic --base-url "http://localhost:8000/v1" --model "local-model"
```

The provider also accepts `openai-compatible` and `openai_compatible` as aliases.

## Rate limiting & fallback

When an LLM provider returns a rate limit error, skene-growth automatically falls back to a cheaper model to keep the workflow moving.
This is convenient for interactive use but can corrupt results during benchmarking or when you need guaranteed output from a specific model.

### Disabling fallback

Pass `--no-fallback` to disable model switching. Instead of falling back, the CLI retries the **same** model with exponential backoff and raises an error if all retries are exhausted:

```bash
uvx skene-growth analyze . --provider gemini --model gemini-3-flash-preview --no-fallback
uvx skene-growth plan --no-fallback
uvx skene-growth build --no-fallback
```

This flag is available on the `analyze`, `plan`, and `build` commands.

## Next steps

- [Configuration](configuration.md) — Save provider settings to a config file
- [Troubleshooting](../troubleshooting.md) — Fix common provider issues
