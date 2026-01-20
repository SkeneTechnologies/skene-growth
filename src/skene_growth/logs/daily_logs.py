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


def _load_skene_config(skene_context_path: Path) -> dict[str, Any]:
    """Load skene.json configuration file."""
    skene_json_path = skene_context_path / "skene.json"
    
    if not skene_json_path.exists():
        console.print(f"[yellow]Warning:[/yellow] skene.json not found at {skene_json_path}")
        console.print("Please provide the path to skene.json:")
        user_path = Prompt.ask("Path to skene.json", default=str(skene_json_path))
        skene_json_path = Path(user_path)
        
        if not skene_json_path.exists():
            raise FileNotFoundError(f"skene.json not found at {skene_json_path}")
    
    return _load_json_file(skene_json_path)


def _load_growth_objectives(skene_context_path: Path) -> list[dict[str, Any]]:
    """Load growth objectives file."""
    # Try common names for growth objectives file
    possible_names = [
        "growth-objectives.json",
        "growth_objectives.json",
        "growth-objectives",
        "growth_objectives",
    ]
    
    objectives_path = None
    for name in possible_names:
        candidate = skene_context_path / name
        if candidate.exists():
            objectives_path = candidate
            break
    
    if objectives_path is None:
        console.print(f"[yellow]Warning:[/yellow] Growth objectives file not found in {skene_context_path}")
        console.print("Please provide the path to growth objectives file:")
        user_path = Prompt.ask("Path to growth objectives file")
        objectives_path = Path(user_path)
        
        if not objectives_path.exists():
            raise FileNotFoundError(f"Growth objectives file not found at {objectives_path}")
    
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


def _prompt_for_source_config(source_id: str) -> dict[str, Any]:
    """Prompt user for source configuration when not found in skene.json."""
    console.print(f"[yellow]Source '{source_id}' not found in skene.json[/yellow]")
    console.print("Please provide source configuration:")
    
    source_type = Prompt.ask("Source type (api, database, manual)", default="manual")
    
    config = {
        "id": source_id,
        "type": source_type,
    }
    
    if source_type == "api":
        config["url"] = Prompt.ask("API URL/endpoint")
        source_auth = Prompt.ask("Authentication method (api_key, bearer, none)", default="none")
        config["auth"] = source_auth
        
        if source_auth == "api_key":
            config["api_key"] = Prompt.ask("API key", password=True)
            config["api_key_header"] = Prompt.ask("API key header name", default="X-API-Key")
        elif source_auth == "bearer":
            config["bearer_token"] = Prompt.ask("Bearer token", password=True)
        
        # Optional: JSON path to extract value from response
        config["value_path"] = Prompt.ask("JSON path to value (e.g., 'data.count' or leave empty)", default="")
    
    elif source_type == "database":
        config["connection_string"] = Prompt.ask("Database connection string", password=True)
        config["query"] = Prompt.ask("SQL query to fetch value")
    
    return config


def _prompt_for_manual_value(metric_id: str, source_id: str, reason: str = "") -> float:
    """Prompt user to manually enter a metric value."""
    if reason:
        console.print(f"[yellow]{reason}[/yellow]")
    console.print(f"Please enter the value for metric '[bold]{metric_id}[/bold]' (source: {source_id}):")
    
    while True:
        value_str = Prompt.ask("Value")
        try:
            return float(value_str)
        except ValueError:
            console.print("[red]Invalid number. Please enter a numeric value.[/red]")


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


def _fetch_from_api(source_config: dict[str, Any], metric_id: str) -> float | None:
    """Fetch data from an API source."""
    url = source_config.get("url")
    if not url:
        return None
    
    # Build headers
    headers = {}
    auth_type = source_config.get("auth", "none")
    
    if auth_type == "api_key":
        api_key = source_config.get("api_key") or os.environ.get(f"SKENE_SOURCE_{source_config.get('id', '').upper()}_API_KEY")
        header_name = source_config.get("api_key_header", "X-API-Key")
        if api_key:
            headers[header_name] = api_key
    elif auth_type == "bearer":
        token = source_config.get("bearer_token") or os.environ.get(f"SKENE_SOURCE_{source_config.get('id', '').upper()}_TOKEN")
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
                return float(value)
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


