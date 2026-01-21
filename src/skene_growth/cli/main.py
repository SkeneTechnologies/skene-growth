"""
CLI for skene-growth PLG analysis toolkit.

Primary usage (uvx - zero installation):
    uvx skene-growth analyze .
    uvx skene-growth generate
    uvx skene-growth inject --csv loops.csv

Alternative usage (pip install):
    skene-growth analyze .
    skene-growth generate
    skene-growth inject --csv loops.csv

Configuration files (optional):
    Project-level: ./.skene-growth.toml
    User-level: ~/.config/skene-growth/config.toml
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import typer
from pydantic import SecretStr
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from skene_growth import __version__
from skene_growth.config import default_model_for_provider, load_config

app = typer.Typer(
    name="skene-growth",
    help="PLG analysis toolkit for codebases. Analyze code, detect growth opportunities.",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()


def json_serializer(obj: Any) -> str:
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"[bold]skene-growth[/bold] version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    """
    skene-growth - PLG analysis toolkit for codebases.

    Analyze your codebase, detect growth opportunities, and generate documentation.

    Quick start with uvx (no installation required):

        uvx skene-growth analyze .

    Or install with pip:

        pip install skene-growth
        skene-growth analyze .
    """
    pass


@app.command()
def analyze(
    path: Path = typer.Argument(
        ".",
        help="Path to codebase to analyze",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "-o",
        "--output",
        help="Output path for growth-manifest.json",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="SKENE_API_KEY",
        help="API key for LLM provider (or set SKENE_API_KEY env var)",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="LLM provider to use (openai, gemini, anthropic, ollama)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="LLM model name (e.g., gemini-2.0-flash)",
    ),
    verbose: bool = typer.Option(
        False,
        "-v",
        "--verbose",
        help="Enable verbose output",
    ),
    business_type: Optional[str] = typer.Option(
        None,
        "--business-type",
        "-b",
        help="Business type for growth template (e.g., 'design-agency', 'b2b-saas'). LLM will infer if not provided.",
    ),
    product_docs: bool = typer.Option(
        False,
        "--product-docs",
        help="Generate product-docs.md with user-facing feature documentation",
    ),
):
    """
    Analyze a codebase and generate growth-manifest.json.

    Scans your codebase to detect:
    - Technology stack (framework, language, database, etc.)
    - Growth hubs (features with growth potential)
    - GTM gaps (missing features that could drive growth)

    With --product-docs flag:
    - Collects product overview (tagline, value proposition, target audience)
    - Collects user-facing feature documentation from codebase
    - Generates product-docs.md: User-friendly documentation of features and roadmap

    Examples:

        # Analyze current directory (uvx)
        uvx skene-growth analyze .

        # Analyze specific path with custom output
        uvx skene-growth analyze ./my-project -o manifest.json

        # With API key
        uvx skene-growth analyze . --api-key "your-key"

        # Specify business type for custom growth template
        uvx skene-growth analyze . --business-type "design-agency"

        # Generate product documentation
        uvx skene-growth analyze . --product-docs
    """
    # Load config with fallbacks
    config = load_config()

    # Apply config defaults
    resolved_api_key = api_key or config.api_key
    resolved_provider = provider or config.provider
    if model:
        resolved_model = model
    else:
        resolved_model = config.get("model") or default_model_for_provider(resolved_provider)
    resolved_output = output or Path(config.output_dir) / "growth-manifest.json"

    # LM Studio and Ollama don't require an API key (local servers)
    is_local_provider = resolved_provider.lower() in (
        "lmstudio",
        "lm-studio",
        "lm_studio",
        "ollama",
    )

    if not resolved_api_key:
        if is_local_provider:
            resolved_api_key = resolved_provider  # Dummy key for local server
        else:
            console.print(
                "[yellow]Warning:[/yellow] No API key provided. "
                "Set --api-key, SKENE_API_KEY env var, or add to .skene-growth.toml"
            )
            console.print("\nTo get an API key, visit: https://aistudio.google.com/apikey")
            raise typer.Exit(1)

    # If product docs are requested, use docs mode to collect features
    mode_str = "docs" if product_docs else "growth"
    console.print(
        Panel.fit(
            f"[bold blue]Analyzing codebase[/bold blue]\n"
            f"Path: {path}\n"
            f"Provider: {resolved_provider}\n"
            f"Model: {resolved_model}\n"
            f"Mode: {mode_str}",
            title="skene-growth",
        )
    )

    # Run async analysis
    asyncio.run(
        _run_analysis(
            path,
            resolved_output,
            resolved_api_key,
            resolved_provider,
            resolved_model,
            verbose,
            product_docs,
            business_type,
        )
    )


async def _run_analysis(
    path: Path,
    output: Path,
    api_key: str,
    provider: str,
    model: str,
    verbose: bool,
    product_docs: Optional[bool] = False,
    business_type: Optional[str] = None,
):
    """Run the async analysis."""
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
            codebase = CodebaseExplorer(path)

            progress.update(task, description="Connecting to LLM provider...")
            llm = create_llm_client(provider, SecretStr(api_key), model)

            # Create analyzer
            progress.update(task, description="Creating analyzer...")
            if product_docs:
                analyzer = DocsAnalyzer()
                request_msg = "Generate documentation for this project"
            else:
                analyzer = ManifestAnalyzer()
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
                raise typer.Exit(1)

            # Save output - unwrap "output" key if present
            progress.update(task, description="Saving manifest...")
            output.parent.mkdir(parents=True, exist_ok=True)
            manifest_data = result.data.get("output", result.data) if "output" in result.data else result.data
            output.write_text(json.dumps(manifest_data, indent=2, default=json_serializer))
            _write_manifest_markdown(manifest_data, output)

            # Generate product docs if requested
            if product_docs:
                _write_product_docs(manifest_data, output)

            template_data = await _write_growth_template(llm, manifest_data, business_type)

            progress.update(task, description="Complete!")

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            if verbose:
                import traceback

                console.print(traceback.format_exc())
            raise typer.Exit(1)

    # Show summary
    console.print(f"\n[green]Success![/green] Manifest saved to: {output}")

    # Show quick stats if available
    if result.data:
        _show_analysis_summary(result.data, template_data)


def _show_analysis_summary(data: dict, template_data: dict | None = None):
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

    if "growth_hubs" in data:
        hubs = data["growth_hubs"]
        table.add_row("Growth Hubs", f"{len(hubs)} features detected")

    if "gtm_gaps" in data:
        gaps = data["gtm_gaps"]
        table.add_row("GTM Gaps", f"{len(gaps)} opportunities identified")

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


def _write_manifest_markdown(manifest_data: dict, output_path: Path) -> None:
    """Render a markdown summary next to the JSON manifest."""
    from skene_growth.docs import DocsGenerator
    from skene_growth.manifest import DocsManifest, GrowthManifest

    try:
        if manifest_data.get("version") == "2.0" or "product_overview" in manifest_data or "features" in manifest_data:
            manifest = DocsManifest.model_validate(manifest_data)
        else:
            manifest = GrowthManifest.model_validate(manifest_data)
    except Exception as exc:
        console.print(f"[yellow]Warning:[/yellow] Failed to parse manifest: {exc}")
        return

    markdown_path = output_path.with_suffix(".md")
    try:
        generator = DocsGenerator()
        markdown_content = generator.generate_analysis(manifest)
        markdown_path.write_text(markdown_content)
        console.print(f"[green]Markdown saved to:[/green] {markdown_path}")
    except Exception as exc:
        console.print(f"[yellow]Warning:[/yellow] Failed to generate markdown: {exc}")


def _write_product_docs(manifest_data: dict, manifest_path: Path) -> None:
    """Generate and save product documentation alongside analysis output.

    Args:
        manifest_data: The manifest data dict
        manifest_path: Path to the growth-manifest.json (used to determine output location)
    """
    from skene_growth.docs import DocsGenerator
    from skene_growth.manifest import DocsManifest, GrowthManifest

    try:
        # Parse manifest (DocsManifest for v2.0, GrowthManifest otherwise)
        if manifest_data.get("version") == "2.0" or "product_overview" in manifest_data or "features" in manifest_data:
            manifest = DocsManifest.model_validate(manifest_data)
        else:
            manifest = GrowthManifest.model_validate(manifest_data)
    except Exception as exc:
        console.print(f"[yellow]Warning:[/yellow] Failed to parse manifest for product docs: {exc}")
        return

    # Write to same directory as manifest (./skene-context/)
    output_dir = manifest_path.parent
    product_docs_path = output_dir / "product-docs.md"

    try:
        generator = DocsGenerator()
        product_content = generator.generate_product_docs(manifest)
        product_docs_path.write_text(product_content)
        console.print(f"[green]Product docs saved to:[/green] {product_docs_path}")
    except Exception as exc:
        console.print(f"[yellow]Warning:[/yellow] Failed to generate product docs: {exc}")


async def _write_growth_template(llm, manifest_data: dict, business_type: Optional[str] = None) -> dict | None:
    """Generate and save the growth template JSON and Markdown outputs.

    Returns:
        Template data dict if successful, None if failed
    """
    from skene_growth.templates import generate_growth_template, write_growth_template_outputs

    try:
        template_data = await generate_growth_template(llm, manifest_data, business_type)
        output_dir = Path("./skene-context")
        json_path, markdown_path = write_growth_template_outputs(template_data, output_dir)
        console.print(f"[green]Growth template saved to:[/green] {json_path}")
        console.print(f"[green]Growth template markdown saved to:[/green] {markdown_path}")
        return template_data
    except Exception as exc:
        console.print(f"[yellow]Warning:[/yellow] Failed to generate growth template: {exc}")
        return None


@app.command(deprecated=True, hidden=True)
def generate(
    manifest: Optional[Path] = typer.Option(
        None,
        "-m",
        "--manifest",
        help="Path to growth-manifest.json (auto-detected if not specified)",
    ),
    output_dir: Path = typer.Option(
        "./skene-docs",
        "-o",
        "--output",
        help="Output directory for generated documentation",
    ),
):
    """
    [DEPRECATED] Use 'analyze --product-docs' instead.

    This command has been consolidated into the analyze command.
    """
    console.print(
        "[yellow]Warning:[/yellow] The 'generate' command is deprecated.\n"
        "Use 'skene-growth analyze --product-docs' instead.\n"
        "This command will be removed in v0.2.0."
    )
    raise typer.Exit(1)


@app.command()
def inject(
    csv: Optional[Path] = typer.Option(
        None,
        "--csv",
        help="Path to growth loops CSV file",
    ),
    manifest: Optional[Path] = typer.Option(
        None,
        "-m",
        "--manifest",
        help="Path to growth-manifest.json",
    ),
    output: Path = typer.Option(
        "./skene-injection-plan.json",
        "-o",
        "--output",
        help="Output path for injection plan",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--execute",
        help="Generate plan only (dry-run) or execute changes",
    ),
):
    """
    Map growth loops to codebase and generate an injection plan.

    Analyzes the codebase to find optimal locations for implementing
    growth loops like referrals, sharing, onboarding, etc.

    Examples:

        # Generate injection plan with built-in loops
        uvx skene-growth inject

        # Use custom loops from CSV
        uvx skene-growth inject --csv loops.csv

        # Specify manifest
        uvx skene-growth inject -m ./manifest.json
    """
    # Auto-detect manifest
    if manifest is None:
        default_paths = [
            Path("./skene-context/growth-manifest.json"),
            Path("./growth-manifest.json"),
        ]
        for p in default_paths:
            if p.exists():
                manifest = p
                break

    if manifest is None or not manifest.exists():
        console.print("[red]Error:[/red] No manifest found. Run 'skene-growth analyze' first or specify --manifest.")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"[bold blue]Generating injection plan[/bold blue]\n"
            f"Manifest: {manifest}\n"
            f"Loops CSV: {csv or 'Using built-in catalog'}\n"
            f"Mode: {'Dry run' if dry_run else 'Execute'}",
            title="skene-growth",
        )
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating injection plan...", total=None)

        try:
            from skene_growth.injector import GrowthLoopCatalog, InjectionPlanner
            from skene_growth.manifest import GrowthManifest

            # Load manifest
            progress.update(task, description="Loading manifest...")
            manifest_data = json.loads(manifest.read_text())
            manifest_obj = GrowthManifest(**manifest_data)

            # Load or create catalog
            progress.update(task, description="Loading growth loops...")
            catalog = GrowthLoopCatalog()

            if csv and csv.exists():
                catalog.load_from_csv(str(csv))
                console.print(f"Loaded loops from: {csv}")

            # Generate plan
            progress.update(task, description="Mapping loops to codebase...")
            planner = InjectionPlanner()
            plan = planner.generate_quick_plan(manifest_obj, catalog)

            # Save plan
            progress.update(task, description="Saving injection plan...")
            output.parent.mkdir(parents=True, exist_ok=True)
            planner.save_plan(plan, output)

            progress.update(task, description="Complete!")

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print(f"\n[green]Success![/green] Injection plan saved to: {output}")

    # Show summary
    if plan.loop_plans:
        table = Table(title="Injection Plan Summary")
        table.add_column("Loop", style="cyan")
        table.add_column("Priority", style="yellow")
        table.add_column("Changes", style="white")

        for lp in plan.loop_plans[:5]:
            table.add_row(
                lp.loop_name,
                str(lp.priority),
                str(len(lp.code_changes)),
            )

        if len(plan.loop_plans) > 5:
            table.add_row("...", "...", f"+{len(plan.loop_plans) - 5} more")

        console.print(table)


@app.command()
def objectives(
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="SKENE_API_KEY",
        help="API key for LLM provider (or set SKENE_API_KEY env var)",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="LLM provider to use (openai, gemini, anthropic, ollama)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="LLM model name (e.g., gemini-2.0-flash)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "-o",
        "--output",
        help="Output path for growth-objectives.md",
    ),
    quarter: Optional[str] = typer.Option(
        None,
        "-q",
        "--quarter",
        help="Quarter label (e.g., 'Q1', 'Q2 2024')",
    ),
    manifest: Optional[Path] = typer.Option(
        None,
        "--manifest",
        help="Path to growth-manifest.json (auto-detected if not specified)",
    ),
    template: Optional[Path] = typer.Option(
        None,
        "--template",
        help="Path to growth-template.json (auto-detected if not specified)",
    ),
    verbose: bool = typer.Option(
        False,
        "-v",
        "--verbose",
        help="Enable verbose output",
    ),
    guidance: Optional[str] = typer.Option(
        None,
        "-g",
        "--guidance",
        help="Guidance text to influence objective selection (e.g., 'Focus on onboarding' or 'Prioritize retention "
        "metrics')",
    ),
):
    """
    Generate 3 prioritized growth objectives from manifest and template.

    Reads existing growth-manifest.json and growth-template.json files,
    then uses an LLM to generate 3 targeted growth objectives based on
    lifecycle stages and identified gaps.

    Examples:

        # Generate objectives (auto-detect manifest and template)
        uvx skene-growth objectives

        # Specify quarter label
        uvx skene-growth objectives --quarter "Q1 2024"

        # With guidance to focus on specific areas
        uvx skene-growth objectives --guidance "I want all objectives to focus on onboarding"

        # With specific files
        uvx skene-growth objectives --manifest ./my-manifest.json --template ./my-template.json

        # With API key
        uvx skene-growth objectives --api-key "your-key"
    """
    # Load config with fallbacks
    config = load_config()

    # Apply config defaults
    resolved_api_key = api_key or config.api_key
    resolved_provider = provider or config.provider
    if model:
        resolved_model = model
    else:
        resolved_model = config.get("model") or default_model_for_provider(resolved_provider)
    resolved_output = output or Path(config.output_dir) / "growth-objectives.md"

    # Auto-detect manifest
    if manifest is None:
        default_manifest_paths = [
            Path("./skene-context/growth-manifest.json"),
            Path("./growth-manifest.json"),
        ]
        for p in default_manifest_paths:
            if p.exists():
                manifest = p
                break

    if manifest is None or not manifest.exists():
        console.print("[red]Error:[/red] No manifest found. Run 'skene-growth analyze' first or specify --manifest.")
        raise typer.Exit(1)

    # Auto-detect template
    if template is None:
        default_template_paths = [
            Path("./skene-context/growth-template.json"),
            Path("./growth-template.json"),
        ]
        for p in default_template_paths:
            if p.exists():
                template = p
                break

    if template is None or not template.exists():
        console.print("[red]Error:[/red] No template found. Run 'skene-growth analyze' first or specify --template.")
        raise typer.Exit(1)

    # LM Studio and Ollama don't require an API key (local servers)
    is_local_provider = resolved_provider.lower() in (
        "lmstudio",
        "lm-studio",
        "lm_studio",
        "ollama",
    )

    if not resolved_api_key:
        if is_local_provider:
            resolved_api_key = resolved_provider  # Dummy key for local server
        else:
            console.print(
                "[yellow]Warning:[/yellow] No API key provided. "
                "Set --api-key, SKENE_API_KEY env var, or add to .skene-growth.toml"
            )
            console.print("\nTo get an API key, visit: https://aistudio.google.com/apikey")
            raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"[bold blue]Generating growth objectives[/bold blue]\n"
            f"Manifest: {manifest}\n"
            f"Template: {template}\n"
            f"Provider: {resolved_provider}\n"
            f"Model: {resolved_model}\n"
            f"Quarter: {quarter or 'Not specified'}\n"
            f"Guidance: {guidance or 'Not specified'}",
            title="skene-growth",
        )
    )

    # Run async objectives generation
    asyncio.run(
        _run_objectives(
            manifest,
            template,
            resolved_output,
            resolved_api_key,
            resolved_provider,
            resolved_model,
            quarter,
            guidance,
            verbose,
        )
    )


async def _run_objectives(
    manifest_path: Path,
    template_path: Path,
    output: Path,
    api_key: str,
    provider: str,
    model: str,
    quarter: Optional[str],
    guidance: Optional[str],
    verbose: bool,
):
    """Run the async objectives generation."""
    from skene_growth.llm import create_llm_client
    from skene_growth.objectives import generate_objectives, write_objectives_output

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing...", total=None)

        try:
            # Load manifest and template
            progress.update(task, description="Loading manifest...")
            manifest_data = json.loads(manifest_path.read_text())

            progress.update(task, description="Loading template...")
            template_data = json.loads(template_path.read_text())

            # Connect to LLM
            progress.update(task, description="Connecting to LLM provider...")
            llm = create_llm_client(provider, SecretStr(api_key), model)

            # Generate objectives
            progress.update(task, description="Generating growth objectives...")
            markdown_content = await generate_objectives(
                llm=llm,
                manifest_data=manifest_data,
                template_data=template_data,
                quarter=quarter,
                guidance=guidance,
            )

            # Write output
            progress.update(task, description="Saving objectives...")
            write_objectives_output(markdown_content, output)

            progress.update(task, description="Complete!")

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            if verbose:
                import traceback

                console.print(traceback.format_exc())
            raise typer.Exit(1)

    console.print(f"\n[green]Success![/green] Objectives saved to: {output}")

    # Show preview
    _show_objectives_preview(markdown_content)


def _show_objectives_preview(markdown_content: str):
    """Display a preview of the generated objectives."""
    table = Table(title="Growth Objectives Preview")
    table.add_column("Lifecycle", style="cyan")
    table.add_column("Metric", style="white")
    table.add_column("Target", style="green")

    # Parse the markdown to extract objectives
    lines = markdown_content.split("\n")
    current_lifecycle = None

    for line in lines:
        if line.startswith("## "):
            current_lifecycle = line[3:].strip()
        elif line.startswith("- **Metric:**"):
            metric = line.replace("- **Metric:**", "").strip()
        elif line.startswith("- **Target:**"):
            target = line.replace("- **Target:**", "").strip()
            if current_lifecycle:
                table.add_row(current_lifecycle, metric, target)

    console.print(table)


@app.command()
def validate(
    manifest: Path = typer.Argument(
        ...,
        help="Path to growth-manifest.json to validate",
        exists=True,
    ),
):
    """
    Validate a growth-manifest.json against the schema.

    Checks that the manifest file is valid JSON and conforms
    to the GrowthManifest schema.

    Examples:

        uvx skene-growth validate ./growth-manifest.json
    """
    console.print(f"Validating: {manifest}")

    try:
        # Load JSON
        data = json.loads(manifest.read_text())

        # Validate against schema
        from skene_growth.manifest import GrowthManifest

        manifest_obj = GrowthManifest(**data)

        console.print("[green]Valid![/green] Manifest conforms to schema.")

        # Show summary
        table = Table(title="Manifest Summary")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Project", manifest_obj.project_name)
        table.add_row("Version", manifest_obj.version)
        table.add_row("Tech Stack", manifest_obj.tech_stack.language or "Unknown")
        table.add_row("Growth Hubs", str(len(manifest_obj.growth_hubs)))
        table.add_row("GTM Gaps", str(len(manifest_obj.gtm_gaps)))

        console.print(table)

    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Validation failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def config(
    init: bool = typer.Option(
        False,
        "--init",
        help="Create a sample config file in current directory",
    ),
    show: bool = typer.Option(
        False,
        "--show",
        help="Show current configuration values",
    ),
):
    """
    Manage skene-growth configuration.

    Configuration files are loaded in this order (later overrides earlier):
    1. User config: ~/.config/skene-growth/config.toml
    2. Project config: ./.skene-growth.toml
    3. Environment variables (SKENE_API_KEY, SKENE_PROVIDER)
    4. CLI arguments

    Examples:

        # Show current configuration
        uvx skene-growth config --show

        # Create a sample config file
        uvx skene-growth config --init
    """
    from skene_growth.config import find_project_config, find_user_config, load_config

    if init:
        config_path = Path(".skene-growth.toml")
        if config_path.exists():
            console.print(f"[yellow]Config already exists:[/yellow] {config_path}")
            raise typer.Exit(1)

        sample_config = """# skene-growth configuration
