"""Benchmark runner entry point.

Usage:
    uv run benchmarks/run.py
    uv run benchmarks/run.py --config benchmarks/config.toml
    uv run benchmarks/run.py --skip-judge
    uv run benchmarks/run.py --evaluate-only results/2025-02-16T14-30-00
"""

import os
import sys
from pathlib import Path

import typer
from loguru import logger

# Ensure project root is on sys.path so `benchmarks.*` imports resolve
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Configure loguru: stderr, concise format
logger.remove()
logger.add(sys.stderr, format="{time:HH:mm:ss} | {level:<7} | {message}", level="INFO")

app = typer.Typer(add_completion=False)


@app.command()
def main(
    config: Path = typer.Option(
        Path("benchmarks/config.toml"),
        "--config",
        help="Path to benchmark config TOML file",
    ),
    skip_judge: bool = typer.Option(
        False,
        "--skip-judge",
        help="Skip LLM-as-judge evaluation",
    ),
    evaluate_only: Path | None = typer.Option(
        None,
        "--evaluate-only",
        help="Re-evaluate existing results directory (stub — not yet implemented)",
    ),
) -> None:
    """Run the skene-growth benchmark suite."""
    from benchmarks.evaluation.llm_judge import evaluate_with_llm_judge
    from benchmarks.evaluation.report import generate_report
    from benchmarks.evaluation.structural import evaluate_structural
    from benchmarks.runner.models import load_benchmark_config, resolve_api_keys
    from benchmarks.runner.orchestrator import create_timestamped_results_dir, run_benchmark_matrix

    if evaluate_only:
        logger.error("--evaluate-only is not yet implemented")
        raise typer.Exit(1)

    # Load config
    logger.info(f"Loading config from {config}")
    try:
        bench_config = load_benchmark_config(config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise typer.Exit(1)

    logger.info(
        f"Config: {len(bench_config.codebases)} codebase(s), "
        f"{len(bench_config.models)} model(s), "
        f"{bench_config.settings.runs_per_combo} run(s) per combo"
    )

    # Resolve API keys
    try:
        api_keys = resolve_api_keys(bench_config)
    except ValueError as e:
        logger.error(str(e))
        raise typer.Exit(1)

    logger.info(f"Resolved {len(api_keys)} API key(s)")

    # Create results directory
    results_base = Path("benchmarks/results")
    results_dir = create_timestamped_results_dir(results_base)
    logger.info(f"Results directory: {results_dir}")

    # Run benchmark matrix
    results = run_benchmark_matrix(bench_config, api_keys, results_dir)

    # Structural evaluation
    logger.info("Running structural evaluation...")
    structural_evals = [evaluate_structural(r) for r in results]

    # LLM judge evaluation (optional)
    if not skip_judge:
        judge_key_env = bench_config.settings.judge_api_key_env
        judge_api_key = os.environ.get(judge_key_env)
        for r in results:
            evaluate_with_llm_judge(
                r,
                judge_provider=bench_config.settings.judge_provider,
                judge_model=bench_config.settings.judge_model,
                judge_api_key=judge_api_key,
            )

    # Generate report
    json_path, md_path = generate_report(results, structural_evals, results_dir)

    # Summary
    successful = sum(1 for r in results if r.success)
    logger.info(f"Done! {successful}/{len(results)} runs succeeded")
    logger.info(f"Report: {md_path}")
    logger.info(f"Data:   {json_path}")

    # Print to stdout so it's visible even when stderr is noisy
    print(f"\n{'=' * 60}")
    print(f"Benchmark complete: {successful}/{len(results)} runs succeeded")
    print(f"Report: {md_path}")
    print(f"Data:   {json_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    app()
