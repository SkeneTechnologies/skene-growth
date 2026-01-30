"""
CLI for skene-growth PLG analysis toolkit.

Primary usage (uvx - zero installation):
    uvx skene-growth analyze .
    uvx skene-growth plan

Alternative usage (pip install):
    skene-growth analyze .
    skene-growth plan

Configuration files (optional):
    Project-level: ./.skene-growth.config
    User-level: ~/.config/skene-growth/config
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

    Workflow suggestion:
        analyze -> plan

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
        help="LLM provider to use (openai, gemini, anthropic/claude, ollama)",
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
    exclude: Optional[list[str]] = typer.Option(
        None,
        "--exclude",
        "-e",
        help=(
            "Folder names to exclude from analysis (can be used multiple times). "
            "Can also be set in .skene-growth.config as exclude_folders. "
            "Example: --exclude tests --exclude vendor"
        ),
    ),
):
    """
    Analyze a codebase and generate growth-manifest.json.

    Scans your codebase to detect:
    - Technology stack (framework, language, database, etc.)
    - Current growth features (features with growth potential)
    - Growth opportunities (missing features that could drive growth)

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

    # Handle output path: if it's a directory, append default filename
    if output:
        # Resolve to absolute path
        if output.is_absolute():
            resolved_output = output.resolve()
        else:
            resolved_output = (Path.cwd() / output).resolve()

        # If path exists and is a directory, or has no file extension, append default filename
        if resolved_output.exists() and resolved_output.is_dir():
            # Path exists and is a directory, append default filename
            resolved_output = (resolved_output / "growth-manifest.json").resolve()
        elif not resolved_output.suffix:
            # No file extension provided, treat as directory and append filename
            resolved_output = (resolved_output / "growth-manifest.json").resolve()
        else:
            # Ensure final path is absolute
            resolved_output = resolved_output.resolve()
    else:
        resolved_output = Path(config.output_dir) / "growth-manifest.json"

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
                "Set --api-key, SKENE_API_KEY env var, or add to .skene-growth.config"
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

    # Collect exclude folders from config and CLI
    exclude_folders = list(config.exclude_folders) if config.exclude_folders else []
    if exclude:
        # Merge CLI excludes with config excludes (deduplicate)
        exclude_folders = list(set(exclude_folders + exclude))

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
            exclude_folders=exclude_folders if exclude_folders else None,
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
    exclude_folders: Optional[list[str]] = None,
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
            codebase = CodebaseExplorer(path, exclude_folders=exclude_folders)

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

            # Generate product docs if requested
            if product_docs:
                _write_product_docs(manifest_data, output)

            template_data = await _write_growth_template(llm, manifest_data, business_type, output)

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


