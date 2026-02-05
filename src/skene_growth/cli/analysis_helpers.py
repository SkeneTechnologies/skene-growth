"""Analysis execution and summary utilities."""

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


async def _show_progress_indicator(stop_event: asyncio.Event) -> None:
    """Show progress indicator with filled boxes every second."""
    count = 0
    while not stop_event.is_set():
        count += 1
        # Print filled box (█) every second
        console.print("[cyan]█[/cyan]", end="")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=1.0)
            break
        except asyncio.TimeoutError:
            continue
    # Print newline when done
    if count > 0:
        console.print()


def json_serializer(obj: Any) -> str:
    """JSON serializer for objects not serializable by default."""
    from datetime import datetime

    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


async def run_analysis(
    path: Path,
    output: Path,
    api_key: str,
    provider: str,
    model: str,
    verbose: bool,
    product_docs: Optional[bool] = False,
    business_type: Optional[str] = None,
    exclude_folders: Optional[list[str]] = None,
    base_url: Optional[str] = None,
):
    """Run the async analysis."""
    from pydantic import SecretStr

    from skene_growth.analyzers import DocsAnalyzer, ManifestAnalyzer
    from skene_growth.codebase import CodebaseExplorer
    from skene_growth.llm import create_llm_client

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing...", total=None)

        try:
            # Initialize components
            progress.update(task, description="Setting up codebase explorer...")
            codebase = CodebaseExplorer(path, exclude_folders=exclude_folders)

            progress.update(task, description="Connecting to LLM provider...")
            llm = create_llm_client(provider, SecretStr(api_key), model)

            # Load existing growth loops from output directory
            progress.update(task, description="Loading existing growth loops...")
            from skene_growth.growth_loops.storage import load_existing_growth_loops

            # Determine base directory for loading existing loops
            base_dir = output.parent if output.parent.name == "skene-context" else output.parent
            existing_loops = load_existing_growth_loops(base_dir)

            if existing_loops:
                progress.update(task, description=f"Found {len(existing_loops)} existing growth loop(s)...")

            # Create analyzer
            progress.update(task, description="Creating analyzer...")
            if product_docs:
                analyzer = DocsAnalyzer(existing_growth_loops=existing_loops)
                request_msg = "Generate documentation for this project"
            else:
                analyzer = ManifestAnalyzer(existing_growth_loops=existing_loops)
                request_msg = "Analyze this codebase for growth opportunities"

            # Define progress callback
            def on_progress(message: str, pct: float):
                progress.update(task, description=f"{message}")

            # Run analysis
            progress.update(task, description="Analyzing codebase...")
            result = await analyzer.run(
                codebase=codebase,
                llm=llm,
                request=request_msg,
                on_progress=on_progress,
            )

            if not result.success:
                console.print("[red]Analysis failed[/red]")
                if verbose and result.data:
                    console.print(json.dumps(result.data, indent=2, default=json_serializer))
                return None, None

            # Save output - unwrap "output" key if present
            progress.update(task, description="Saving manifest...")
            output.parent.mkdir(parents=True, exist_ok=True)
            manifest_data = result.data.get("output", result.data) if "output" in result.data else result.data
            output.write_text(json.dumps(manifest_data, indent=2, default=json_serializer))

            progress.update(task, description="Complete!")

            return result, manifest_data

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            if verbose:
                import traceback

                console.print(traceback.format_exc())
            return None, None


