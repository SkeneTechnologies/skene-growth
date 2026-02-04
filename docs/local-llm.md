# Local LLM Support

Run GGUF models directly via [llama-cpp-python](https://github.com/abetlen/llama-cpp-python), without requiring external services like Ollama or LM Studio.

## Installation

The local LLM feature requires the `local` optional dependency:

```bash
# Using pip
pip install skene-growth[local]

# Using poetry
poetry install -E local

# Using uv
uv pip install skene-growth[local]
```

### GPU Acceleration

For GPU acceleration, you need to install `llama-cpp-python` with the appropriate backend before installing skene-growth:

**CUDA (NVIDIA GPUs):**
```bash
CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
pip install skene-growth[local]
```

**Metal (Apple Silicon):**
```bash
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
pip install skene-growth[local]
```

**ROCm (AMD GPUs):**
```bash
CMAKE_ARGS="-DLLAMA_HIPBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
pip install skene-growth[local]
```

## Quick Start

```bash
# List available models
skene-growth models list

# Download a model
skene-growth models download qwen-2.5-3b

# Run analysis with local model
skene-growth analyze . --provider local --model qwen-2.5-3b
```

## CLI Commands

### `models list`

Show available models and their download status:

```bash
skene-growth models list
```

Output:
```
                     Available Local Models
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Model ID              ┃ Name         ┃ Status         ┃ Size    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ qwen-2.5-3b (default) │ Qwen 2.5 3B  │ Downloaded     │ 2.0 GB  │
│ llama-3.1-8b          │ Llama 3.1 8B │ Not downloaded │ -       │
│ qwen-2.5-14b          │ Qwen 2.5 14B │ Not downloaded │ -       │
└───────────────────────┴──────────────┴────────────────┴─────────┘
```

### `models download`

Download a model from Hugging Face:

```bash
skene-growth models download qwen-2.5-3b
skene-growth models download llama-3.1-8b
```

Models are stored in `~/.cache/skene-growth/models/`.

### `models delete`

Delete a downloaded model:

```bash
skene-growth models delete qwen-2.5-3b

# Skip confirmation
skene-growth models delete qwen-2.5-3b --force
```

## Available Models

The default model registry includes:

| Model ID | Name | Size | Context Length | Best For |
|----------|------|------|----------------|----------|
| `qwen-2.5-3b` | Qwen 2.5 3B | ~2 GB | 32K | Fast analysis, lower memory |
| `llama-3.1-8b` | Llama 3.1 8B | ~5 GB | 128K | Balanced performance |
| `qwen-2.5-14b` | Qwen 2.5 14B | ~9 GB | 32K | Higher quality output |

All models use Q4_K_M quantization for a good balance of quality and performance.

## Usage

### CLI

```bash
# Use default model (qwen-2.5-3b)
skene-growth analyze . --provider local

# Specify a model
skene-growth analyze . --provider local --model llama-3.1-8b

# Generate growth plan
skene-growth plan --provider local --model qwen-2.5-3b
```

### Python API

```python
import asyncio
from pydantic import SecretStr
from skene_growth.llm import create_llm_client

async def main():
    # Create client (model loads lazily on first use)
    client = create_llm_client(
        provider="local",
        api_key=SecretStr("unused"),  # Not needed for local models
        model_name="qwen-2.5-3b"
    )

    # Generate content
    response = await client.generate_content("Explain PLG in one sentence.")
    print(response)

    # Streaming
    async for chunk in client.generate_content_stream("Count from 1 to 5."):
        print(chunk, end="", flush=True)

asyncio.run(main())
```

### Using Custom GGUF Files

You can use any GGUF model file by passing the path directly:

```python
client = create_llm_client(
    provider="local",
    api_key=SecretStr("unused"),
    model_name="/path/to/your/model.gguf"
)
```

## Custom Model Registry

You can add your own models by creating a `models.yaml` file in your config directory:

**Location:** `~/.config/skene-growth/models.yaml`

```yaml
version: "1.0"

models:
  my-custom-model:
    name: "My Custom Model"
    huggingface_repo: "username/repo-name"
    filename: "model-q4_k_m.gguf"
    quantization: "Q4_K_M"
    context_length: 8192
    chat_format: "chatml"  # or "llama-3", "llama-2", etc.

  # Add more models...

defaults:
  model: "my-custom-model"  # Set your preferred default
  n_ctx: 4096              # Default context length
  n_gpu_layers: -1         # -1 = auto (use GPU if available)
```

User models are merged with the default registry, so you can override existing models or add new ones.

### Chat Formats

Common chat format values:
- `chatml` - Qwen, many instruction-tuned models
- `llama-3` - Llama 3.x models
- `llama-2` - Llama 2 models
- `mistral-instruct` - Mistral models
- `alpaca` - Alpaca-style models

See [llama-cpp-python chat formats](https://github.com/abetlen/llama-cpp-python#chat-completion) for more options.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `XDG_CACHE_HOME` | Base directory for model storage | `~/.cache` |
| `XDG_CONFIG_HOME` | Base directory for user config | `~/.config` |

### Model Storage

Downloaded models are stored in:
- `~/.cache/skene-growth/models/` (or `$XDG_CACHE_HOME/skene-growth/models/`)

### Memory Requirements

Approximate RAM requirements for Q4_K_M quantized models:

| Model Size | RAM Required |
|------------|--------------|
| 3B params  | ~4 GB |
| 7-8B params | ~6-8 GB |
| 13-14B params | ~10-12 GB |

GPU offloading can reduce RAM usage. Set `n_gpu_layers` in the registry defaults or use the default `-1` (auto) to automatically use GPU when available.

## Troubleshooting

### Model not found

```
ValueError: Model 'xyz' not found in registry. Available models: [...]
```

Check available models with `skene-growth models list` or add the model to your custom registry.

### Model not downloaded

```
ValueError: Model 'qwen-2.5-3b' is not downloaded. Run: skene-growth models download qwen-2.5-3b
```

Download the model first with `skene-growth models download <model-id>`.

### Out of memory

If you run out of memory:
1. Use a smaller model (e.g., `qwen-2.5-3b` instead of `qwen-2.5-14b`)
2. Reduce context length in your custom registry
3. Enable GPU offloading if you have a compatible GPU

### llama-cpp-python not installed

```
RuntimeError: llama-cpp-python is required for local models. Install with: pip install skene-growth[local]
```

Install the local dependencies:
```bash
pip install skene-growth[local]
```

### Slow generation

- Enable GPU acceleration (see [GPU Acceleration](#gpu-acceleration))
- Use a smaller model
- Reduce context length

## Comparison with Other Local Options

| Feature | `local` provider | LM Studio | Ollama |
|---------|-----------------|-----------|--------|
| External service | No | Yes | Yes |
| Model management | Built-in CLI | GUI | CLI |
| GPU support | CUDA, Metal, ROCm | Auto | Auto |
| Setup complexity | pip install | Download app | Download + serve |
| Memory control | Fine-grained | Limited | Limited |
| Custom models | GGUF files | GGUF files | Ollama library |

Use the `local` provider when you want:
- No external services running
- Fine-grained control over model loading
- Easy integration with Python code
- Portable model management
