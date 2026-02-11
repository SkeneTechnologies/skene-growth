"""Tests for configuration loading."""

import os
import tempfile
from pathlib import Path

import pytest

from skene_growth.config import (
    Config,
    default_model_for_provider,
    find_project_config,
    find_user_config,
    load_config,
    load_toml,
    DEFAULT_MODEL_BY_PROVIDER,
)


class TestDefaultModelForProvider:
    """Test default model selection."""

    def test_returns_correct_model_for_openai(self):
        """Test default model for OpenAI."""
        assert default_model_for_provider("openai") == "gpt-4o-mini"

    def test_returns_correct_model_for_gemini(self):
        """Test default model for Gemini."""
        assert default_model_for_provider("gemini") == "gemini-2.0-flash"

    def test_returns_correct_model_for_anthropic(self):
        """Test default model for Anthropic."""
        assert default_model_for_provider("anthropic") == "claude-sonnet-4-20250514"

    def test_returns_correct_model_for_ollama(self):
        """Test default model for Ollama."""
        assert default_model_for_provider("ollama") == "llama2"

    def test_returns_fallback_for_unknown_provider(self):
        """Test fallback model for unknown provider."""
        assert default_model_for_provider("unknown") == "gpt-4o-mini"

    def test_case_insensitive(self):
        """Test that provider names are case insensitive."""
        assert default_model_for_provider("OpenAI") == "gpt-4o-mini"
        assert default_model_for_provider("GEMINI") == "gemini-2.0-flash"


class TestConfig:
    """Test Config class."""

    def test_initialization_creates_empty_values(self):
        """Test that new Config has empty values."""
        config = Config()
        assert config._values == {}

    def test_get_returns_value(self):
        """Test getting a config value."""
        config = Config()
        config.set("key1", "value1")
        assert config.get("key1") == "value1"

    def test_get_returns_default_when_key_missing(self):
        """Test that get returns default for missing key."""
        config = Config()
        assert config.get("missing", "default") == "default"

    def test_get_returns_none_by_default(self):
        """Test that get returns None when no default specified."""
        config = Config()
        assert config.get("missing") is None

    def test_set_stores_value(self):
        """Test that set stores a value."""
        config = Config()
        config.set("key1", "value1")
        assert config._values["key1"] == "value1"

    def test_set_overwrites_existing_value(self):
        """Test that set overwrites existing values."""
        config = Config()
        config.set("key1", "original")
        config.set("key1", "updated")
        assert config.get("key1") == "updated"

    def test_update_adds_new_values(self):
        """Test that update adds new values."""
        config = Config()
        config.update({"key1": "value1", "key2": "value2"})
        assert config.get("key1") == "value1"
        assert config.get("key2") == "value2"

    def test_update_preserves_existing_values(self):
        """Test that update doesn't overwrite existing values."""
        config = Config()
        config.set("key1", "original")
        config.update({"key1": "new", "key2": "value2"})
        assert config.get("key1") == "original"  # Existing value preserved
        assert config.get("key2") == "value2"   # New value added


class TestConfigProperties:
    """Test Config property accessors."""

    def test_api_key_property(self):
        """Test api_key property."""
        config = Config()
        config.set("api_key", "test-key")
        assert config.api_key == "test-key"

    def test_api_key_returns_none_when_not_set(self):
        """Test that api_key returns None when not set."""
        config = Config()
        assert config.api_key is None

    def test_provider_property(self):
        """Test provider property."""
        config = Config()
        config.set("provider", "gemini")
        assert config.provider == "gemini"

    def test_provider_defaults_to_openai(self):
        """Test that provider defaults to openai."""
        config = Config()
        assert config.provider == "openai"

    def test_output_dir_property(self):
        """Test output_dir property."""
        config = Config()
        config.set("output_dir", "/custom/path")
        assert config.output_dir == "/custom/path"

    def test_output_dir_defaults_to_skene_context(self):
        """Test that output_dir defaults to ./skene-context."""
        config = Config()
        assert config.output_dir == "./skene-context"

    def test_verbose_property(self):
        """Test verbose property."""
        config = Config()
        config.set("verbose", True)
        assert config.verbose is True

    def test_verbose_defaults_to_false(self):
        """Test that verbose defaults to False."""
        config = Config()
        assert config.verbose is False

    def test_model_property_returns_set_model(self):
        """Test that model property returns the set model."""
        config = Config()
        config.set("model", "gpt-4")
        assert config.model == "gpt-4"

    def test_model_property_uses_provider_default(self):
        """Test that model property uses provider default when not set."""
        config = Config()
        config.set("provider", "gemini")
        assert config.model == "gemini-2.0-flash"

    def test_model_property_defaults_for_openai_provider(self):
        """Test model default for openai provider."""
        config = Config()
        # Provider defaults to openai
        assert config.model == "gpt-4o-mini"


