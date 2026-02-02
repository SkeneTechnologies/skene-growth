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
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import typer
from pydantic import SecretStr
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
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


def _generate_sample_growth_analysis():
    """
    Generate a sample growth analysis in the style of growth-plan.md.
    This demonstrates the kind of insights available with API key configuration.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    report = f"""

╔═════════════════════════════════════════════════════════════════════════════╗
║                                                                             ║
║   ██████╗ ██████╗  ██████╗ ██╗    ██╗████████╗██╗  ██╗                      ║
║  ██╔════╝ ██╔══██╗██╔═══██╗██║    ██║╚══██╔══╝██║  ██║                      ║
║  ██║  ███╗██████╔╝██║   ██║██║ █╗ ██║   ██║   ███████║                      ║
║  ██║   ██║██╔══██╗██║   ██║██║███╗██║   ██║   ██╔══██║                      ║
║  ╚██████╔╝██║  ██║╚██████╔╝╚███╔███╔╝   ██║   ██║  ██║                      ║
║   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝    ╚═╝   ╚═╝  ╚═╝                      ║
║                                                                             ║
║      ██████╗ ███████╗██████╗  ██████╗ ██████╗ ████████╗                     ║
║      ██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝                     ║
║      ██████╔╝█████╗  ██████╔╝██║   ██║██████╔╝   ██║                        ║
║      ██╔══██╗██╔══╝  ██╔═══╝ ██║   ██║██╔══██╗   ██║                        ║
║      ██║  ██║███████╗██║     ╚██████╔╝██║  ██║   ██║                        ║
║      ╚═╝  ╚═╝╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝                        ║
║                                                                             ║
║                           ▼ SAMPLE PREVIEW ▼                                ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝

**CONFIDENTIAL ENGINEERING MEMO**
**TO:** Engineering & Product Leadership
**FROM:** Skene Growth Intelligence
**DATE:** {timestamp}
**SUBJECT:** Unlock Full AI-Powered Growth Infrastructure for Your Codebase

───────────────────────────────────────────────────────────────────────────────

### EXECUTIVE SUMMARY

Growth infrastructure is the engineering layer that injects growth without manual
intervention. It's not marketing—it's architecting viral loops, activation 
triggers, and retention mechanics directly into your codebase. Elite products (Slack, 
Notion, Figma) don't grow through ads; they grow through engineered network effects, 
frictionless onboarding, and compounding user value. This analysis detects where your 
code creates growth opportunities and where it creates friction. To unlock the full 
AI-powered analysis of YOUR codebase's growth infrastructure, run `skene config` to 
get started (2 minutes).

───────────────────────────────────────────────────────────────────────────────

### 1. THE CEO'S NEXT ACTION

**Hypothesis:** The barrier between you and exponential growth insights is a 2-minute 
API key setup. Every day without Skene Growth is a day of missed optimization 
opportunities.