def _fetch_from_database(source_config: dict[str, Any], metric_id: str) -> float | None:
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
                return float(result[0])
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
                    return float(result[0])
            return None
        except ImportError:
            pass
        
        console.print("[dim]No database driver available (psycopg2 or sqlite3)[/dim]")
        return None
        
    except Exception as e:
        console.print(f"[dim]Database query failed: {e}[/dim]")
        return None


def _fetch_data_from_source(source_config: dict[str, Any], metric_id: str) -> dict[str, Any]:
    """
    Fetch data from a configured source.
    
    Attempts to fetch automatically based on source type.
    Falls back to manual input if automatic fetch fails.
    
    Args:
        source_config: Source configuration from skene.json
        metric_id: The metric identifier to fetch
    
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
            value = _prompt_for_manual_value(metric_id, source_id)
        else:
            value = _prompt_for_manual_value(
                metric_id, 
                source_id, 
                reason=f"Could not fetch automatically from {source_type} source."
            )
        fetch_method = "manual"
    
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "metric_id": metric_id,
        "value": value,
        "source": source_id,
        "status": "verified",
        "fetch_method": fetch_method,
    }


def _get_daily_log_file_path(skene_context_path: Path) -> Path:
    """Get the path for today's daily log file."""
    daily_logs_dir = skene_context_path / "daily_logs"
    daily_logs_dir.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now()
    filename = f"daily_logs_{today.year:04d}_{today.month:02d}_{today.day:02d}.json"
    
    return daily_logs_dir / filename


def _get_existing_metric_ids(existing_data: list[dict[str, Any]]) -> set[str]:
    """Get set of metric IDs already present in existing data."""
    return {entry.get("metric_id") for entry in existing_data if isinstance(entry, dict) and entry.get("metric_id")}


def fetch_daily_logs(skene_context_path: Path | str | None = None) -> Path:
    """
    Fetch data from sources defined in skene.json and store in daily logs.
    
    This function:
    1. Reads skene.json for source configurations
    2. Reads growth objectives to determine what metrics to fetch
    3. For each objective, attempts to fetch from configured source
    4. Falls back to manual input if automatic fetch fails
    5. Saves results to daily_logs/daily_logs_YYYY_MM_DD.json
    6. Skips metrics already logged today (deduplication)
    
    Args:
        skene_context_path: Path to skene-context directory. Defaults to ./skene-context
    
    Returns:
        Path to the created/updated daily log file
    
    Raises:
        FileNotFoundError: If required files are not found
        ValueError: If configuration is invalid
    """
    # Determine skene-context path
    if skene_context_path is None:
        skene_context_path = Path("./skene-context")
    else:
        skene_context_path = Path(skene_context_path)
    
    if not skene_context_path.exists():
        console.print(f"[yellow]Warning:[/yellow] skene-context directory not found at {skene_context_path}")
        user_path = Prompt.ask("Path to skene-context directory", default=str(skene_context_path))
        skene_context_path = Path(user_path)
        
        if not skene_context_path.exists():
            raise FileNotFoundError(f"skene-context directory not found at {skene_context_path}")
    
    # Load configuration
    console.print("[bold]Loading configuration...[/bold]")
    skene_config = _load_skene_config(skene_context_path)
    
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
        
        # Get source ID from objective
        source_id = objective.get("source") or objective.get("source_id")
        metric_id = objective.get("metric_id") or objective.get("id") or objective.get("name")
        
        if not source_id:
            console.print(f"[yellow]Warning:[/yellow] Objective missing source: {objective}")
            continue
        
        if not metric_id:
            console.print(f"[yellow]Warning:[/yellow] Objective missing metric_id: {objective}")
            continue
        
        # Check for duplicate - skip if already logged today
        if metric_id in existing_metric_ids:
            console.print(f"[dim]Skipping '{metric_id}' - already logged today[/dim]")
            skipped_count += 1
            continue
        
        # Get source configuration
        source_config = _get_source_config(source_id, skene_config)
        
        if source_config is None:
            # Prompt user for source configuration
            source_config = _prompt_for_source_config(source_id)
        
        # Fetch data from source (with manual fallback)
        entry = _fetch_data_from_source(source_config, metric_id)
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
