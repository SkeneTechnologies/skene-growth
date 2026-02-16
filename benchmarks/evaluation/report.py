"""Report generation: summary.json and summary.md from benchmark results."""

import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from benchmarks.evaluation.models import StructuralEvaluation
from benchmarks.runner.models import PipelineResult
from benchmarks.runner.pipeline import _redact_command


def generate_report(
    results: list[PipelineResult],
    structural_evals: list[StructuralEvaluation],
    output_dir: Path,
) -> tuple[Path, Path]:
    """Generate summary.json and summary.md from benchmark results.

    Args:
        results: All pipeline results.
        structural_evals: Structural evaluation results (one per pipeline result).
        output_dir: Timestamped results directory to write reports to.

    Returns:
        Tuple of (summary_json_path, summary_md_path).
    """
    logger.info("Generating reports...")

    # Build summary data
    summary_data = _build_summary_data(results, structural_evals)

    # Write summary.json
    json_path = output_dir / "summary.json"
    with open(json_path, "w") as f:
        json.dump(summary_data, f, indent=2, default=str)
    logger.info(f"Wrote {json_path}")

    # Write summary.md
    md_path = output_dir / "summary.md"
    md_content = _build_summary_markdown(results, structural_evals, summary_data)
    md_path.write_text(md_content)
    logger.info(f"Wrote {md_path}")

    return json_path, md_path


def _build_summary_data(
    results: list[PipelineResult],
    structural_evals: list[StructuralEvaluation],
) -> dict:
    """Build the summary.json data structure."""
    # Index evaluations by (codebase, model, run)
    eval_index: dict[tuple[str, str, int], StructuralEvaluation] = {}
    for ev in structural_evals:
        eval_index[(ev.codebase_name, ev.model_name, ev.run_number)] = ev

    result_entries = []
    for r in results:
        ev = eval_index.get((r.codebase_name, r.model_name, r.run_number))
        entry = {
            "codebase": r.codebase_name,
            "model": r.model_name,
            "provider": r.provider,
            "model_id": r.model_id,
            "run_number": r.run_number,
            "success": r.success,
            "error_message": r.error_message,
            "output_dir": str(r.output_dir),
            "steps": [{**s.model_dump(), "command": _redact_command(s.command)} for s in r.steps],
            "total_duration_seconds": round(sum(s.duration_seconds for s in r.steps), 2),
            "structural_score": ev.score if ev else None,
            "structural_checks": [c.model_dump() for c in ev.checks] if ev else [],
        }
        result_entries.append(entry)

    return {
        "generated_at": datetime.now().isoformat(),
        "total_runs": len(results),
        "successful_runs": sum(1 for r in results if r.success),
        "results": result_entries,
    }


def _build_summary_markdown(
    results: list[PipelineResult],
    structural_evals: list[StructuralEvaluation],
    summary_data: dict,
) -> str:
    """Build the summary.md content."""
    lines: list[str] = []
    lines.append("# Benchmark Results\n")
    lines.append(f"Generated: {summary_data['generated_at']}\n")
    lines.append(f"Total runs: {summary_data['total_runs']} | "
                 f"Successful: {summary_data['successful_runs']}\n")

    # Comparison table
    codebases = sorted(set(r.codebase_name for r in results))
    models = sorted(set(r.model_name for r in results))

    eval_index: dict[tuple[str, str, int], StructuralEvaluation] = {}
    for ev in structural_evals:
        eval_index[(ev.codebase_name, ev.model_name, ev.run_number)] = ev

    if codebases and models:
        lines.append("\n## Comparison Table\n")
        # Header
        header = "| Model |"
        separator = "| --- |"
        for cb in codebases:
            header += f" {cb} |"
            separator += " --- |"
        lines.append(header)
        lines.append(separator)

        # Rows
        for model_name in models:
            row = f"| {model_name} |"
            for cb in codebases:
                # Average score across runs for this combo
                scores = []
                for r in results:
                    if r.codebase_name == cb and r.model_name == model_name:
                        ev = eval_index.get((cb, model_name, r.run_number))
                        if ev:
                            scores.append(ev.score)
                if scores:
                    avg = sum(scores) / len(scores)
                    row += f" {avg:.0%} |"
                else:
                    row += " N/A |"
            lines.append(row)

    # Per-codebase breakdown
    lines.append("\n## Per-Codebase Breakdown\n")
    for cb in codebases:
        lines.append(f"\n### {cb}\n")
        cb_results = [r for r in results if r.codebase_name == cb]
        for r in cb_results:
            ev = eval_index.get((r.codebase_name, r.model_name, r.run_number))
            status = "PASS" if r.success else "FAIL"
            score_str = f"{ev.score:.0%}" if ev else "N/A"
            lines.append(f"- **{r.model_name}** (run {r.run_number}): {status} | "
                         f"Structural: {score_str}")

            if ev:
                failed_checks = [c for c in ev.checks if not c.passed]
                if failed_checks:
                    for c in failed_checks:
                        detail = f" — {c.detail}" if c.detail else ""
                        lines.append(f"  - FAIL: {c.check_name}{detail}")

    # Timing analysis
    lines.append("\n## Timing Analysis\n")
    lines.append("| Model | Codebase | Step | Duration (s) |")
    lines.append("| --- | --- | --- | --- |")
    for r in results:
        for step in r.steps:
            lines.append(f"| {r.model_name} | {r.codebase_name} | {step.step_name} | {step.duration_seconds:.1f} |")

    # Highlights
    lines.append("\n## Highlights\n")

    if structural_evals:
        best = max(structural_evals, key=lambda e: e.score)
        worst = min(structural_evals, key=lambda e: e.score)
        lines.append(f"- **Best structural score**: {best.model_name} on {best.codebase_name} ({best.score:.0%})")
        lines.append(f"- **Worst structural score**: {worst.model_name} on {worst.codebase_name} ({worst.score:.0%})")

    # Common failures
    failure_counts: dict[str, int] = {}
    for ev in structural_evals:
        for c in ev.checks:
            if not c.passed:
                failure_counts[c.check_name] = failure_counts.get(c.check_name, 0) + 1

    if failure_counts:
        lines.append("\n### Common Failures\n")
        for check_name, count in sorted(failure_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- `{check_name}`: failed {count} time(s)")

    lines.append("")
    return "\n".join(lines)
