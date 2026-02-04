"""
Model registry for loading and validating YAML model configurations.
"""

import os
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ModelConfig:
    """Configuration for a single model."""

    id: str
    name: str
    huggingface_repo: str
    filename: str
    quantization: str
    context_length: int
    chat_format: str


@dataclass
class RegistryDefaults:
    """Default settings from the registry."""

    model: str
    n_ctx: int
    n_gpu_layers: int


class ModelRegistry:
    """
    Loads and manages model configurations from YAML files.

    Loads the default registry from the package data, and optionally
    merges user-defined models from ~/.config/skene-growth/models.yaml.
    """

    def __init__(self):
        self._models: dict[str, ModelConfig] = {}
        self._defaults: RegistryDefaults | None = None
        self._load_registries()

    def _load_registries(self) -> None:
        """Load default and user registries."""
        # Load default registry from package data
        default_data = self._load_default_registry()
        if default_data:
            self._parse_registry(default_data)

        # Load user registry (overrides/extends defaults)
        user_data = self._load_user_registry()
        if user_data:
            self._parse_registry(user_data)

    def _load_default_registry(self) -> dict[str, Any] | None:
        """Load the default models.yaml from package data."""
        try:
            # Python 3.9+ style
            with resources.files("skene_growth.data").joinpath("models.yaml").open("r") as f:
                return yaml.safe_load(f)
        except Exception:
            # Fallback: try to find the file relative to this module
            try:
                module_dir = Path(__file__).parent.parent.parent
                default_path = module_dir / "data" / "models.yaml"
                if default_path.exists():
                    with open(default_path, "r") as f:
                        return yaml.safe_load(f)
            except Exception:
                pass
        return None

    def _load_user_registry(self) -> dict[str, Any] | None:
        """Load user models.yaml from config directory."""
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            config_dir = Path(config_home) / "skene-growth"
        else:
            config_dir = Path.home() / ".config" / "skene-growth"

        user_registry = config_dir / "models.yaml"
        if user_registry.exists():
            try:
                with open(user_registry, "r") as f:
                    return yaml.safe_load(f)
            except Exception:
                pass
        return None

    def _parse_registry(self, data: dict[str, Any]) -> None:
        """Parse registry data and populate models."""
        if not data:
            return

        # Parse models
        models = data.get("models", {})
        for model_id, model_data in models.items():
            self._models[model_id] = ModelConfig(
                id=model_id,
                name=model_data.get("name", model_id),
                huggingface_repo=model_data.get("huggingface_repo", ""),
                filename=model_data.get("filename", ""),
                quantization=model_data.get("quantization", ""),
                context_length=model_data.get("context_length", 4096),
                chat_format=model_data.get("chat_format", "chatml"),
            )

        # Parse defaults
        defaults = data.get("defaults", {})
        if defaults:
            self._defaults = RegistryDefaults(
                model=defaults.get("model", "qwen-2.5-3b"),
                n_ctx=defaults.get("n_ctx", 4096),
                n_gpu_layers=defaults.get("n_gpu_layers", -1),
            )

    def get_model(self, model_id: str) -> ModelConfig | None:
        """Get a model configuration by ID."""
        return self._models.get(model_id)

    def list_models(self) -> list[ModelConfig]:
        """List all available models."""
        return list(self._models.values())

    def get_default_model_id(self) -> str:
        """Get the default model ID."""
        if self._defaults:
            return self._defaults.model
        return "qwen-2.5-3b"

    def get_defaults(self) -> RegistryDefaults:
        """Get registry defaults."""
        if self._defaults:
            return self._defaults
        return RegistryDefaults(model="qwen-2.5-3b", n_ctx=4096, n_gpu_layers=-1)


# Global registry instance (lazy loaded)
_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    """Get the global model registry."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
