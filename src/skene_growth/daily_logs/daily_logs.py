"""
Daily logs functionality for fetching data from sources and storing metrics.

This module handles:
- Reading configuration from skene.json
- Reading growth objectives
- Fetching data from configured sources (API, database, etc.)
- Manual input fallback when automatic fetch fails
- Storing daily logs in JSON format with deduplication
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console
from rich.prompt import Prompt

from skene_growth.config import load_config

console = Console()


def _load_json_file(file_path: Path) -> dict[str, Any] | list[Any]:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")


def _parse_markdown_objectives(file_path: Path) -> list[dict[str, Any]]:
    """Parse growth objectives from Markdown format.

    Expected format:
    ## SECTION_NAME
    - **Metric:** Metric Name
    - **Target:** target value
    - **Tolerance:** tolerance
    """
    objectives = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")

    lines = content.split("\n")
    current_objective = {}

    for line in lines:
        line = line.strip()

        # Skip empty lines, main header, horizontal rules, and footer
        if not line or line.startswith("# ") or line.startswith("---") or line.startswith("*"):
            continue

        # Check for section headers (## SECTION_NAME)
        if line.startswith("##"):
            # Save previous objective if exists
            if current_objective.get("metric_id"):
                objectives.append(current_objective)
                current_objective = {}
            continue

        # Parse metric fields
        if line.startswith("- **Metric:**"):
            metric_name = line.replace("- **Metric:**", "").strip()
            current_objective["metric_id"] = metric_name.lower().replace(" ", "_")
            current_objective["name"] = metric_name
        elif line.startswith("- **Source:**"):
            source = line.replace("- **Source:**", "").strip()
            current_objective["source"] = source
            current_objective["source_id"] = source
        elif line.startswith("- **Target:**"):
            target = line.replace("- **Target:**", "").strip()
            current_objective["target"] = target
        elif line.startswith("- **Tolerance:**"):
            tolerance = line.replace("- **Tolerance:**", "").strip()
            current_objective["tolerance"] = tolerance

    # Add last objective if exists
    if current_objective.get("metric_id"):
        objectives.append(current_objective)

    return objectives


def _load_skene_config(skene_context_path: Path) -> dict[str, Any] | None:
    """Load skene.json configuration file. Returns None if not found."""
    skene_json_path = skene_context_path / "skene.json"

    if not skene_json_path.exists():
        return None

    try:
        return _load_json_file(skene_json_path)
    except Exception:
        return None


def _load_growth_objectives(skene_context_path: Path) -> list[dict[str, Any]]:
    """Load growth objectives file.

    Checks in this order:
    1. Filename from config (growth_objectives_file) in skene-context directory
    2. Common filenames in skene-context directory
    3. Prompt user if still not found
    """
    # Get filename from config if specified
    config = load_config()
    config_filename = config.get("growth_objectives_file")

    # Build list of possible filenames to try
    possible_names = []

    # If config specifies a filename, try it first
    if config_filename:
        possible_names.append(config_filename)

    # Add default and common names (default is growth-objectives.md)
    possible_names.extend(
        [
            "growth-objectives.md",
            "growth-objectives.json",
            "growth_objectives.json",
            "growth-objectives",
            "growth_objectives",
        ]
    )

    objectives_path = None
    for name in possible_names:
        candidate = skene_context_path / name
        if candidate.exists():
            objectives_path = candidate
            break

    # If still not found, prompt user
    if objectives_path is None:
        console.print(f"[yellow]Warning:[/yellow] Growth objectives file not found in {skene_context_path}")
        console.print("Please provide the path to growth objectives file:")
        user_path = Prompt.ask("Path to growth objectives file")
        objectives_path = Path(user_path)

        if not objectives_path.exists():
            raise FileNotFoundError(f"Growth objectives file not found at {objectives_path}")

    # Handle Markdown files
    if objectives_path.suffix == ".md":
        return _parse_markdown_objectives(objectives_path)

    # Handle JSON files
    data = _load_json_file(objectives_path)

    # Handle both array and object with array property
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "objectives" in data:
        return data["objectives"]
    elif isinstance(data, dict) and "growth_objectives" in data:
        return data["growth_objectives"]
    else:
        # Try to find any array property
        for key, value in data.items():
            if isinstance(value, list):
                return value
        raise ValueError("Could not find objectives array in growth objectives file")


def _get_source_config(source_id: str, skene_config: dict[str, Any]) -> dict[str, Any] | None:
    """Get source configuration from skene.json by source ID."""
    sources = skene_config.get("sources", [])

    # Handle list of source objects
    if isinstance(sources, list):
        for source in sources:
            if isinstance(source, dict):
                if source.get("id") == source_id or source.get("source_id") == source_id:
                    return source

    # Handle dict of sources
    elif isinstance(sources, dict):
        return sources.get(source_id)

    return None


def _prompt_for_manual_value(
    metric_id: str,
    source_id: str | None = None,
    reason: str = "",
    example: str | None = None,
    provided_values: dict[str, str] | None = None,
    non_interactive: bool = False,
) -> str:
    """Prompt user to manually enter a metric value (accepts any text).

    Args:
        metric_id: The metric identifier
        source_id: Optional source ID
        reason: Optional reason message
        example: Optional example value
        provided_values: Optional dict of metric_id -> value for non-interactive mode
        non_interactive: If True, raise error instead of prompting when value not provided

    Returns:
        The metric value as a string
    """
    # Check if value was provided in non-interactive mode
    if provided_values is not None and metric_id in provided_values:
        return provided_values[metric_id]

    # In non-interactive mode, raise error if value not provided
    if non_interactive:
        raise ValueError(
            f"Metric '{metric_id}' requires a value but none was provided. "
            f"Use --values or --values-file to provide values, or use --list-metrics to see required metrics."
        )

    # Interactive mode: prompt user
    if reason:
        console.print(f"[yellow]{reason}[/yellow]")

    display_text = f"Please enter the value for metric '[bold]{metric_id}[/bold]'"
    if source_id:
        display_text += f" (source: {source_id})"
    display_text += ":"
    console.print(display_text)

    # Add example if provided
    if example:
        console.print(f"[dim]Example: {example}[/dim]")
    else:
        # Default examples based on common metric types
        if "rate" in metric_id.lower() or "percentage" in metric_id.lower():
            console.print("[dim]Example: 95% or 0.95[/dim]")
        elif "count" in metric_id.lower() or "number" in metric_id.lower():
            console.print("[dim]Example: 150 or 1,234[/dim]")
        elif "time" in metric_id.lower() or "duration" in metric_id.lower() or "minutes" in metric_id.lower():
            console.print("[dim]Example: 2.5 minutes or 150 seconds[/dim]")
        else:
            console.print("[dim]Example: Any text or number value[/dim]")

    value = Prompt.ask("Value")
    return value


def _extract_value_from_json(data: Any, path: str) -> Any:
    """Extract a value from nested JSON using dot notation path."""
    if not path:
        return data

    parts = path.split(".")
    current = data

    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            idx = int(part)
            current = current[idx] if idx < len(current) else None
        else:
            return None

        if current is None:
            return None

    return current


def _fetch_from_api(source_config: dict[str, Any], metric_id: str) -> str | None:
    """Fetch data from an API source."""
    url = source_config.get("url")
    if not url:
        return None

    # Build headers
    headers = {}
    auth_type = source_config.get("auth", "none")

    if auth_type == "api_key":
        api_key = source_config.get("api_key") or os.environ.get(
            f"SKENE_SOURCE_{source_config.get('id', '').upper()}_API_KEY"
        )
        header_name = source_config.get("api_key_header", "X-API-Key")
        if api_key:
            headers[header_name] = api_key
    elif auth_type == "bearer":
        token = source_config.get("bearer_token") or os.environ.get(
            f"SKENE_SOURCE_{source_config.get('id', '').upper()}_TOKEN"
        )
        if token:
            headers["Authorization"] = f"Bearer {token}"

    # Replace {metric_id} placeholder in URL if present
    url = url.replace("{metric_id}", metric_id)

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            value_path = source_config.get("value_path", "")
            value = _extract_value_from_json(data, value_path)

            if value is not None:
                return str(value)
            return None

    except httpx.HTTPStatusError as e:
        console.print(f"[dim]API returned error: {e.response.status_code}[/dim]")
        return None
    except httpx.RequestError as e:
        console.print(f"[dim]API request failed: {e}[/dim]")
        return None
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        console.print(f"[dim]Failed to parse API response: {e}[/dim]")
        return None


def _fetch_from_database(source_config: dict[str, Any], metric_id: str) -> str | None:
    """Fetch data from a database source."""
    connection_string = source_config.get("connection_string")
    query = source_config.get("query")

    if not connection_string or not query:
        return None

    # Replace {metric_id} placeholder in query if present
    query = query.replace("{metric_id}", metric_id)

    try:
        # Try to import database libraries
        # Support for PostgreSQL
        try:
            import psycopg2

            conn = psycopg2.connect(connection_string)
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            conn.close()
            if result:
                return str(result[0])
            return None
        except ImportError:
            pass

        # Support for SQLite
        try:
            import sqlite3

            if connection_string.startswith("sqlite:"):
                db_path = connection_string.replace("sqlite:", "").replace("///", "")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(query)
                result = cursor.fetchone()
                conn.close()
                if result:
                    return str(result[0])
            return None
        except ImportError:
            pass

        console.print("[dim]No database driver available (psycopg2 or sqlite3)[/dim]")
        return None

    except Exception as e:
        console.print(f"[dim]Database query failed: {e}[/dim]")
        return None


def _fetch_data_from_source(
    source_config: dict[str, Any],
    metric_id: str,
    provided_values: dict[str, str] | None = None,
    non_interactive: bool = False,
) -> dict[str, Any]:
    """
    Fetch data from a configured source.

    Attempts to fetch automatically based on source type.
    Falls back to manual input if automatic fetch fails.

    Args:
        source_config: Source configuration from skene.json
        metric_id: The metric identifier to fetch
        provided_values: Optional dict of metric_id -> value for non-interactive mode
        non_interactive: If True, raise error instead of prompting when value not provided

    Returns:
        Data point dict with timestamp, metric_id, value, source, and status
    """
    source_id = source_config.get("id", "unknown")
    source_type = source_config.get("type", "manual")

    value = None
    fetch_method = "manual"

    # Try automatic fetch based on source type
    if source_type == "api":
        console.print(f"[dim]Fetching '{metric_id}' from API source '{source_id}'...[/dim]")
        value = _fetch_from_api(source_config, metric_id)
        if value is not None:
            fetch_method = "api"
            console.print(f"[green]✓[/green] Got value from API: {value}")

    elif source_type == "database":
        console.print(f"[dim]Fetching '{metric_id}' from database source '{source_id}'...[/dim]")
        value = _fetch_from_database(source_config, metric_id)
        if value is not None:
            fetch_method = "database"
            console.print(f"[green]✓[/green] Got value from database: {value}")

    # Fallback to manual input if automatic fetch failed or source is manual type
    if value is None:
        if source_type == "manual":
            value = _prompt_for_manual_value(
                metric_id,
                source_id,
                provided_values=provided_values,
                non_interactive=non_interactive,
            )
        else:
            value = _prompt_for_manual_value(
                metric_id,
                source_id,
                reason=f"Could not fetch automatically from {source_type} source.",
                provided_values=provided_values,
                non_interactive=non_interactive,
            )
        fetch_method = "manual"
        # When manually entered, source is N/A
        source_id = "N/A"

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "metric_id": metric_id,
        "value": value,
        "source": source_id,
        "status": "verified",
        "fetch_method": fetch_method,
    }


def _get_daily_log_file_path(skene_context_path: Path, create_dir: bool = True) -> Path:
    """Get the path for today's daily log file.

    Args:
        skene_context_path: Path to skene-context directory
        create_dir: If True, create the daily_logs directory if it doesn't exist

    Returns:
        Path to today's daily log file
    """
    daily_logs_dir = skene_context_path / "daily_logs"
    if create_dir:
        daily_logs_dir.mkdir(parents=True, exist_ok=True)

    # Use UTC for consistency with timestamps
    today = datetime.utcnow()
    filename = f"daily_logs_{today.year:04d}_{today.month:02d}_{today.day:02d}.json"

    return daily_logs_dir / filename


def _get_existing_metric_ids(existing_data: list[dict[str, Any]]) -> set[str]:
    """Get set of metric IDs already present in existing data."""
    return {entry.get("metric_id") for entry in existing_data if isinstance(entry, dict) and entry.get("metric_id")}


def list_required_metrics(skene_context_path: Path | str | None = None) -> list[dict[str, Any]]:
    """
    List metrics that need values for today's daily log.

    This is useful for non-interactive mode to determine what values need to be provided.

    Args:
        skene_context_path: Path to skene-context directory. Defaults to ./skene-context

    Returns:
        List of dicts with metric_id, name, source_id, and target (if available)
    """
    # Determine skene-context path
    if skene_context_path is None:
        skene_context_path = Path("./skene-context")
    else:
        skene_context_path = Path(skene_context_path)

    if not skene_context_path.exists():
        raise FileNotFoundError(f"skene-context directory not found at {skene_context_path}")

    # Load growth objectives
    objectives = _load_growth_objectives(skene_context_path)

    if not objectives:
        return []

    # Get today's log file path (don't create directory for read-only operation)
    log_file_path = _get_daily_log_file_path(skene_context_path, create_dir=False)

    # Check existing data for deduplication
    existing_data: list[dict[str, Any]] = []
    if log_file_path.exists():
        try:
            loaded = _load_json_file(log_file_path)
            if isinstance(loaded, list):
                existing_data = loaded
        except Exception:
            pass

    existing_metric_ids = _get_existing_metric_ids(existing_data)

    # Build list of required metrics
    required_metrics = []
    for objective in objectives:
        if not isinstance(objective, dict):
            continue

        metric_id = objective.get("metric_id") or objective.get("id") or objective.get("name")
        if not metric_id:
            continue

        # Skip if already logged today
        if metric_id in existing_metric_ids:
            continue

        source_id = objective.get("source") or objective.get("source_id")

        required_metrics.append(
            {
                "metric_id": metric_id,
                "name": objective.get("name", metric_id),
                "source_id": source_id,
                "target": objective.get("target"),
            }
        )

    return required_metrics


def fetch_daily_logs(
    skene_context_path: Path | str | None = None,
    provided_values: dict[str, str] | None = None,
    non_interactive: bool = False,
) -> Path:
    """
    Fetch data from sources defined in skene.json and store in daily logs.

    This function:
    1. Optionally reads skene.json for source configurations (if exists)
    2. Reads growth objectives to determine what metrics to fetch
    3. For each objective:
       - If source found in skene.json, attempts automatic fetch (API/database)
       - If source not found or skene.json missing, prompts user for value directly
       - Falls back to manual input if automatic fetch fails
    4. Saves results to daily_logs/daily_logs_YYYY_MM_DD.json
    5. Skips metrics already logged today (deduplication)

    Args:
        skene_context_path: Path to skene-context directory. Defaults to ./skene-context
        provided_values: Optional dict mapping metric_id -> value for non-interactive mode
        non_interactive: If True, raise errors instead of prompting when values are missing

    Returns:
        Path to the created/updated daily log file

    Raises:
        FileNotFoundError: If growth objectives file is not found
        ValueError: If configuration is invalid or required values missing in non-interactive mode
    """
    # Determine skene-context path
    if skene_context_path is None:
        skene_context_path = Path("./skene-context")
    else:
        skene_context_path = Path(skene_context_path)

    if not skene_context_path.exists():
        if non_interactive:
            raise FileNotFoundError(f"skene-context directory not found at {skene_context_path}")
        console.print(f"[yellow]Warning:[/yellow] skene-context directory not found at {skene_context_path}")
        user_path = Prompt.ask("Path to skene-context directory", default=str(skene_context_path))
        skene_context_path = Path(user_path)

        if not skene_context_path.exists():
            raise FileNotFoundError(f"skene-context directory not found at {skene_context_path}")

    # Load configuration (optional - skene.json may not exist)
    skene_config = _load_skene_config(skene_context_path)
    if skene_config is None:
        console.print("[dim]skene.json not found - will prompt for values directly[/dim]")
    else:
        console.print("[bold]Loading configuration...[/bold]")

    # Load growth objectives
    console.print("[bold]Loading growth objectives...[/bold]")
    objectives = _load_growth_objectives(skene_context_path)

    # Get today's log file path
    log_file_path = _get_daily_log_file_path(skene_context_path)

    if not objectives:
        console.print("[yellow]Warning:[/yellow] No objectives found")
        # Create empty file if it doesn't exist
        if not log_file_path.exists():
            log_file_path.write_text("[]")
            console.print(f"[green]✓[/green] Created empty daily log file: {log_file_path}")
        return log_file_path

    # Check if file already exists and load existing data
    existing_data: list[dict[str, Any]] = []
    if log_file_path.exists():
        console.print(f"[dim]Loading existing log file: {log_file_path}[/dim]")
        try:
            loaded = _load_json_file(log_file_path)
            if isinstance(loaded, list):
                existing_data = loaded
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not load existing log file: {e}")

    # Get already logged metric IDs for deduplication
    existing_metric_ids = _get_existing_metric_ids(existing_data)

    # Fetch data for each objective
    console.print(f"[bold]Processing {len(objectives)} objectives...[/bold]")
    new_entries: list[dict[str, Any]] = []
    skipped_count = 0

    for objective in objectives:
        if not isinstance(objective, dict):
            console.print(f"[yellow]Warning:[/yellow] Skipping invalid objective: {objective}")
            continue

        # Get source ID and metric ID from objective
        source_id = objective.get("source") or objective.get("source_id")
        metric_id = objective.get("metric_id") or objective.get("id") or objective.get("name")

        if not metric_id:
            console.print(f"[yellow]Warning:[/yellow] Objective missing metric_id: {objective}")
            continue

        # Check for duplicate - skip if already logged today
        if metric_id in existing_metric_ids:
            console.print(f"[dim]Skipping '{metric_id}' - already logged today[/dim]")
            skipped_count += 1
            continue

        # Try to get source configuration from skene.json if available
        source_config = None
        if skene_config and source_id:
            source_config = _get_source_config(source_id, skene_config)

        # If no skene.json or source not found, prompt directly for value
        if source_config is None:
            if source_id:
                console.print(f"[dim]Source '{source_id}' not found in skene.json - manual entry[/dim]")
            else:
                console.print("[dim]No source specified - manual entry[/dim]")

            # Get example from objective if available (from Target field)
            example = objective.get("target")
            value = _prompt_for_manual_value(
                metric_id,
                source_id,
                example=example,
                provided_values=provided_values,
                non_interactive=non_interactive,
            )
            entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "metric_id": metric_id,
                "value": value,
                "source": "N/A",
                "status": "verified",
                "fetch_method": "manual",
            }
        else:
            # Fetch data from source (with manual fallback)
            entry = _fetch_data_from_source(source_config, metric_id, provided_values, non_interactive)

        new_entries.append(entry)
        console.print(f"[green]✓[/green] Logged metric '{metric_id}': {entry['value']}")

    # Combine existing and new entries
    all_entries = existing_data + new_entries

    # Write to file
    console.print(f"[bold]Writing to {log_file_path}...[/bold]")
    with open(log_file_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2, ensure_ascii=False)

    console.print(f"[green]✓[/green] Daily logs saved to: {log_file_path}")
    console.print(f"[green]✓[/green] Added {len(new_entries)} new entries")
    if skipped_count > 0:
        console.print(f"[dim]Skipped {skipped_count} already logged metrics[/dim]")

    return log_file_path
