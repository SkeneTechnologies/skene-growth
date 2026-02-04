"""
Model manager for downloading, storing, and loading local LLM models.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from skene_growth.llm.local.model_registry import get_registry


@dataclass
class ModelStatus:
    """Status information for a model."""

    model_id: str
    name: str
    downloaded: bool
    path: Path | None
    size_bytes: int | None


def get_models_dir() -> Path:
    """Get the directory for storing downloaded models."""
    cache_home = os.environ.get("XDG_CACHE_HOME")
    if cache_home:
        cache_dir = Path(cache_home) / "skene-growth" / "models"
    else:
        cache_dir = Path.home() / ".cache" / "skene-growth" / "models"

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_model_path(model_id: str) -> Path | None:
    """
    Get the path to a downloaded model file.

    Args:
        model_id: Model identifier from the registry

    Returns:
        Path to the model file if downloaded, None otherwise
    """
    registry = get_registry()
    config = registry.get_model(model_id)
    if not config:
        return None

    model_path = get_models_dir() / config.filename
    if model_path.exists():
        return model_path
    return None


def is_model_downloaded(model_id: str) -> bool:
    """Check if a model has been downloaded."""
    return get_model_path(model_id) is not None


def get_model_status(model_id: str) -> ModelStatus | None:
    """Get the status of a model."""
    registry = get_registry()
    config = registry.get_model(model_id)
    if not config:
        return None

    model_path = get_model_path(model_id)
    size_bytes = None
    if model_path and model_path.exists():
        size_bytes = model_path.stat().st_size

    return ModelStatus(
        model_id=model_id,
        name=config.name,
        downloaded=model_path is not None,
        path=model_path,
        size_bytes=size_bytes,
    )


def list_models_status() -> list[ModelStatus]:
    """List all models and their download status."""
    registry = get_registry()
    statuses = []
    for model in registry.list_models():
        status = get_model_status(model.id)
        if status:
            statuses.append(status)
    return statuses


def download_model(model_id: str) -> Path:
    """
    Download a model from Hugging Face.

    Args:
        model_id: Model identifier from the registry

    Returns:
        Path to the downloaded model file

    Raises:
        ValueError: If model is not found in registry
        RuntimeError: If download fails
    """
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        raise RuntimeError(
            "huggingface_hub is required for downloading models. "
            "Install with: pip install skene-growth[local]"
        )

    registry = get_registry()
    config = registry.get_model(model_id)
    if not config:
        raise ValueError(f"Model '{model_id}' not found in registry")

    models_dir = get_models_dir()
    logger.info(f"Downloading {config.name} from {config.huggingface_repo}...")

    try:
        # Download to the cache directory
        downloaded_path = hf_hub_download(
            repo_id=config.huggingface_repo,
            filename=config.filename,
            local_dir=models_dir,
            local_dir_use_symlinks=False,
        )
        logger.info(f"Downloaded {config.name} to {downloaded_path}")
        return Path(downloaded_path)
    except Exception as e:
        raise RuntimeError(f"Failed to download model '{model_id}': {e}")


def delete_model(model_id: str) -> bool:
    """
    Delete a downloaded model.

    Args:
        model_id: Model identifier from the registry

    Returns:
        True if model was deleted, False if not found

    Raises:
        ValueError: If model is not found in registry
    """
    registry = get_registry()
    config = registry.get_model(model_id)
    if not config:
        raise ValueError(f"Model '{model_id}' not found in registry")

    model_path = get_model_path(model_id)
    if model_path and model_path.exists():
        model_path.unlink()
        logger.info(f"Deleted model {config.name}")
        return True

    return False


def load_model(model_id: str, n_ctx: int | None = None, n_gpu_layers: int | None = None):
    """
    Load a model using llama-cpp-python.

    Args:
        model_id: Model identifier from the registry
        n_ctx: Context length (defaults to registry defaults)
        n_gpu_layers: Number of GPU layers (defaults to registry defaults, -1 = auto)

    Returns:
        Loaded Llama model instance

    Raises:
        ValueError: If model is not found or not downloaded
        RuntimeError: If llama-cpp-python is not installed
    """
    try:
        from llama_cpp import Llama
    except ImportError:
        raise RuntimeError(
            "llama-cpp-python is required for local models. "
            "Install with: pip install skene-growth[local]"
        )

    registry = get_registry()
    config = registry.get_model(model_id)
    if not config:
        raise ValueError(f"Model '{model_id}' not found in registry")

    model_path = get_model_path(model_id)
    if not model_path:
        raise ValueError(
            f"Model '{model_id}' is not downloaded. "
            f"Run: skene-growth models download {model_id}"
        )

    defaults = registry.get_defaults()
    resolved_n_ctx = n_ctx if n_ctx is not None else defaults.n_ctx
    resolved_n_gpu_layers = n_gpu_layers if n_gpu_layers is not None else defaults.n_gpu_layers

    logger.info(f"Loading {config.name} with n_ctx={resolved_n_ctx}, n_gpu_layers={resolved_n_gpu_layers}")

    return Llama(
        model_path=str(model_path),
        n_ctx=resolved_n_ctx,
        n_gpu_layers=resolved_n_gpu_layers,
        chat_format=config.chat_format,
        verbose=False,
    )


def load_model_from_path(
    model_path: str | Path, chat_format: str = "chatml", n_ctx: int = 4096, n_gpu_layers: int = -1
):
    """
    Load a model from a custom path (bypasses registry).

    Args:
        model_path: Path to the GGUF model file
        chat_format: Chat format to use (default: chatml)
        n_ctx: Context length
        n_gpu_layers: Number of GPU layers (-1 = auto)

    Returns:
        Loaded Llama model instance

    Raises:
        RuntimeError: If llama-cpp-python is not installed
        ValueError: If model file not found
    """
    try:
        from llama_cpp import Llama
    except ImportError:
        raise RuntimeError(
            "llama-cpp-python is required for local models. "
            "Install with: pip install skene-growth[local]"
        )

    path = Path(model_path)
    if not path.exists():
        raise ValueError(f"Model file not found: {model_path}")

    logger.info(f"Loading model from {model_path}")

    return Llama(
        model_path=str(path),
        n_ctx=n_ctx,
        n_gpu_layers=n_gpu_layers,
        chat_format=chat_format,
        verbose=False,
    )
