"""
Local LLM management module.

Provides model registry, download management, and model loading for
running GGUF models via llama-cpp-python.
"""

from skene_growth.llm.local.model_manager import (
    delete_model,
    download_model,
    get_model_path,
    get_model_status,
    get_models_dir,
    is_model_downloaded,
    list_models_status,
    load_model,
    load_model_from_path,
)
from skene_growth.llm.local.model_registry import (
    ModelConfig,
    ModelRegistry,
    RegistryDefaults,
    get_registry,
)

__all__ = [
    # Registry
    "ModelConfig",
    "ModelRegistry",
    "RegistryDefaults",
    "get_registry",
    # Manager
    "get_models_dir",
    "get_model_path",
    "is_model_downloaded",
    "get_model_status",
    "list_models_status",
    "download_model",
    "delete_model",
    "load_model",
    "load_model_from_path",
]