**The Action:** Run `skene config` in your terminal. This interactive setup will 
guide you through:
1. Selecting your preferred LLM provider (Gemini, Anthropic, OpenAI)
2. Creating an API key (we'll provide direct links)
3. Saving your configuration securely

After setup, run `skene-growth analyze .` to get your complete growth analysis.

───────────────────────────────────────────────────────────────────────────────

### 2. STRIP TO THE GROWTH CORE

The fundamental problem is **Feature Accumulation Fallacy**.
Most teams believe more features = more growth. This is false. Growth comes from 
helping customers achieve their desired outcome faster, not from giving them more 
options. Every feature adds cognitive load. Every configuration step increases 
friction. The products that win are the ones that eliminate steps, not add them.

Growth is not about committing code to a codebase and then not looking at the data. 
It's about instrumenting your product, measuring what actually drives customer 
success, and iterating based on evidence—not assumptions. You can't optimize what 
you don't measure.

**Current Core:** Building features customers might want.
**Optimal Core:** Engineering the fastest path to customer success, measured and 
optimized continuously.

───────────────────────────────────────────────────────────────────────────────

### 3. THE PLAYBOOK: GET YOUR API KEY

Elite growth teams don't wait. Here's how to get started:

**Option 1: Gemini (Recommended - Fast & Free tier available)**
*   Link: https://aistudio.google.com/apikey
*   Why: 2M token context, fast, generous free tier
*   Setup time: 60 seconds

**Option 2: Anthropic Claude (Best quality)**
*   Link: https://console.anthropic.com/
*   Why: Superior reasoning, detailed analysis
*   Setup time: 90 seconds

**Option 3: OpenAI (Industry standard)**
*   Link: https://platform.openai.com/api-keys
*   Why: Reliable, well-documented
*   Setup time: 90 seconds

───────────────────────────────────────────────────────────────────────────────

### 4. ENGINEER THE ASYMMETRIC LEVERAGE

**Lever:** Automated Growth Loops with Skene

Most teams build growth features manually, one at a time. This is linear effort for 
linear results. Skene automates the detection, implementation, and optimization of 
growth infrastructure—turning weeks of engineering into minutes of analysis.

*   **The Shadow Rule:** Growth infrastructure should be as automated as your CI/CD 
    pipeline. If you're manually implementing analytics, onboarding flows, or viral 
    mechanics, you're moving too slow.
*   **The Move:** Use Skene to identify growth opportunities, generate implementation 
    code, and continuously measure impact. Every analysis improves the next. Your 
    codebase becomes a growth engine, not just a product.

The leverage compounds: More codebases analyzed → Better pattern detection → 
Faster growth implementation → More successful products.

───────────────────────────────────────────────────────────────────────────────

### 5. APPLY POWER DYNAMICS

*   **Control of Onboarding:** Build instant value delivery into your codebase. Auto-generate 
    demo data, template workspaces, and guided flows. Users experience success before 
    configuration, not after.
*   **Control of Retention:** Instrument every critical action. Measure time-to-value, 
    activation rates, and feature adoption. Growth infrastructure surfaces what's working 
    and what's not—automatically.
*   **Control of Virality:** Engineer sharing into your product. Export with attribution, 
    public showcases, team invites. Every user action becomes a potential acquisition channel.

───────────────────────────────────────────────────────────────────────────────

### 6. THE "AVERAGE" TRAP

*   **The Common Path:** Building features without measuring impact. Shipping code and 
    hoping it drives growth. Optimizing for "more" instead of "faster customer success."
*   **The Failure Point:** Feature-rich products with single-digit activation rates. 
    Beautiful codebases with no growth infrastructure. Teams that build but never measure.

The average team ships features. The elite team engineers growth loops and measures 
everything. Don't be average. Configure Skene and start measuring what actually matters.

───────────────────────────────────────────────────────────────────────────────

### 7. TECHNICAL EXECUTION

#### **Next Growth Loop: Automated Growth Infrastructure**

**Confidence:** 95%

**Exact Logic:**
1. Run `skene config` to set up your API key (2 minutes)
2. Run `skene-growth analyze .` to get your growth infrastructure analysis
3. Review the growth-manifest.json for detected opportunities
4. Implement the highest-impact growth loops first
5. Re-run analysis to measure impact and iterate

**Exact Data Triggers:**
*   Codebase structure analysis (tech stack, frameworks, patterns)
*   Growth feature detection (analytics, onboarding, sharing mechanisms)
*   Opportunity identification (missing viral loops, friction points, activation gaps)

**Exact Stack/Steps:**
*   **Now:** Configure API key and run initial analysis
*   **Next:** Implement top 3 growth opportunities from the manifest
*   **Later:** Integrate Skene into CI/CD to continuously monitor growth infrastructure

**Get API keys:**
*   Gemini: https://aistudio.google.com/apikey
*   Anthropic: https://console.anthropic.com/
*   OpenAI: https://platform.openai.com/api-keys

───────────────────────────────────────────────────────────────────────────────

### 8. THE MEMO

**STATUS:** URGENT
**OBJECTIVE:** ENGINEER GROWTH INFRASTRUCTURE. MEASURE EVERYTHING. ITERATE FAST.

Growth is not about features. It's about helping customers succeed faster. Every 
line of code should either deliver value or measure value delivery. If you're not 
measuring, you're guessing. If you're guessing, you're losing.

This sample preview shows the format. The real analysis identifies YOUR specific 
growth bottlenecks, YOUR missing infrastructure, YOUR optimization opportunities.

**Run this now:**

    skene config

Then analyze:

    skene-growth analyze .

**Get API keys here:**
• Gemini: https://aistudio.google.com/apikey
• Anthropic: https://console.anthropic.com/
• OpenAI: https://platform.openai.com/api-keys

**End of Memo.**

"""
    return report


def _show_sample_report(
    path: Path, output: Optional[Path] = None, exclude_folders: Optional[list[str]] = None
):
    """
    Display sample growth analysis preview (no API key required).
    
    Shows the kind of strategic insights available with full API access.
    Automatically creates .skene-growth.config file in the working directory if it doesn't exist.

    Args:
        path: Path to codebase
        output: Optional output path for JSON report (not used in sample mode)
        exclude_folders: Optional list of folders to exclude (not used in sample mode)
    """
    # Create config file in the working directory if it doesn't exist
    config_path = Path.cwd() / ".skene-growth.config"
    if not config_path.exists():
        sample_config = """# skene-growth configuration
# See: https://github.com/skene-technologies/skene-growth

# API key for LLM provider (can also use SKENE_API_KEY env var)
# Get your API key:
#   • Gemini (recommended): https://aistudio.google.com/apikey
#   • Anthropic: https://console.anthropic.com/
#   • OpenAI: https://platform.openai.com/api-keys
# api_key = "your-api-key-here"

# LLM provider to use (default: gemini)
provider = "gemini"

# Default output directory
output_dir = "./skene-context"

# Enable verbose output
verbose = false
"""
        config_path.write_text(sample_config)
        console.print(
            f"[green]✓ Created config file:[/green] {config_path}\n"
            f"[dim]Edit this file to add your API key and customize settings.[/dim]\n"
        )

    console.print(
        Panel.fit(
            "[bold blue]Growth Analysis Preview[/bold blue]\n"
            f"Path: {path}\n"
            "Mode: Sample Report (no API key required)",
            title="skene-growth",
        )
    )

    # Generate and display sample report
    console.print()
    sample_report = _generate_sample_growth_analysis()
    console.print(sample_report)
    
    # Call to action
    console.print()
    console.print(
        Panel.fit(
            "[bold yellow]Get and share this with team by configurating the api-key[/bold yellow]\n\n"
            "**Run this now:**\n\n"
            "    [bold cyan]skene-growth config[/bold cyan]\n\n"
            "Then analyze:\n\n"
            "    [bold cyan]skene-growth analyze .[/bold cyan]\n\n"
            "**Get API keys here:**\n"
            "• Gemini: https://aistudio.google.com/apikey\n"
            "• Anthropic: https://console.anthropic.com/\n"
            "• OpenAI: https://platform.openai.com/api-keys",
            title="🚀 Unlock Full Analysis",
            border_style="yellow"
        )
    )


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

        uvx skene analyze .
        # Or: uvx skene-growth analyze .

    Or install with pip:

        pip install skene-growth
        skene analyze .
        # Or: skene-growth analyze .
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
        help="LLM model name (e.g., gemini-3-flash-preview for v1beta API)",
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
        uvx skene analyze .
        # Or: uvx skene-growth analyze .

        # Analyze specific path with custom output
        uvx skene analyze ./my-project -o manifest.json

        # With API key
        uvx skene analyze . --api-key "your-key"

        # Specify business type for custom growth template
        uvx skene analyze . --business-type "design-agency"

        # Generate product documentation
        uvx skene analyze . --product-docs
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

    # If no API key and not using local provider, show sample report
    if not resolved_api_key and not is_local_provider:
        console.print(
            "[yellow]No API key provided.[/yellow] Showing sample growth analysis preview.\n"
            "For full AI-powered analysis, set --api-key, SKENE_API_KEY env var, or add to .skene-growth.config\n"
        )
        _show_sample_report(path, output, exclude_folders=exclude if exclude else None)
        return

    if not resolved_api_key and not is_local_provider:
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
        json_path = write_growth_template_outputs(template_data, output_dir)
        console.print(f"[green]Growth template saved to:[/green] {json_path}")
        return template_data
    except Exception as exc:
        console.print(f"[yellow]Warning:[/yellow] Failed to generate growth template: {exc}")
        return None


@app.command()
def audit(
    path: Path = typer.Argument(
        ".",
        help="Path to codebase to audit",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "-o",
        "--output",
        help="Output path (not used in sample mode)",
    ),
    exclude: Optional[list[str]] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Folder names to exclude (not used in sample mode)",
    ),
):
    """
    Show sample growth analysis preview (no API key).

    Displays a preview of the strategic insights and recommendations available
    with full API-powered analysis. This gives you a sense of:
    - Growth opportunity identification
    - Strategic recommendations
    - Implementation roadmaps
    - Technical growth infrastructure

    For full codebase-specific analysis, configure an API key.

    Examples:

        # Show sample growth analysis
        uvx skene audit .
        # Or: uvx skene-growth audit .

        # Analyze with full AI insights (requires API key)
        uvx skene analyze . --api-key YOUR_KEY
    """
    # Always show sample report
    _show_sample_report(path, output, exclude_folders=exclude if exclude else None)


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
        help="LLM model name (e.g., gemini-3-flash-preview for v1beta API)",
    ),
    verbose: bool = typer.Option(
        False,
        "-v",
        "--verbose",
        help="Enable verbose output",
    ),
    onboarding: bool = typer.Option(
        False,
        "--onboarding",
        help="Generate onboarding-focused plan using Senior Onboarding Engineer perspective",
    ),
):
    """
    Generate a growth plan using Council of Growth Engineers.

    Uses manifest and template when present (auto-detected from
    ./skene-context/ or current dir) to generate a growth plan.
    None of these context files are required.

    Examples:

        # Generate growth plan (uses any context files found)
        uvx skene plan --api-key "your-key"
        # Or: uvx skene-growth plan --api-key "your-key"

        # Specify context directory containing manifest and template
        uvx skene plan --context ./my-context --api-key "your-key"

        # Override context file paths
        uvx skene plan --manifest ./manifest.json --template ./template.json

        # Generate onboarding-focused plan
        uvx skene plan --onboarding --api-key "your-key"
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

    # If no API key and not using local provider, show sample report
    if not resolved_api_key and not is_local_provider:
        # Determine path for sample report (use context dir if provided, else current dir)
        sample_path = context if context else Path(".")
        console.print(
            "[yellow]No API key provided.[/yellow] Showing sample growth plan preview.\n"
            "For full AI-powered plan generation, set --api-key, SKENE_API_KEY env var, or add to .skene-growth.config\n"
        )
        _show_sample_report(sample_path, output, exclude_folders=None)
        return

    if not resolved_api_key:
        resolved_api_key = resolved_provider  # Dummy key for local server

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

    plan_type = "onboarding plan" if onboarding else "growth plan"
    console.print(
        Panel.fit(
            f"[bold blue]Generating {plan_type}[/bold blue]\n"
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
            onboarding=onboarding,
        )
    )


@app.command()
def chat(
    path: Path = typer.Argument(
        ".",
        help="Path to codebase to analyze",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
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
        help="LLM model name (e.g., gemini-3-flash-preview for v1beta API)",
    ),
    max_steps: int = typer.Option(
        4,
        "--max-steps",
        help="Maximum tool calls per user request",
    ),
    tool_output_limit: int = typer.Option(
        4000,
        "--tool-output-limit",
        help="Max tool output characters kept in context",
    ),
):
    """
    Interactive terminal chat that invokes skene-growth tools.

    Examples:

        uvx skene chat . --api-key "your-key"
        # Or: uvx skene-growth chat . --api-key "your-key"
        uvx skene chat ./my-project --provider gemini --model gemini-3-flash-preview
    """
    config = load_config()

    resolved_api_key = api_key or config.api_key
    resolved_provider = provider or config.provider
    if model:
        resolved_model = model
    else:
        resolved_model = config.get("model") or default_model_for_provider(resolved_provider)

    is_local_provider = resolved_provider.lower() in (
        "lmstudio",
        "lm-studio",
        "lm_studio",
        "ollama",
    )

    if not resolved_api_key:
        if is_local_provider:
            resolved_api_key = resolved_provider
        else:
            console.print(
                "[yellow]Warning:[/yellow] No API key provided. "
                "Set --api-key, SKENE_API_KEY env var, or add to .skene-growth.config"
            )
            raise typer.Exit(1)

    from skene_growth.cli.chat import run_chat

    run_chat(
        console=console,
        repo_path=path,
        api_key=resolved_api_key,
        provider=resolved_provider,
        model=resolved_model,
        max_steps=max_steps,
        tool_output_limit=tool_output_limit,
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
    # Now section 1 (after Executive Summary), but also match old formats for backwards compatibility
    pattern = r"##?\s*(?:1|2|7)?\.\s*(?:THE\s+)?CEO'?s?\s+Next\s+Action.*?\n\n\*\*(.*?):\*\*\s*(.*?)(?=\n\n###|\n\n##|\Z)"
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
    pattern2 = r"##?\s*(?:1|2|7)?\.\s*(?:THE\s+)?CEO'?s?\s+Next\s+Action.*?\n\n(.*?)(?=\n\n###|\n\n##|\Z)"
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
    onboarding: bool = False,
):
    """Run cycle generation using Council of Growth Engineers."""
    from pydantic import SecretStr

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

    # Print the report to terminal (same format as sample report)
    if memo_content:
        console.print()
        console.print(memo_content)

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

        uvx skene validate ./growth-manifest.json
        # Or: uvx skene-growth validate ./growth-manifest.json
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


def _get_provider_models(provider: str) -> list[str]:
    """Get list of recommended models for a provider (up to 5)."""
    models_by_provider = {
        "openai": [
            "gpt-5.2",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
        ],
        "gemini": [
            "gemini-3-flash-preview",  # v1beta API (Speed/Value - Daily Driver)
            "gemini-3-pro-preview",  # v1beta API (Flagship - King of Versatility)
            "gemini-2.5-flash",  # Legacy/Stable
            "gemini-2.5-pro",  # Legacy/Stable
            "gemini-3-nano-preview",  # Legacy
        ],
        "anthropic": [
            "claude-opus-4-5",            
            "claude-sonnet-4-5",
            "claude-haiku-4-5",
        ],
        "claude": [
            "claude-opus-4-5",            
            "claude-sonnet-4-5",
            "claude-haiku-4-5",
        ],
        "lmstudio": [
            "custom-model",
            "llama-3.3-70b",
            "llama-3.3-8b",
            "mistral-large",
            "phi-4",
        ],
        "lm-studio": [
            "custom-model",
            "llama-3.3-70b",
            "llama-3.3-8b",
            "mistral-large",
            "phi-4",
        ],
        "lm_studio": [
            "custom-model",
            "llama-3.3-70b",
            "llama-3.3-8b",
            "mistral-large",
            "phi-4",
        ],
        "ollama": [
            "llama3.3",
            "llama3.2",
            "mistral",
            "qwen2.5",
            "phi4",
        ],
    }
    return models_by_provider.get(provider.lower(), ["gpt-4o"])


def _save_config(config_path: Path, provider: str, model: str, api_key: str) -> None:
    """Save configuration to a TOML file."""
    # Read existing config if it exists
    existing_config = {}
    if config_path.exists():
        try:
            from skene_growth.config import load_toml
            existing_config = load_toml(config_path)
        except Exception:
            pass  # If we can't read it, start fresh

    # Update values
    config_data = {
        **existing_config,
        "provider": provider,
        "model": model,
        "api_key": api_key,
    }

    # Write TOML file
    # Since tomli_w might not be available, we'll write manually
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = ["# skene-growth configuration"]
    lines.append("# See: https://github.com/skene-technologies/skene-growth")
    lines.append("")
    lines.append("# API key for LLM provider (can also use SKENE_API_KEY env var)")
    lines.append(f'api_key = "{api_key}"')
    lines.append("")
    lines.append("# LLM provider to use")
    lines.append(f'provider = "{provider}"')
    lines.append("")
    lines.append("# Model to use")
    lines.append(f'model = "{model}"')
    lines.append("")
    
    # Preserve other settings
    for key, value in existing_config.items():
        if key not in ["api_key", "provider", "model"]:
            if isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            elif isinstance(value, bool):
                lines.append(f"{key} = {str(value).lower()}")
            elif isinstance(value, list):
                lines.append(f'{key} = {value}')
            else:
                lines.append(f"{key} = {value}")
    
    # Add defaults if not present
    if "output_dir" not in existing_config:
        lines.append("")
        lines.append("# Default output directory")
        lines.append('output_dir = "./skene-context"')
    
    if "verbose" not in existing_config:
        lines.append("")
        lines.append("# Enable verbose output")
        lines.append("verbose = false")
    
    config_path.write_text("\n".join(lines))


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
        uvx skene config --show
        # Or: uvx skene-growth config --show

        # Create a sample config file
        uvx skene config --init
        # Or: uvx skene-growth config --init
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

    current_provider = cfg.provider
    current_model = cfg.model
    
    values_table.add_row("provider", current_provider, "config/default")
    values_table.add_row("model", current_model, "config/default")
    values_table.add_row("output_dir", cfg.output_dir, "config/default")
    values_table.add_row("verbose", str(cfg.verbose), "config/default")

    console.print(values_table)

    if not project_cfg and not user_cfg:
        console.print("\n[dim]Tip: Run 'skene-growth config --init' to create a config file[/dim]")
        return

    # Ask if user wants to edit
    console.print()
    edit = Confirm.ask("[bold yellow]Do you want to edit this configuration?[/bold yellow]", default=False)
    
    if not edit:
        return
    
    # Determine which config file to edit (prefer project, fallback to user)
    config_path = project_cfg if project_cfg else user_cfg
    if not config_path:
        # Create user config if neither exists
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            config_dir = Path(config_home) / "skene-growth"
        else:
            config_dir = Path.home() / ".config" / "skene-growth"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config"
    
    # Ask for provider
    console.print()
    providers = ["openai", "gemini", "anthropic", "claude", "lmstudio", "ollama"]
    provider_options = "\n".join([f"  {i+1}. {p}" for i, p in enumerate(providers)])
    console.print(f"[bold]Select LLM provider:[/bold]\n{provider_options}")
    
    while True:
        provider_choice = Prompt.ask(
            f"\n[cyan]Provider[/cyan] (1-{len(providers)})",
            default=str(providers.index(current_provider) + 1) if current_provider in providers else "1"
        )
        try:
            idx = int(provider_choice) - 1
            if 0 <= idx < len(providers):
                selected_provider = providers[idx]
                break
            else:
                console.print("[red]Invalid choice. Please enter a number between 1 and {}[/red]".format(len(providers)))
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
    
    # Ask for model based on provider
    console.print()
    models = _get_provider_models(selected_provider)
    model_options = "\n".join([f"  {i+1}. {m}" for i, m in enumerate(models)])
    console.print(f"[bold]Select model for {selected_provider}:[/bold]\n{model_options}")
    
    # Determine default model
    default_model_idx = None
    default_model_text = ""
    
    # If provider matches and current model is in the list, use it as default
    if selected_provider == current_provider and current_model in models:
        default_model_idx = str(models.index(current_model) + 1)
        default_model_text = f" (current: {current_model})"
    elif selected_provider == current_provider and current_model:
        # Same provider but model not in list - show as hint
        console.print(f"\n[dim]Note: Current model '{current_model}' not in recommended list. You can enter it manually.[/dim]")
    
    while True:
        prompt_text = f"\n[cyan]Model[/cyan] (1-{len(models)} or enter custom model name)"
        if default_model_text:
            prompt_text += default_model_text
        
        model_choice = Prompt.ask(
            prompt_text,
            default=default_model_idx if default_model_idx else "1"
        )
        
        try:
            idx = int(model_choice) - 1
            if 0 <= idx < len(models):
                selected_model = models[idx]
                break
            else:
                console.print(f"[yellow]Number out of range. Using as custom model name.[/yellow]")
                selected_model = model_choice
                break
        except ValueError:
            # Allow custom model name
            selected_model = model_choice
            break
    
    # Ask for API key
    console.print()
    api_key_prompt = "[cyan]API Key[/cyan]"
    if api_key:
        api_key_prompt += f" (current: {api_key[:4]}...{api_key[-4:]})"
    api_key_prompt += ": "
    
    new_api_key = Prompt.ask(
        api_key_prompt,
        password=True,
        default=api_key if api_key else ""
    )
    
    if not new_api_key:
        console.print("[yellow]No API key provided. Configuration will be saved without API key.[/yellow]")
        new_api_key = ""
    
    # Save configuration
    try:
        _save_config(config_path, selected_provider, selected_model, new_api_key)
        console.print(f"\n[green]✓ Configuration saved to:[/green] {config_path}")
        console.print(f"[green]  Provider:[/green] {selected_provider}")
        console.print(f"[green]  Model:[/green] {selected_model}")
        console.print(f"[green]  API Key:[/green] {'Set' if new_api_key else 'Not set'}")
    except Exception as e:
        console.print(f"[red]Error saving configuration:[/red] {e}")
        raise typer.Exit(1)


def _run_chat_default(
    path: Path = typer.Argument(
        ".",
        help="Path to codebase to analyze",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
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
        help="LLM model name (e.g., gemini-3-flash-preview for v1beta API)",
    ),
    max_steps: int = typer.Option(
        4,
        "--max-steps",
        help="Maximum tool calls per user request",
    ),
    tool_output_limit: int = typer.Option(
        4000,
        "--tool-output-limit",
        help="Max tool output characters kept in context",
    ),
):
    """Interactive terminal chat that invokes skene-growth tools."""
    # Auto-create user config on first run if no config exists
    from skene_growth.config import find_project_config, find_user_config

    user_cfg = find_user_config()
    project_cfg = find_project_config()

    if not user_cfg and not project_cfg:
        # Create user config directory if it doesn't exist
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            config_dir = Path(config_home) / "skene-growth"
        else:
            config_dir = Path.home() / ".config" / "skene-growth"

        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config"

        # Create sample config
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
        console.print(
            f"[green]Created config file:[/green] {config_path}\n"
            "[dim]Edit this file to add your API key and customize settings.[/dim]\n"
        )

    config = load_config()

    resolved_api_key = api_key or config.api_key
    resolved_provider = provider or config.provider
    if model:
        resolved_model = model
    else:
        resolved_model = config.get("model") or default_model_for_provider(resolved_provider)

    is_local_provider = resolved_provider.lower() in (
        "lmstudio",
        "lm-studio",
        "lm_studio",
        "ollama",
    )

    if not resolved_api_key:
        if is_local_provider:
            resolved_api_key = resolved_provider
        else:
            # Find which config file exists to show helpful message
            config_file = find_project_config() or find_user_config()
            if config_file:
                console.print(
                    f"[yellow]Warning:[/yellow] No API key provided. "
                    "While that is ok, without api-key, Skene will not use advanced AI-analysis tools.\n"
                    f"To enable AI features, add your API key to: [cyan]{config_file}[/cyan]\n"
                    "Or set --api-key flag or SKENE_API_KEY env var."
                )
            else:
                console.print(
                    "[yellow]Warning:[/yellow] No API key provided. "
                    "While that is ok, without api-key, Skene will not use advanced AI-analysis tools.\n"
                    "To enable AI features, set --api-key, SKENE_API_KEY env var, or create a config file:\n"
                    "  ~/.config/skene-growth/config (user-level)\n"
                    "  ./.skene-growth.config (project-level)"
                )
            raise typer.Exit(1)

    from skene_growth.cli.chat import run_chat

    run_chat(
        console=console,
        repo_path=path,
        api_key=resolved_api_key,
        provider=resolved_provider,
        model=resolved_model,
        max_steps=max_steps,
        tool_output_limit=tool_output_limit,
    )


def skene_entry_point():
    """Entry point for 'skene' command - includes all commands, defaults to chat."""
    # Create a typer app for the skene command that includes all commands
    skene_app = typer.Typer(
        name="skene",
        help="PLG analysis toolkit for codebases. Analyze code, detect growth opportunities.",
        add_completion=False,
        no_args_is_help=False,
    )

    # Add all commands from the main app as subcommands FIRST
    # This ensures subcommands are recognized before the callback
    skene_app.command()(analyze)
    skene_app.command()(audit)
    skene_app.command()(plan)
    skene_app.command()(chat)
    skene_app.command()(validate)
    skene_app.command()(config)

    # Add callback to handle default case (no subcommand) - launches chat
    # Added AFTER commands so subcommands take precedence
    # No arguments in callback to avoid conflicts with subcommands
    @skene_app.callback(invoke_without_command=True)
    def default_callback(ctx: typer.Context):
        """Default: Launch interactive chat. Use subcommands for other operations."""
        # Only invoke chat if no subcommand was provided
        if ctx.invoked_subcommand is None:
            # Parse all arguments manually from sys.argv
            import sys
            path_arg = "."
            api_key_arg = None
            provider_arg = None
            model_arg = None
            max_steps_arg = 4
            tool_output_limit_arg = 4000
            
            args = sys.argv[1:]  # Skip script name
            i = 0
            while i < len(args):
                arg = args[i]
                if arg in ["--api-key"] and i + 1 < len(args):
                    api_key_arg = args[i + 1]
                    i += 2
                elif arg in ["--provider", "-p"] and i + 1 < len(args):
                    provider_arg = args[i + 1]
                    i += 2
                elif arg in ["--model", "-m"] and i + 1 < len(args):
                    model_arg = args[i + 1]
                    i += 2
                elif arg == "--max-steps" and i + 1 < len(args):
                    max_steps_arg = int(args[i + 1])
                    i += 2
                elif arg == "--tool-output-limit" and i + 1 < len(args):
                    tool_output_limit_arg = int(args[i + 1])
                    i += 2
                elif arg.startswith("--api-key="):
                    api_key_arg = arg.split("=", 1)[1]
                    i += 1
                elif arg.startswith("--provider=") or arg.startswith("-p="):
                    provider_arg = arg.split("=", 1)[1]
                    i += 1
                elif arg.startswith("--model=") or arg.startswith("-m="):
                    model_arg = arg.split("=", 1)[1]
                    i += 1
                elif not arg.startswith("-"):
                    # Found a non-option argument - this is the path
                    path_arg = arg
                    i += 1
                else:
                    i += 1
            
            # Check environment variable for API key if not provided
            if not api_key_arg:
                api_key_arg = os.environ.get("SKENE_API_KEY")
            
            _run_chat_default(
                Path(path_arg),
                api_key_arg,
                provider_arg,
                model_arg,
                max_steps_arg,
                tool_output_limit_arg,
            )

    # Run the app - typer will handle sys.argv automatically
    skene_app()


if __name__ == "__main__":
    app()