# See: https://github.com/skene-technologies/skene-growth

# API key for LLM provider (can also use SKENE_API_KEY env var)
# api_key = "your-gemini-api-key"

# LLM provider to use (default: gemini)
provider = "gemini"

# Default output directory
output_dir = "./skene-context"

# Enable verbose output
verbose = false
"""
        config_path.write_text(sample_config)
        console.print(f"[green]Created config file:[/green] {config_path}")
        console.print("\nEdit this file to add your API key and customize settings.")
        return

    # Default: show configuration
    cfg = load_config()
    project_cfg = find_project_config()
    user_cfg = find_user_config()

    console.print(Panel.fit("[bold blue]Configuration[/bold blue]", title="skene-growth"))

    table = Table(title="Config Files")
    table.add_column("Type", style="cyan")
    table.add_column("Path", style="white")
    table.add_column("Status", style="green")

    table.add_row(
        "Project",
        str(project_cfg) if project_cfg else "./.skene-growth.toml",
        "[green]Found[/green]" if project_cfg else "[dim]Not found[/dim]",
    )
    table.add_row(
        "User",
        str(user_cfg) if user_cfg else "~/.config/skene-growth/config.toml",
        "[green]Found[/green]" if user_cfg else "[dim]Not found[/dim]",
    )
    console.print(table)

    console.print()

    values_table = Table(title="Current Values")
    values_table.add_column("Setting", style="cyan")
    values_table.add_column("Value", style="white")
    values_table.add_column("Source", style="dim")

    # Show API key (masked)
    api_key = cfg.api_key
    if api_key:
        masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        values_table.add_row("api_key", masked, "config/env")
    else:
        values_table.add_row("api_key", "[dim]Not set[/dim]", "-")

    values_table.add_row("provider", cfg.provider, "config/default")
    values_table.add_row("output_dir", cfg.output_dir, "config/default")
    values_table.add_row("verbose", str(cfg.verbose), "config/default")

    console.print(values_table)

    if not project_cfg and not user_cfg:
        console.print("\n[dim]Tip: Run 'skene-growth config --init' to create a config file[/dim]")


@app.command()
def daily_logs(
    skene_context: Optional[Path] = typer.Option(
        None,
        "-c",
        "--context",
        help="Path to skene-context directory (default: ./skene-context)",
    ),
):
    """
    Fetch data from sources defined in skene.json and store in daily logs.

    This command:
    1. Reads skene.json from skene-context directory
    2. Reads growth-objectives file
    3. Fetches data from configured sources for each objective
    4. Stores results in skene-context/daily_logs/daily_logs_YYYY_MM_DD.json

    If files are not found or sources are missing, you'll be prompted to provide
    the necessary information interactively.

    Examples:

        # Use default skene-context directory
        uvx skene-growth daily-logs

        # Specify custom skene-context path
        uvx skene-growth daily-logs --context ./my-context
    """
    from skene_growth.logs import fetch_daily_logs

    try:
        context_path = skene_context or Path("./skene-context")
        log_file_path = fetch_daily_logs(context_path)

        if log_file_path:
            console.print(f"\n[green]✓[/green] Daily logs successfully created: {log_file_path}")
        else:
            console.print("[yellow]No data was fetched[/yellow]")

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
