"""Analyse the data schema of a codebase via iterative grep + LLM passes."""

import asyncio
from pathlib import Path

import typer
from pydantic import SecretStr
from rich.panel import Panel

from skene.analyzers.growth_from_schema import analyse_growth_from_schema
from skene.analyzers.plan_engine import DEFAULT_FEATURE_COUNT, plan_engine_from_manifest
from skene.analyzers.schema_journey import analyse_journey
from skene.cli.app import app, resolve_cli_config
from skene.output import console, error, success, warning


@app.command(name="analyse-journey")
def analyse_journey_cmd(
    path: Path | None = typer.Argument(
        None,
        help="Path to codebase to analyse (omit for current directory)",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output: Path = typer.Option(
        Path("./skene/schema.yaml"),
        "-o",
        "--output",
        help="Output path for schema.yaml",
    ),
    iterations: int = typer.Option(
        6,
        "--iterations",
        "-n",
        min=1,
        max=30,
        help="Number of grep + LLM refinement iterations",
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
    skip_growth_manifest: bool = typer.Option(
        False,
        "--skip-growth-manifest",
        help="Do not run analyse-growth-from-schema after the schema is written",
    ),
    growth_output: Path | None = typer.Option(
        None,
        "--growth-output",
        help=(
            "Path for growth-manifest.json after schema analysis "
            "(default: same directory as schema output, filename growth-manifest.json)"
        ),
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
            "(default: same directory as schema output, filename engine.yaml)"
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
    Analyse the data schema of a codebase.

    Repeatedly runs grep (or ripgrep) for schema-related patterns — classes,
    models, tables, migrations, typed records — and asks the LLM provider to
    distil entities into a growing schema. Each iteration's LLM response also
    suggests the next grep keyword, so the analysis journeys through the
    codebase until the schema stabilises.

    The result is saved as YAML (default: ./skene/schema.yaml).

    By default, **analyse-growth-from-schema** runs immediately afterward on the
    same schema file and writes ``growth-manifest.json`` next to it (unless
    ``--skip-growth-manifest`` is set).

    Examples:

        skene analyse-journey

        skene analyse-journey ./my-project -n 10 -o ./skene/schema.yaml

        skene analyse-journey --provider anthropic --model claude-sonnet-4-5
    """
    base_path = (path if path is not None else Path(".")).resolve()
    if not base_path.exists():
        error(f"Path does not exist: {base_path}")
        raise typer.Exit(1)
    if not base_path.is_dir():
        error(f"Path is not a directory: {base_path}")
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
            "An API key is required for analyse-journey. "
            "Set --api-key, SKENE_API_KEY env var, or add api_key to .skene.config."
        )
        raise typer.Exit(1)

    resolved_api_key = rc.api_key or rc.provider  # Dummy key for local servers.

    resolved_output = output if output.is_absolute() else (Path.cwd() / output).resolve()
    if resolved_output.exists() and resolved_output.is_dir():
        resolved_output = (resolved_output / "schema.yaml").resolve()
    elif not resolved_output.suffix:
        resolved_output = (resolved_output / "schema.yaml").resolve()
    else:
        resolved_output = resolved_output.resolve()

    console.print(
        Panel.fit(
            "[bold blue]Analysing codebase schema[/bold blue]\n"
            f"Path: {base_path}\n"
            f"Provider: {rc.provider}\n"
            f"Model: {rc.model}\n"
            f"Iterations: {iterations}\n"
            f"Output: {resolved_output}\n"
            f"Then: {'(growth manifest skipped)' if skip_growth_manifest else 'schema-driven growth manifest'}"
            + ("" if skip_growth_manifest or skip_plan else " → engine.yaml plan"),
            title="skene · analyse-journey",
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

        state = await analyse_journey(
            path=base_path,
            llm=llm,
            output_path=resolved_output,
            iterations=iterations,
            excludes=exclude if exclude else None,
        )

        if not state.tables:
            warning("No schema tables were discovered.")
        success(f"Schema saved to: {resolved_output} ({len(state.tables)} tables)")

        if skip_growth_manifest:
            return

        resolved_growth = (
            growth_output
            if growth_output is not None
            else (resolved_output.parent / "growth-manifest.json")
        )
        if not resolved_growth.is_absolute():
            resolved_growth = (Path.cwd() / resolved_growth).resolve()
        if resolved_growth.exists() and resolved_growth.is_dir():
            resolved_growth = (resolved_growth / "growth-manifest.json").resolve()
        elif not resolved_growth.suffix:
            resolved_growth = (resolved_growth / "growth-manifest.json").resolve()
        else:
            resolved_growth = resolved_growth.resolve()

        try:
            gstate = await analyse_growth_from_schema(
                path=base_path,
                schema_path=resolved_output,
                llm=llm,
                output_path=resolved_growth,
                excludes=exclude if exclude else None,
            )
            if not gstate.features:
                warning("Growth manifest: no features grounded from schema + codebase.")
            success(
                f"Growth manifest saved to: {resolved_growth} "
                f"({len(gstate.features)} feature(s), {len(gstate.growth_opportunities)} opportunity(ies))"
            )
        except Exception as e:
            warning(f"Growth manifest step failed (schema was saved): {e}")
            return

        if skip_plan:
            return

        if not gstate.growth_opportunities:
            warning("Skipping analyse-plan: manifest has no growth_opportunities.")
            return

        resolved_plan = (
            plan_output
            if plan_output is not None
            else (resolved_output.parent / "engine.yaml")
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
                manifest_path=resolved_growth,
                schema_path=resolved_output,
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
