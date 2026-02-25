"""Report generation: summary.json and summary.md from benchmark results."""

import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from benchmarks.evaluation.models import FactualEvaluation, StructuralEvaluation
from benchmarks.runner.models import PipelineResult
from benchmarks.runner.pipeline import _redact_command


def generate_report(
    results: list[PipelineResult],
    structural_evals: list[StructuralEvaluation],
    output_dir: Path,
    factual_evals: list[FactualEvaluation] | None = None,
) -> tuple[Path, Path]:
    """Generate summary.json and summary.md from benchmark results.

    Args:
        results: All pipeline results.
        structural_evals: Structural evaluation results (one per pipeline result).
        output_dir: Timestamped results directory to write reports to.
        factual_evals: Optional factual evaluation results (for codebases with ground truth).

    Returns:
        Tuple of (summary_json_path, summary_md_path).
    """
    logger.info("Generating reports...")
    factual_evals = factual_evals or []

    # Build summary data
    summary_data = _build_summary_data(results, structural_evals, factual_evals)

    # Write summary.json
    json_path = output_dir / "summary.json"
    with open(json_path, "w") as f:
        json.dump(summary_data, f, indent=2, default=str)
    logger.info(f"Wrote {json_path}")

    # Write summary.md
    md_path = output_dir / "summary.md"
    md_content = _build_summary_markdown(results, structural_evals, factual_evals, summary_data)
    md_path.write_text(md_content)
    logger.info(f"Wrote {md_path}")

    return json_path, md_path


def _build_summary_data(
    results: list[PipelineResult],
    structural_evals: list[StructuralEvaluation],
    factual_evals: list[FactualEvaluation],
) -> dict:
    """Build the summary.json data structure."""
    # Index evaluations by (codebase, model, run)
    eval_index: dict[tuple[str, str, int], StructuralEvaluation] = {}
    for ev in structural_evals:
        eval_index[(ev.codebase_name, ev.model_name, ev.run_number)] = ev

    factual_index: dict[tuple[str, str, int], FactualEvaluation] = {}
    for fev in factual_evals:
        factual_index[(fev.codebase_name, fev.model_name, fev.run_number)] = fev

    result_entries = []
    for r in results:
        ev = eval_index.get((r.codebase_name, r.model_name, r.run_number))
        fev = factual_index.get((r.codebase_name, r.model_name, r.run_number))
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
            "factual_score": fev.score if fev else None,
            "factual_category_scores": fev.category_scores if fev else None,
            "factual_checks": [c.model_dump() for c in fev.checks] if fev else [],
        }
        result_entries.append(entry)

    return {
        "generated_at": datetime.now().isoformat(),
        "total_runs": len(results),
        "successful_runs": sum(1 for r in results if r.success),
        "has_factual_evaluation": len(factual_evals) > 0,
        "results": result_entries,
    }


