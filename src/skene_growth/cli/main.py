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
from skene_growth.config import load_config

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
        help="LLM provider to use",
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
    docs: bool = typer.Option(
        False,
        "--docs",
        help="Enable documentation mode (collects product overview and features)",
    ),
):
    """
    Analyze a codebase and generate growth-manifest.json.

    Scans your codebase to detect:
    - Technology stack (framework, language, database, etc.)
    - Growth hubs (features with growth potential)
    - GTM gaps (missing features that could drive growth)

    With --docs flag, also collects:
    - Product overview (tagline, value proposition, target audience)
    - User-facing feature documentation

    Examples:

        # Analyze current directory (uvx)
        uvx skene-growth analyze .

        # Analyze specific path with custom output
        uvx skene-growth analyze ./my-project -o manifest.json

        # With API key
        uvx skene-growth analyze . --api-key "your-key"
    """
    # Load config with fallbacks
    config = load_config()

    # Apply config defaults
    resolved_api_key = api_key or config.api_key
    resolved_provider = provider or config.provider
    resolved_model = model or config.model
    resolved_output = output or Path(config.output_dir) / "growth-manifest.json"

    if not resolved_api_key:
        console.print(
            "[yellow]Warning:[/yellow] No API key provided. "
            "Set --api-key, SKENE_API_KEY env var, or add to .skene-growth.toml"
        )
        console.print("\nTo get an API key, visit: https://aistudio.google.com/apikey")
        raise typer.Exit(1)

    mode_str = "docs" if docs else "growth"
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
            docs,
        )
    )


async def _run_analysis(
    path: Path,
    output: Path,
    api_key: str,
    provider: str,
    model: str,
    verbose: bool,
    docs: bool = False,
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
            if docs:
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
            manifest_data = (
                result.data.get("output", result.data) if "output" in result.data else result.data
            )
            output.write_text(json.dumps(manifest_data, indent=2, default=json_serializer))
            _write_manifest_markdown(manifest_data, output)

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
        _show_analysis_summary(result.data)


def _show_analysis_summary(data: dict):
    """Display a summary of the analysis results."""
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

    console.print(table)


def _write_manifest_markdown(manifest_data: dict, output_path: Path) -> None:
    """Render a markdown summary next to the JSON manifest."""
    from skene_growth.docs import DocsGenerator
    from skene_growth.manifest import DocsManifest, GrowthManifest

    try:
        if (
            manifest_data.get("version") == "2.0"
            or "product_overview" in manifest_data
            or "features" in manifest_data
        ):
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


@app.command()
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
    template: str = typer.Option(
        "default",
        "-t",
        "--template",
        help="Documentation template to use",
    ),
):
    """
    Generate documentation from a growth-manifest.json.

    Creates markdown documentation including:
    - Context document (project overview)
    - Product documentation
    - SEO-optimized pages

    Examples:

        # Generate docs (auto-detect manifest)
        uvx skene-growth generate

        # Specify manifest and output
        uvx skene-growth generate -m ./manifest.json -o ./docs
    """
    # Auto-detect manifest if not provided
    if manifest is None:
        default_paths = [
            Path("./skene-context/growth-manifest.json"),
            Path("./growth-manifest.json"),
            Path("./manifest.json"),
        ]
        for p in default_paths:
            if p.exists():
                manifest = p
                break

        if manifest is None:
            console.print(
                "[red]Error:[/red] No manifest found. "
                "Run 'skene-growth analyze' first or specify --manifest."
            )
            raise typer.Exit(1)

    if not manifest.exists():
        console.print(f"[red]Error:[/red] Manifest not found: {manifest}")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"[bold blue]Generating documentation[/bold blue]\n"
            f"Manifest: {manifest}\n"
            f"Output: {output_dir}\n"
            f"Template: {template}",
            title="skene-growth",
        )
    )

    # Load manifest
    try:
        manifest_data = json.loads(manifest.read_text())
    except Exception as e:
        console.print(f"[red]Error loading manifest:[/red] {e}")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating documentation...", total=None)

        try:
            from skene_growth.docs import DocsGenerator
            from skene_growth.manifest import DocsManifest, GrowthManifest

            # Parse manifest - use DocsManifest for v2.0, GrowthManifest otherwise
            progress.update(task, description="Parsing manifest...")
            if manifest_data.get("version") == "2.0":
                manifest_obj = DocsManifest(**manifest_data)
            else:
                manifest_obj = GrowthManifest(**manifest_data)

            # Generate docs
            progress.update(task, description="Generating context document...")
            generator = DocsGenerator()

            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate context doc
            context_doc = generator.generate_context(manifest_obj)
            context_path = output_dir / "context.md"
            context_path.write_text(context_doc)

            # Generate product docs
            progress.update(task, description="Generating product documentation...")
            product_doc = generator.generate_product_docs(manifest_obj)
            product_path = output_dir / "product-docs.md"
            product_path.write_text(product_doc)

            progress.update(task, description="Complete!")

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print(f"\n[green]Success![/green] Documentation generated in: {output_dir}")

    # List generated files
    table = Table(title="Generated Files")
    table.add_column("File", style="cyan")
    table.add_column("Description", style="white")
    table.add_row("context.md", "Project context document")
    table.add_row("product-docs.md", "Product documentation")
    console.print(table)


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
        console.print(
            "[red]Error:[/red] No manifest found. "
            "Run 'skene-growth analyze' first or specify --manifest."
        )
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


if __name__ == "__main__":
    app()