def show_analysis_summary(data: dict, template_data: dict | None = None):
    """Display a summary of the analysis results.

    Args:
        data: Manifest data
        template_data: Growth template data (optional)
    """
    # Unwrap "output" key if present (from GenerateStep)
    if "output" in data and isinstance(data["output"], dict):
        data = data["output"]

    table = Table(title="Analysis Summary")
    table.add_column("Category", style="cyan")
    table.add_column("Details", style="white")

    if "tech_stack" in data:
        tech = data["tech_stack"]
        tech_items = [f"{k}: {v}" for k, v in tech.items() if v]
        table.add_row("Tech Stack", "\n".join(tech_items[:5]) or "Not detected")

    if "industry" in data and data["industry"]:
        industry = data["industry"]
        primary = industry.get("primary") or "Unknown"
        secondary = industry.get("secondary", [])
        confidence = industry.get("confidence")
        industry_str = primary
        if secondary:
            industry_str += f" ({', '.join(secondary[:3])})"
        if confidence is not None:
            industry_str += f" — {int(confidence * 100)}% confidence"
        table.add_row("Industry", industry_str)

    features = data.get("current_growth_features")
    if features:
        table.add_row("Current Growth Features", f"{len(features)} features detected")

    opportunities = data.get("growth_opportunities")
    if opportunities:
        table.add_row("Growth Opportunities", f"{len(opportunities)} opportunities identified")

    if "revenue_leakage" in data:
        leakage = data["revenue_leakage"]
        high_impact = sum(1 for item in leakage if item.get("impact") == "high")
        table.add_row(
            "Revenue Leakage",
            f"{len(leakage)} issues found ({high_impact} high impact)" if leakage else "None detected",
        )
    # Add growth template summary
    if template_data:
        if "lifecycles" in template_data:
            # New format with lifecycles
            lifecycle_count = len(template_data["lifecycles"])
            lifecycle_names = [lc["name"] for lc in template_data["lifecycles"][:3]]
            lifecycle_summary = ", ".join(lifecycle_names)
            if lifecycle_count > 3:
                lifecycle_summary += f", +{lifecycle_count - 3} more"
            table.add_row("Lifecycle Stages", f"{lifecycle_count} stages: {lifecycle_summary}")
        elif "visuals" in template_data and "lifecycleVisuals" in template_data["visuals"]:
            # Legacy format with visuals
            lifecycle_count = len(template_data["visuals"]["lifecycleVisuals"])
            lifecycle_names = list(template_data["visuals"]["lifecycleVisuals"].keys())[:3]
            lifecycle_summary = ", ".join(lifecycle_names)
            if lifecycle_count > 3:
                lifecycle_summary += f", +{lifecycle_count - 3} more"
            table.add_row("Lifecycle Stages", f"{lifecycle_count} stages: {lifecycle_summary}")

    console.print(table)


async def run_cycle(
    manifest_path: Path | None,
    template_path: Path | None,
    output_path: Path,
    api_key: str,
    provider: str,
    model: str,
    verbose: bool,
    onboarding: bool = False,
):
    """Run cycle generation using Council of Growth Engineers."""
    from pydantic import SecretStr

    from skene_growth.cli.prompt_builder import extract_ceo_next_action
    from skene_growth.llm import create_llm_client

    next_action = None
    memo_content = None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing...", total=None)

        try:
            # Load manifest (use empty dict if missing)
            progress.update(task, description="Loading manifest...")
            if manifest_path and manifest_path.exists():
                manifest_data = json.loads(manifest_path.read_text())
            else:
                manifest_data = {"project_name": "Project", "description": "No manifest provided."}

            # Load template (use empty dict if missing)
            progress.update(task, description="Loading template...")
            if template_path and template_path.exists():
                template_data = json.loads(template_path.read_text())
            else:
                template_data = {"lifecycles": []}

            # Connect to LLM
            progress.update(task, description="Connecting to LLM provider...")
            llm = create_llm_client(provider, SecretStr(api_key), model)

            # Generate memo
            memo_type = "onboarding memo" if onboarding else "Council memo"
            progress.update(task, description=f"Generating {memo_type}...")
            from skene_growth.planner import Planner

            planner = Planner()

            # Start progress indicator for generation
            stop_event = asyncio.Event()
            progress_task = None

            try:
                progress_task = asyncio.create_task(_show_progress_indicator(stop_event))

                if onboarding:
                    memo_content = await planner.generate_onboarding_memo(
                        llm=llm,
                        manifest_data=manifest_data,
                        template_data=template_data,
                    )
                else:
                    memo_content = await planner.generate_council_memo(
                        llm=llm,
                        manifest_data=manifest_data,
                        template_data=template_data,
                    )
            finally:
                # Stop progress indicator
                if progress_task is not None:
                    stop_event.set()
                    try:
                        await progress_task
                    except Exception:
                        pass

            # Write output
            progress.update(task, description="Writing output...")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(memo_content)

            progress.update(task, description="Complete!")

            # Extract and display CEO's Next Action
            next_action = extract_ceo_next_action(memo_content)

            return memo_content, next_action

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            if verbose:
                import traceback

                console.print(traceback.format_exc())
            return None, None
