"""Orchestrator: iterates the benchmark matrix and manages output directories.

Combos are interleaved by provider to reduce the likelihood of hitting
rate/quota limits from a single provider.
"""

import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from loguru import logger

from benchmarks.runner.models import BenchmarkConfig, CodebaseConfig, ModelConfig, PipelineResult
from benchmarks.runner.pipeline import run_pipeline


def create_timestamped_results_dir(base_path: Path) -> Path:
    """Create a timestamped results directory."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    results_dir = base_path / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


def _interleave_by_provider(
    combos: list[tuple[CodebaseConfig, ModelConfig, int]],
) -> list[tuple[CodebaseConfig, ModelConfig, int]]:
    """Reorder combos so consecutive runs use different providers.

    Groups combos by provider, then round-robins across groups.
    This spreads API calls across providers and reduces quota pressure.
    """
    by_provider: dict[str, list[tuple[CodebaseConfig, ModelConfig, int]]] = defaultdict(list)
    for combo in combos:
        by_provider[combo[1].provider].append(combo)

    queues = list(by_provider.values())
    interleaved: list[tuple[CodebaseConfig, ModelConfig, int]] = []
    while queues:
        next_round = []
        for q in queues:
            interleaved.append(q.pop(0))
            if q:
                next_round.append(q)
        queues = next_round

    return interleaved


def run_benchmark_matrix(
    config: BenchmarkConfig,
    api_keys: dict[str, str],
    output_base_dir: Path,
) -> list[PipelineResult]:
    """Run the full benchmark matrix: codebase x model x run_number.

    Combos are interleaved by provider to avoid hammering a single
    provider's API consecutively.

    Args:
        config: Validated benchmark configuration.
        api_keys: Resolved API keys (env var name -> value).
        output_base_dir: Timestamped results directory.

    Returns:
        List of PipelineResult for each combo.
    """
    # Build full combo list
    combos: list[tuple[CodebaseConfig, ModelConfig, int]] = []
    for codebase in config.codebases:
        for model_cfg in config.models:
            for run_num in range(1, config.settings.runs_per_combo + 1):
                combos.append((codebase, model_cfg, run_num))

    # Interleave by provider
    combos = _interleave_by_provider(combos)

    results: list[PipelineResult] = []
    total = len(combos)

    for i, (codebase, model_cfg, run_num) in enumerate(combos, 1):
        api_key = api_keys[model_cfg.api_key_env]
        logger.info(f"[{i}/{total}] {codebase.name} / {model_cfg.name} / run-{run_num}")

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

        # Delay between calls to avoid hitting rate/quota limits
        delay = config.settings.delay_between_calls
        if delay > 0 and i < total:
            logger.info(f"  Waiting {delay}s before next call...")
            time.sleep(delay)

    return results
