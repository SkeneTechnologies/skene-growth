"""
Configuration file support for skene-growth.

Supports loading config from:
1. Project-level: ./.skene-growth.config
2. User-level: ~/.config/skene-growth/config

Priority: CLI args > environment variables > project config > user config
"""

import os
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore


DEFAULT_MODEL_BY_PROVIDER = {
    "openai": "gpt-4o",
    "gemini": "gemini-3-flash-preview",  # v1beta API requires -preview suffix
    "anthropic": "claude-sonnet-4-5",
    "ollama": "llama3.3",
    "generic": "custom-model",
}


def default_model_for_provider(provider: str) -> str:
    """Return the default model for a given provider."""
    return DEFAULT_MODEL_BY_PROVIDER.get(provider.lower(), "gpt-4o-mini")


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
        key = self.get("api_key")
        # Treat empty strings as None
        return key if key else None

    @property
    def provider(self) -> str:
        """Get LLM provider."""
        return self.get("provider", "openai")

    @property
    def output_dir(self) -> str:
        """Get default output directory."""
        return self.get("output_dir", "./skene-context")

    @property
    def verbose(self) -> bool:
        """Get verbose flag."""
        return self.get("verbose", False)

    @property
    def debug(self) -> bool:
        """Get debug flag for LLM input/output logging."""
        return self.get("debug", False)

    @property
    def model(self) -> str:
        """Get LLM model name."""
        model = self.get("model")
        if model:
            return model
        return default_model_for_provider(self.provider)

    @property
    def exclude_folders(self) -> list[str]:
        """Get list of folder names to exclude from analysis."""
        exclude = self.get("exclude_folders")
        if exclude:
            if isinstance(exclude, list):
                return exclude
            elif isinstance(exclude, str):
                return [exclude]
        return []

    @property
    def base_url(self) -> str | None:
        """Get base URL for OpenAI-compatible providers."""
        return self.get("base_url")

    @property
    def upstream(self) -> str | None:
        """Get upstream URL for deploy push (e.g. https://skene.ai/workspace/my-app)."""
        url = self.get("upstream")
        return url if url else None

    @property
    def upstream_token(self) -> str | None:
        """Get upstream API token. Precedence: SKENE_UPSTREAM_TOKEN env > config > credentials file."""
        return self.get("upstream_token")


def find_project_config() -> Path | None:
    """Find project-level config file (.skene-growth.config)."""
    cwd = Path.cwd()

    # Search up the directory tree
    for parent in [cwd, *cwd.parents]:
        config_path = parent / ".skene-growth.config"
        if config_path.exists():
            return config_path

    return None


def find_user_config() -> Path | None:
    """Find user-level config file (~/.config/skene-growth/config)."""
    # XDG_CONFIG_HOME or ~/.config
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        config_dir = Path(config_home) / "skene-growth"
    else:
        config_dir = Path.home() / ".config" / "skene-growth"

    config_path = config_dir / "config"
    if config_path.exists():
        return config_path

    return None


def get_credentials_path() -> Path:
    """Return path to user-level credentials file (for upstream token)."""
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        return Path(config_home) / "skene-growth" / "credentials"
    return Path.home() / ".config" / "skene-growth" / "credentials"


def resolve_upstream_token(config: Config) -> str | None:
    """
    Resolve upstream token in precedence order:
    1. SKENE_UPSTREAM_TOKEN env (already in config)
    2. Config file upstream_token
    3. Credentials file (~/.config/skene-growth/credentials)
    """
    token = config.upstream_token
    if not token:
        cred_path = get_credentials_path()
        if cred_path.exists():
            try:
                data = load_toml(cred_path)
                token = data.get("token") or data.get("upstream_token")
            except Exception:
                pass
    return token.strip() if isinstance(token, str) and token else None


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
    3. Project-level config (./.skene-growth.config)
    4. User-level config (~/.config/skene-growth/config)
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
    if base_url := os.environ.get("SKENE_BASE_URL"):
        config.set("base_url", base_url)
    if os.environ.get("SKENE_DEBUG", "").lower() in ("1", "true", "yes"):
        config.set("debug", True)
    if upstream_token := os.environ.get("SKENE_UPSTREAM_TOKEN"):
        config.set("upstream_token", upstream_token.strip() if upstream_token else None)

    return config