async def _write_growth_template(
    llm, manifest_data: dict, business_type: Optional[str] = None, manifest_path: Optional[Path] = None
) -> dict | None:
    """Generate and save the growth template JSON output.

    Args:
        llm: LLM client
        manifest_data: Manifest data
        business_type: Optional business type
        manifest_path: Path to the manifest file (template will be saved to same directory)

    Returns:
        Template data dict if successful, None if failed
    """
    from skene_growth.templates import generate_growth_template, write_growth_template_outputs

    try:
        template_data = await generate_growth_template(llm, manifest_data, business_type)
        # Save template to the same directory as the manifest
        if manifest_path:
            output_dir = manifest_path.parent
        else:
            output_dir = Path("./skene-context")
        json_path, markdown_path = write_growth_template_outputs(template_data, output_dir)
        console.print(f"[green]Growth template saved to:[/green] {json_path}")
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
def plan(
    manifest: Optional[Path] = typer.Option(
        None,
        "--manifest",
        help="Path to growth-manifest.json",
    ),
    template: Optional[Path] = typer.Option(
        None,
        "--template",
        help="Path to growth-template.json",
    ),
    context: Optional[Path] = typer.Option(
        None,
        "--context",
        "-c",
        help="Directory containing growth-manifest.json and growth-template.json (auto-detected if not specified)",
    ),
    output: Path = typer.Option(
        "./skene-context/growth-plan.md",
        "-o",
        "--output",
        help="Output path for growth plan (markdown)",
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
        help="LLM provider to use (openai, gemini, anthropic/claude, ollama)",
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
):
    """
    Generate a growth plan using Council of Growth Engineers.

    Uses manifest and template when present (auto-detected from
    ./skene-context/ or current dir) to generate a growth plan.
    None of these context files are required.

    Examples:

        # Generate growth plan (uses any context files found)
        uvx skene-growth plan --api-key "your-key"

        # Specify context directory containing manifest and template
        uvx skene-growth plan --context ./my-context --api-key "your-key"

        # Override context file paths
        uvx skene-growth plan --manifest ./manifest.json --template ./template.json
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

    # Validate context directory if provided
    if context:
        if not context.exists():
            console.print(f"[red]Error:[/red] Context directory does not exist: {context}")
            raise typer.Exit(1)
        if not context.is_dir():
            console.print(f"[red]Error:[/red] Context path is not a directory: {context}")
            raise typer.Exit(1)

    # Auto-detect manifest
    if manifest is None:
        default_paths = []

        # If context is specified, check there first
        if context:
            default_paths.append(context / "growth-manifest.json")

        # Then check standard default paths
        default_paths.extend(
            [
                Path("./skene-context/growth-manifest.json"),
                Path("./growth-manifest.json"),
            ]
        )

        for p in default_paths:
            if p.exists():
                manifest = p
                break

    # Auto-detect template
    if template is None:
        default_template_paths = []

        # If context is specified, check there first
        if context:
            default_template_paths.append(context / "growth-template.json")

        # Then check standard default paths
        default_template_paths.extend(
            [
                Path("./skene-context/growth-template.json"),
                Path("./growth-template.json"),
            ]
        )

        for p in default_template_paths:
            if p.exists():
                template = p
                break

    # Check API key
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
                "Set --api-key, SKENE_API_KEY env var, or add to .skene-growth.config"
            )
            raise typer.Exit(1)

    # Handle output path: if it's a directory, append default filename
    # Resolve to absolute path
    if output.is_absolute():
        resolved_output = output.resolve()
    else:
        resolved_output = (Path.cwd() / output).resolve()

    # If path exists and is a directory, or has no file extension, append default filename
    if resolved_output.exists() and resolved_output.is_dir():
        # Path exists and is a directory, append default filename
        resolved_output = (resolved_output / "growth-plan.md").resolve()
    elif not resolved_output.suffix:
        # No file extension provided, treat as directory and append filename
        resolved_output = (resolved_output / "growth-plan.md").resolve()

    # Ensure final path is absolute (should already be, but double-check)
    resolved_output = resolved_output.resolve()

    console.print(
        Panel.fit(
            f"[bold blue]Generating growth plan[/bold blue]\n"
            f"Manifest: {manifest if manifest and manifest.exists() else 'Not provided'}\n"
            f"Template: {template if template and template.exists() else 'Not provided'}\n"
            f"Output: {resolved_output}\n"
            f"Provider: {resolved_provider}\n"
            f"Model: {resolved_model}",
            title="skene-growth",
        )
    )

    # Run async cycle generation
    asyncio.run(
        _run_cycle(
            manifest_path=manifest,
            template_path=template,
            output_path=resolved_output,
            api_key=resolved_api_key,
            provider=resolved_provider,
            model=resolved_model,
            verbose=verbose,
        )
    )


def _extract_ceo_next_action(memo_content: str) -> str | None:
    """Extract the CEO's Next Action section from the memo.

    Args:
        memo_content: Full memo markdown content

    Returns:
        Extracted next action text or None if not found
    """
    import re

    # Look for the CEO's Next Action section (flexible patterns)
    # Pattern 1: Match section heading followed by any bold text
    pattern = r"##?\s*7?\.\s*(?:THE\s+)?CEO'?s?\s+Next\s+Action.*?\n\n\*\*(.*?):\*\*\s*(.*?)(?=\n\n###|\n\n##|\Z)"
    match = re.search(pattern, memo_content, re.IGNORECASE | re.DOTALL)

    if match:
        intro = match.group(1).strip()  # e.g., "Within 24 hours", "Ship in 24 Hours"
        action = match.group(2).strip()

        # Combine intro and action for context
        full_action = f"{intro}: {action}" if intro else action

        # Clean up markdown and extra formatting
        full_action = re.sub(r"\[.*?\]", "", full_action)  # Remove markdown links
        full_action = re.sub(r"\n\n+", "\n\n", full_action)  # Normalize line breaks
        return full_action

    # Fallback: Look for any bold text after CEO's Next Action heading
    pattern2 = r"##?\s*7?\.\s*(?:THE\s+)?CEO'?s?\s+Next\s+Action.*?\n\n(.*?)(?=\n\n###|\n\n##|\Z)"
    match2 = re.search(pattern2, memo_content, re.IGNORECASE | re.DOTALL)

    if match2:
        action = match2.group(1).strip()
        action = re.sub(r"\[.*?\]", "", action)
        action = re.sub(r"\n\n+", "\n\n", action)
        # Remove the bold markers if present
        action = re.sub(r"\*\*", "", action)
        return action

    return None


async def _run_cycle(
    manifest_path: Path | None,
    template_path: Path | None,
    output_path: Path,
    api_key: str,
    provider: str,
    model: str,
    verbose: bool,
):
    """Run cycle generation using Council of Growth Engineers."""
    from pydantic import SecretStr

    from skene_growth.llm import create_llm_client

    next_action = None

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

            # Generate Council memo
            progress.update(task, description="Generating Council memo...")
            from skene_growth.planner import Planner

            planner = Planner()
            memo_content = await planner.generate_council_memo(
                llm=llm,
                manifest_data=manifest_data,
                template_data=template_data,
            )

            # Write output
            progress.update(task, description="Writing output...")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(memo_content)

            progress.update(task, description="Complete!")

            # Extract and display CEO's Next Action
            next_action = _extract_ceo_next_action(memo_content)

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            if verbose:
                import traceback

                console.print(traceback.format_exc())
            raise typer.Exit(1)

    console.print(f"\n[green]Success![/green] Growth plan saved to: {output_path}")

    # Display next action box
    if next_action:
        console.print("\n")
        console.print(
            Panel(
                next_action,
                title="[bold yellow]⚡ Next Action - Ship in 24 Hours[/bold yellow]",
                border_style="yellow",
                padding=(1, 2),
            )
        )


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
        table.add_row("Current Growth Features", str(len(manifest_obj.current_growth_features)))
        table.add_row("New Growth Opportunities", str(len(manifest_obj.growth_opportunities)))

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
    1. User config: ~/.config/skene-growth/config
    2. Project config: ./.skene-growth.config
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
        config_path = Path(".skene-growth.config")
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
        str(project_cfg) if project_cfg else "./.skene-growth.config",
        "[green]Found[/green]" if project_cfg else "[dim]Not found[/dim]",
    )
    table.add_row(
        "User",
        str(user_cfg) if user_cfg else "~/.config/skene-growth/config",
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
