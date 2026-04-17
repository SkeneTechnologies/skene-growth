"""Derive a growth manifest from an existing schema + codebase evidence."""

import asyncio
from pathlib import Path

import typer
from pydantic import SecretStr
from rich.panel import Panel

from skene.analyzers.growth_from_schema import analyse_growth_from_schema
from skene.analyzers.plan_engine import DEFAULT_FEATURE_COUNT, plan_engine_from_manifest
from skene.cli.app import app, resolve_cli_config
from skene.output import console, error, success, warning


@app.command(name="analyse-growth-from-schema")
def analyse_growth_from_schema_cmd(
    path: Path | None = typer.Argument(
        None,
        help="Path to codebase to analyse (omit for current directory)",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    schema: Path = typer.Option(
        Path("./skene/schema.yaml"),
        "-s",
        "--schema",
        help="Path to schema.yaml (run 'analyse-journey' first to generate it)",
    ),
    output: Path = typer.Option(
        Path("./skene/growth-manifest.json"),
        "-o",
        "--output",
        help="Output path for growth-manifest.json",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        envvar="SKENE_API_KEY",
        help="API key for LLM provider (or set SKENE_API_KEY env var)",
    ),
    provider: str | None = typer.Option(
        None,
        "--provider",
        "-p",
        help="LLM provider (openai, gemini, anthropic/claude, lmstudio, ollama, generic, skene)",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="LLM model name",
    ),
    base_url: str | None = typer.Option(
        None,
        "--base-url",
        envvar="SKENE_BASE_URL",
        help="Base URL for API endpoint",
    ),
    exclude: list[str] | None = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Folder name to exclude from grep (repeatable)",
    ),
    quiet: bool = typer.Option(
        False,
        "-q",
        "--quiet",
        help="Suppress status messages; show only errors and final results",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Show diagnostic messages and log all LLM input/output",
    ),
    no_fallback: bool = typer.Option(
        False,
        "--no-fallback",
        help="Disable model fallback on rate limits; retry same model instead",
    ),
    skip_plan: bool = typer.Option(
        False,
        "--skip-plan",
        help="Do not run analyse-plan after the growth manifest is written",
    ),
    plan_output: Path | None = typer.Option(
        None,
        "--plan-output",
        help=(
            "Path for engine.yaml after planning "
            "(default: same directory as schema, filename engine.yaml)"
        ),
    ),
    plan_count: int = typer.Option(
        DEFAULT_FEATURE_COUNT,
        "--plan-count",
        min=1,
        max=10,
        help="Number of growth features to promote into engine.yaml",
    ),
):
    """
    Derive a growth manifest from the already-built schema plus codebase evidence.

    Uses the tables, columns, and relationships in ``schema.yaml`` to hypothesise
    which growth features (invites, subscriptions, onboarding, analytics, etc.)
    the product supports, then searches the codebase with ripgrep for grounded
    evidence and assembles a standard ``growth-manifest.json``.

    ``skene analyse-journey`` runs this step automatically after writing the
    schema (unless ``--skip-growth-manifest``). You can also invoke this command
    alone, or point ``--schema`` at an existing schema YAML file.

    Examples:

        skene analyse-growth-from-schema

        skene analyse-growth-from-schema ./my-project -s ./skene/schema.yaml

        skene analyse-growth-from-schema --provider anthropic --model claude-sonnet-4-5
    """
    base_path = (path if path is not None else Path(".")).resolve()
    if not base_path.exists():
        error(f"Path does not exist: {base_path}")
        raise typer.Exit(1)
    if not base_path.is_dir():
        error(f"Path is not a directory: {base_path}")
        raise typer.Exit(1)

    resolved_schema = schema if schema.is_absolute() else (Path.cwd() / schema).resolve()
    if not resolved_schema.exists():
        error(
            f"Schema file not found: {resolved_schema}\n"
            "Run 'skene analyse-journey' first, or pass --schema <path>."
        )
        raise typer.Exit(1)

    rc = resolve_cli_config(
        api_key=api_key,
        provider=provider,
        model=model,
        base_url=base_url,
        quiet=quiet,
        debug=debug,
    )

    if not rc.api_key and not rc.is_local:
        error(
            "An API key is required for analyse-growth-from-schema. "
            "Set --api-key, SKENE_API_KEY env var, or add api_key to .skene.config."
        )
        raise typer.Exit(1)

    resolved_api_key = rc.api_key or rc.provider

    resolved_output = output if output.is_absolute() else (Path.cwd() / output).resolve()
    if resolved_output.exists() and resolved_output.is_dir():
        resolved_output = (resolved_output / "growth-manifest.json").resolve()
    elif not resolved_output.suffix:
        resolved_output = (resolved_output / "growth-manifest.json").resolve()
    else:
        resolved_output = resolved_output.resolve()

    console.print(
        Panel.fit(
            "[bold blue]Deriving growth manifest from schema[/bold blue]\n"
            f"Path: {base_path}\n"
            f"Schema: {resolved_schema}\n"
            f"Provider: {rc.provider}\n"
            f"Model: {rc.model}\n"
            f"Output: {resolved_output}\n"
            f"Then: {'(plan skipped)' if skip_plan else 'engine.yaml plan (analyse-plan)'}",
            title="skene · analyse-growth-from-schema",
        )
    )

    from skene.llm import create_llm_client

    async def execute():
        llm = create_llm_client(
            rc.provider,
            SecretStr(resolved_api_key),
            rc.model,
            base_url=rc.base_url,
            debug=rc.debug,
            no_fallback=no_fallback,
        )

        state = await analyse_growth_from_schema(
            path=base_path,
            schema_path=resolved_schema,
            llm=llm,
            output_path=resolved_output,
            excludes=exclude if exclude else None,
        )

        if not state.features:
            warning("No current growth features were grounded in the codebase.")
        success(
            f"Manifest saved to: {resolved_output} "
            f"({len(state.features)} feature(s), {len(state.growth_opportunities)} opportunity(ies))"
        )

        if skip_plan:
            return

        if not state.growth_opportunities:
            warning("Skipping analyse-plan: manifest has no growth_opportunities.")
            return

        resolved_plan = (
            plan_output
            if plan_output is not None
            else (resolved_schema.parent / "engine.yaml")
        )
        if not resolved_plan.is_absolute():
            resolved_plan = (Path.cwd() / resolved_plan).resolve()
        if resolved_plan.exists() and resolved_plan.is_dir():
            resolved_plan = (resolved_plan / "engine.yaml").resolve()
        elif not resolved_plan.suffix:
            resolved_plan = (resolved_plan / "engine.yaml").resolve()
        else:
            resolved_plan = resolved_plan.resolve()

        try:
            pstate = await plan_engine_from_manifest(
                manifest_path=resolved_output,
                schema_path=resolved_schema,
                llm=llm,
                engine_path=resolved_plan,
                project_root=base_path,
                feature_count=plan_count,
            )
            added = len(pstate.delta.features) if pstate.delta else 0
            total = len(pstate.merged.features) if pstate.merged else 0
            if added == 0:
                warning("analyse-plan produced no new features; engine.yaml left unchanged.")
            success(
                f"engine.yaml saved to: {resolved_plan} "
                f"({added} feature(s) planned, {total} total after merge)"
            )
        except Exception as e:
            warning(f"analyse-plan step failed (manifest was saved): {e}")

    asyncio.run(execute())