def _build_summary_markdown(
    results: list[PipelineResult],
    structural_evals: list[StructuralEvaluation],
    factual_evals: list[FactualEvaluation],
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

    factual_index: dict[tuple[str, str, int], FactualEvaluation] = {}
    for fev in factual_evals:
        factual_index[(fev.codebase_name, fev.model_name, fev.run_number)] = fev

    has_factual = len(factual_evals) > 0

    if codebases and models:
        lines.append("\n## Comparison Table\n")
        # Header
        header = "| Model |"
        separator = "| --- |"
        for cb in codebases:
            header += f" {cb} (structural) |"
            separator += " --- |"
            if has_factual:
                header += f" {cb} (factual) |"
                separator += " --- |"
        lines.append(header)
        lines.append(separator)

        # Rows
        for model_name in models:
            row = f"| {model_name} |"
            for cb in codebases:
                # Structural score
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

                # Factual score
                if has_factual:
                    fscores = []
                    for r in results:
                        if r.codebase_name == cb and r.model_name == model_name:
                            fev = factual_index.get((cb, model_name, r.run_number))
                            if fev:
                                fscores.append(fev.score)
                    if fscores:
                        favg = sum(fscores) / len(fscores)
                        row += f" {favg:.0%} |"
                    else:
                        row += " N/A |"
            lines.append(row)

    # Factual accuracy breakdown (category scores per model)
    if has_factual:
        lines.append("\n## Factual Accuracy Breakdown\n")

        # Collect all categories
        all_categories = sorted({cat for fev in factual_evals for cat in fev.category_scores})
        if all_categories:
            header = "| Model | Codebase |"
            separator = "| --- | --- |"
            for cat in all_categories:
                header += f" {cat} |"
                separator += " --- |"
            lines.append(header)
            lines.append(separator)

            for model_name in models:
                for cb in codebases:
                    # Find factual eval for this combo
                    fev = None
                    for r in results:
                        if r.codebase_name == cb and r.model_name == model_name:
                            fev = factual_index.get((cb, model_name, r.run_number))
                            break
                    if fev is None:
                        continue
                    row = f"| {model_name} | {cb} |"
                    for cat in all_categories:
                        cat_score = fev.category_scores.get(cat)
                        row += f" {cat_score:.0%} |" if cat_score is not None else " N/A |"
                    lines.append(row)

    # Per-codebase breakdown
    lines.append("\n## Per-Codebase Breakdown\n")
    for cb in codebases:
        lines.append(f"\n### {cb}\n")
        cb_results = [r for r in results if r.codebase_name == cb]
        for r in cb_results:
            ev = eval_index.get((r.codebase_name, r.model_name, r.run_number))
            fev = factual_index.get((r.codebase_name, r.model_name, r.run_number))
            status = "PASS" if r.success else "FAIL"
            score_str = f"{ev.score:.0%}" if ev else "N/A"
            factual_str = f" | Factual: {fev.score:.0%}" if fev else ""
            lines.append(f"- **{r.model_name}** (run {r.run_number}): {status} | "
                         f"Structural: {score_str}{factual_str}")

            if ev:
                failed_checks = [c for c in ev.checks if not c.passed]
                if failed_checks:
                    for c in failed_checks:
                        detail = f" — {c.detail}" if c.detail else ""
                        lines.append(f"  - FAIL: {c.check_name}{detail}")

            if fev:
                failed_factual = [c for c in fev.checks if not c.passed]
                if failed_factual:
                    for c in failed_factual:
                        detail = f" — expected: {c.expected}, got: {c.actual}" if c.expected else f" — {c.detail}"
                        lines.append(f"  - FACTUAL MISS: {c.check_name}{detail}")

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

    if factual_evals:
        best_f = max(factual_evals, key=lambda e: e.score)
        worst_f = min(factual_evals, key=lambda e: e.score)
        lines.append(f"- **Best factual score**: {best_f.model_name} on {best_f.codebase_name} ({best_f.score:.0%})")
        lines.append(f"- **Worst factual score**: {worst_f.model_name} on {worst_f.codebase_name} ({worst_f.score:.0%})")

    # Common failures
    failure_counts: dict[str, int] = {}
    for ev in structural_evals:
        for c in ev.checks:
            if not c.passed:
                failure_counts[c.check_name] = failure_counts.get(c.check_name, 0) + 1

    if failure_counts:
        lines.append("\n### Common Structural Failures\n")
        for check_name, count in sorted(failure_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- `{check_name}`: failed {count} time(s)")

    # Common factual misses
    if factual_evals:
        factual_failures: dict[str, int] = {}
        for fev in factual_evals:
            for c in fev.checks:
                if not c.passed:
                    factual_failures[c.check_name] = factual_failures.get(c.check_name, 0) + 1

        if factual_failures:
            lines.append("\n### Common Factual Misses\n")
            for check_name, count in sorted(factual_failures.items(), key=lambda x: -x[1]):
                lines.append(f"- `{check_name}`: missed {count} time(s)")

    lines.append("")
    return "\n".join(lines)
