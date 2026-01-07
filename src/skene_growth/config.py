"""
Configuration file support for skene-growth.

Supports loading config from:
1. Project-level: ./.skene-growth.toml
2. User-level: ~/.config/skene-growth/config.toml

Priority: CLI args > environment variables > project config > user config
"""

import os
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore


class Config:
    """Configuration container with hierarchical loading."""

    def __init__(self):
        self._values: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value."""
        return self._values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a config value."""
        self._values[key] = value

    def update(self, values: dict[str, Any]) -> None:
        """Update config with new values (existing values take precedence)."""
        for key, value in values.items():
            if key not in self._values:
                self._values[key] = value

    @property
    def api_key(self) -> str | None:
        """Get API key."""
        return self.get("api_key")

    @property
    def provider(self) -> str:
        """Get LLM provider."""
        return self.get("provider", "gemini")

    @property
    def output_dir(self) -> str:
        """Get default output directory."""
        return self.get("output_dir", "./skene-context")

    @property
    def verbose(self) -> bool:
        """Get verbose flag."""
        return self.get("verbose", False)


def find_project_config() -> Path | None:
    """Find project-level config file (.skene-growth.toml)."""
    cwd = Path.cwd()

    # Search up the directory tree
    for parent in [cwd, *cwd.parents]:
        config_path = parent / ".skene-growth.toml"
        if config_path.exists():
            return config_path

    return None


def find_user_config() -> Path | None:
    """Find user-level config file (~/.config/skene-growth/config.toml)."""
    # XDG_CONFIG_HOME or ~/.config
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        config_dir = Path(config_home) / "skene-growth"
    else:
        config_dir = Path.home() / ".config" / "skene-growth"

    config_path = config_dir / "config.toml"
    if config_path.exists():
        return config_path

    return None


def load_toml(path: Path) -> dict[str, Any]:
    """Load a TOML file."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config() -> Config:
    """
    Load configuration with proper precedence.

    Priority (highest to lowest):
    1. CLI arguments (applied later by CLI)
    2. Environment variables
    3. Project-level config (./.skene-growth.toml)
    4. User-level config (~/.config/skene-growth/config.toml)
    """
    config = Config()

    # Start with user config (lowest priority)
    user_config = find_user_config()
    if user_config:
        try:
            data = load_toml(user_config)
            config.update(data)
        except Exception:
            pass  # Ignore malformed config

    # Apply project config (higher priority)
    project_config = find_project_config()
    if project_config:
        try:
            data = load_toml(project_config)
            # Project config overwrites user config
            for key, value in data.items():
                config.set(key, value)
        except Exception:
            pass  # Ignore malformed config

    # Apply environment variables (highest priority before CLI)
    if api_key := os.environ.get("SKENE_API_KEY"):
        config.set("api_key", api_key)
    if provider := os.environ.get("SKENE_PROVIDER"):
        config.set("provider", provider)

    return config
