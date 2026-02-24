"""Pydantic models for benchmark configuration and runtime results."""

import tomllib
from pathlib import Path

from pydantic import BaseModel, field_validator


class BenchmarkSettings(BaseModel):
    """Global benchmark settings."""

    judge_provider: str = "anthropic"
    judge_model: str = "claude-sonnet-4-5"
    judge_api_key_env: str = "ANTHROPIC_API_KEY"
    runs_per_combo: int = 1
    delay_between_calls: int = 0


class CodebaseConfig(BaseModel):
    """A codebase to benchmark against."""

    name: str
    path: Path
    ground_truth: Path | None = None

    @field_validator("path")
    @classmethod
    def validate_path_exists(cls, v: Path) -> Path:
        resolved = v.resolve()
        if not resolved.exists():
            raise ValueError(f"Codebase path does not exist: {resolved}")
        if not resolved.is_dir():
            raise ValueError(f"Codebase path is not a directory: {resolved}")
        return resolved

    @field_validator("ground_truth")
    @classmethod
    def validate_ground_truth_exists(cls, v: Path | None) -> Path | None:
        if v is None:
            return None
        resolved = v.resolve()
        if not resolved.exists():
            raise ValueError(f"Ground truth file does not exist: {resolved}")
        return resolved


class ModelConfig(BaseModel):
    """An LLM provider/model combo to benchmark."""

    name: str
    provider: str
    model: str
    api_key_env: str


class BenchmarkConfig(BaseModel):
    """Top-level benchmark configuration."""

    settings: BenchmarkSettings = BenchmarkSettings()
    codebases: list[CodebaseConfig]
    models: list[ModelConfig]


class StepMetadata(BaseModel):
    """Metadata for a single pipeline step."""

    step_name: str
    exit_code: int
    duration_seconds: float
    command: list[str]
    success: bool


class PipelineResult(BaseModel):
    """Result of running the full pipeline for one combo."""

    codebase_name: str
    model_name: str
    provider: str
    model_id: str
    run_number: int
    output_dir: Path
    steps: list[StepMetadata]
    success: bool
    error_message: str | None = None


def load_benchmark_config(config_path: Path) -> BenchmarkConfig:
    """Load and validate benchmark configuration from a TOML file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    return BenchmarkConfig(**raw)


def resolve_api_keys(config: BenchmarkConfig) -> dict[str, str]:
    """Resolve API keys from environment variables.

    Returns a mapping of env var name -> key value.
    Raises ValueError if any required keys are missing.
    """
    import os

    required_envs: set[str] = set()
    for model in config.models:
        required_envs.add(model.api_key_env)

    resolved: dict[str, str] = {}
    missing: list[str] = []

    for env_name in sorted(required_envs):
        value = os.environ.get(env_name)
        if value:
            resolved[env_name] = value
        else:
            missing.append(env_name)

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return resolved
