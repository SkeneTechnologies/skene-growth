"""Orchestrator: iterates the benchmark matrix and manages output directories."""

from datetime import datetime
from pathlib import Path

from loguru import logger

from benchmarks.runner.models import BenchmarkConfig, PipelineResult
from benchmarks.runner.pipeline import run_pipeline


def create_timestamped_results_dir(base_path: Path) -> Path:
    """Create a timestamped results directory."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    results_dir = base_path / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


def run_benchmark_matrix(
    config: BenchmarkConfig,
    api_keys: dict[str, str],
    output_base_dir: Path,
) -> list[PipelineResult]:
    """Run the full benchmark matrix: codebase x model x run_number.

    Args:
        config: Validated benchmark configuration.
        api_keys: Resolved API keys (env var name -> value).
        output_base_dir: Timestamped results directory.

    Returns:
        List of PipelineResult for each combo.
    """
    results: list[PipelineResult] = []
    total_combos = len(config.codebases) * len(config.models) * config.settings.runs_per_combo
    current = 0

    for codebase in config.codebases:
        for model_cfg in config.models:
            api_key = api_keys[model_cfg.api_key_env]

            for run_num in range(1, config.settings.runs_per_combo + 1):
                current += 1
                logger.info(f"[{current}/{total_combos}] {codebase.name} / {model_cfg.name} / run-{run_num}")

                output_dir = output_base_dir / codebase.name / model_cfg.name / f"run-{run_num}"

                result = run_pipeline(
                    codebase_path=codebase.path,
                    codebase_name=codebase.name,
                    provider=model_cfg.provider,
                    model=model_cfg.model,
                    model_name=model_cfg.name,
                    api_key=api_key,
                    output_dir=output_dir,
                    run_number=run_num,
                )
                results.append(result)

                if result.success:
                    logger.info(f"  -> Success ({sum(s.duration_seconds for s in result.steps):.1f}s total)")
                else:
                    logger.warning(f"  -> Failed: {result.error_message}")

    return results