class TestFindProjectConfig:
    """Test finding project config file."""

    def test_finds_config_in_current_directory(self, tmp_path, monkeypatch):
        """Test finding config in current directory."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / ".skene-growth.config"
        config_file.write_text("")

        found = find_project_config()
        assert found == config_file

    def test_finds_config_in_parent_directory(self, tmp_path, monkeypatch):
        """Test finding config in parent directory."""
        config_file = tmp_path / ".skene-growth.config"
        config_file.write_text("")

        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)

        found = find_project_config()
        assert found == config_file

    def test_returns_none_when_no_config_found(self, tmp_path, monkeypatch):
        """Test that it returns None when no config found."""
        monkeypatch.chdir(tmp_path)

        found = find_project_config()
        assert found is None


class TestFindUserConfig:
    """Test finding user config file."""

    def test_finds_config_in_xdg_config_home(self, tmp_path, monkeypatch):
        """Test finding config in XDG_CONFIG_HOME."""
        config_dir = tmp_path / "skene-growth"
        config_dir.mkdir()
        config_file = config_dir / "config"
        config_file.write_text("")

        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        found = find_user_config()
        assert found == config_file

    def test_finds_config_in_home_config(self, tmp_path, monkeypatch):
        """Test finding config in ~/.config when XDG_CONFIG_HOME not set."""
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))

        config_dir = tmp_path / ".config" / "skene-growth"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config"
        config_file.write_text("")

        found = find_user_config()
        assert found == config_file

    def test_returns_none_when_no_config_found(self, tmp_path, monkeypatch):
        """Test that it returns None when no config found."""
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        found = find_user_config()
        assert found is None


class TestLoadToml:
    """Test TOML loading."""

    def test_loads_valid_toml(self, tmp_path):
        """Test loading valid TOML file."""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text('[section]\nkey = "value"')

        data = load_toml(toml_file)
        assert data == {"section": {"key": "value"}}

    def test_loads_toml_with_multiple_keys(self, tmp_path):
        """Test loading TOML with multiple keys."""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text('provider = "gemini"\napi_key = "test"\nverbose = true')

        data = load_toml(toml_file)
        assert data["provider"] == "gemini"
        assert data["api_key"] == "test"
        assert data["verbose"] is True


class TestLoadConfig:
    """Test loading config with precedence."""

    def test_loads_config_from_environment(self, monkeypatch):
        """Test that environment variables are loaded."""
        monkeypatch.setenv("SKENE_API_KEY", "env-key")
        monkeypatch.setenv("SKENE_PROVIDER", "gemini")

        config = load_config()

        assert config.api_key == "env-key"
        assert config.provider == "gemini"

    def test_environment_overrides_project_config(self, tmp_path, monkeypatch):
        """Test that environment variables override project config."""
        monkeypatch.chdir(tmp_path)

        # Create project config
        config_file = tmp_path / ".skene-growth.config"
        config_file.write_text('provider = "anthropic"')

        # Set environment variable
        monkeypatch.setenv("SKENE_PROVIDER", "gemini")

        config = load_config()

        # Environment should win
        assert config.provider == "gemini"

    def test_project_config_overrides_user_config(self, tmp_path, monkeypatch):
        """Test that project config overrides user config."""
        monkeypatch.chdir(tmp_path)

        # Create user config
        user_config_dir = tmp_path / ".config" / "skene-growth"
        user_config_dir.mkdir(parents=True)
        user_config = user_config_dir / "config"
        user_config.write_text('provider = "openai"')
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

        # Create project config
        project_config = tmp_path / ".skene-growth.config"
        project_config.write_text('provider = "gemini"')

        config = load_config()

        # Project config should win
        assert config.provider == "gemini"

    def test_ignores_malformed_config(self, tmp_path, monkeypatch):
        """Test that malformed config is ignored."""
        monkeypatch.chdir(tmp_path)

        config_file = tmp_path / ".skene-growth.config"
        config_file.write_text('invalid toml {{{')

        # Should not raise error
        config = load_config()
        assert isinstance(config, Config)


class TestConfigIntegration:
    """Integration tests for config loading."""

    def test_full_config_precedence_chain(self, tmp_path, monkeypatch):
        """Test complete precedence chain: env > project > user."""
        monkeypatch.chdir(tmp_path)

        # User config (lowest priority)
        user_config_dir = tmp_path / ".config" / "skene-growth"
        user_config_dir.mkdir(parents=True)
        user_config = user_config_dir / "config"
        user_config.write_text('provider = "openai"\nverbose = false')
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

        # Project config (middle priority)
        project_config = tmp_path / ".skene-growth.config"
        project_config.write_text('provider = "gemini"\noutput_dir = "/project/output"')

        # Environment (highest priority)
        monkeypatch.setenv("SKENE_PROVIDER", "anthropic")
        monkeypatch.setenv("SKENE_API_KEY", "env-key")

        config = load_config()

        # Environment wins for provider and api_key
        assert config.provider == "anthropic"
        assert config.api_key == "env-key"

        # Project config wins for output_dir (not overridden by env)
        assert config.output_dir == "/project/output"

        # User config provides verbose (not overridden by project or env)
        assert config.verbose is False
