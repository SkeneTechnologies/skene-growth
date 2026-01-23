"""
Daily logs management for tracking growth metrics.

Reads skene.json configuration and growth-objectives.md to fetch and store
daily metric values.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger


def _load_skene_config(context_path: Path) -> dict[str, Any]:
    """Load skene.json configuration file."""
    skene_path = context_path / "skene.json"
    
    if not skene_path.exists():
        # Create a default skene.json with example structure
        default_config = {
            "sources": [
                {
                    "name": "example_api",
                    "type": "api",
                    "endpoint": "https://api.example.com/metrics",
                    "auth": {
                        "type": "bearer",
                        "token_env": "API_TOKEN"
                    },
                    "comment": "Replace with your actual data source configuration"
                }
            ],
            "objectives": [],
            "config": {
                "timeout": 30,
                "retries": 3,
                "comment": "Optional: Configure timeout and retry settings"
            }
        }
        skene_path.parent.mkdir(parents=True, exist_ok=True)
        skene_path.write_text(json.dumps(default_config, indent=2))
        logger.info(f"Created default skene.json at {skene_path}")
        return default_config
    
    try:
        return json.loads(skene_path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in skene.json: {e}")


def _load_objectives(context_path: Path) -> list[dict[str, Any]]:
    """Load and parse growth-objectives.md file."""
    objectives_paths = [
        context_path / "growth-objectives.md",
        Path("./growth-objectives.md"),
    ]
    
    objectives_path = None
    for path in objectives_paths:
        if path.exists():
            objectives_path = path
            break
    
    if not objectives_path:
        raise FileNotFoundError(
            f"growth-objectives.md not found. Run 'skene-growth objectives' first. "
            f"Checked: {[str(p) for p in objectives_paths]}"
        )
    
    content = objectives_path.read_text()
    
    # Parse markdown objectives
    objectives = []
    current_objective = None
    
    for line in content.split("\n"):
        # Lifecycle header: ## LIFECYCLE_NAME
        lifecycle_match = re.match(r"^##\s+(.+)$", line)
        if lifecycle_match:
            if current_objective:
                objectives.append(current_objective)
            current_objective = {
                "lifecycle": lifecycle_match.group(1).strip(),
                "metric": None,
                "target": None,
                "tolerance": None,
            }
            continue
        
        # Metric: - **Metric:** Metric Name
        metric_match = re.match(r"^-\s+\*\*Metric:\*\*\s+(.+)$", line)
        if metric_match and current_objective:
            current_objective["metric"] = metric_match.group(1).strip()
            continue
        
        # Target: - **Target:** Target Value
        target_match = re.match(r"^-\s+\*\*Target:\*\*\s+(.+)$", line)
        if target_match and current_objective:
            current_objective["target"] = target_match.group(1).strip()
            continue
        
        # Tolerance: - **Tolerance:** Tolerance Range
        tolerance_match = re.match(r"^-\s+\*\*Tolerance:\*\*\s+(.+)$", line)
        if tolerance_match and current_objective:
            current_objective["tolerance"] = tolerance_match.group(1).strip()
            continue
    
    # Add last objective
    if current_objective:
        objectives.append(current_objective)
    
    if not objectives:
        raise ValueError("No objectives found in growth-objectives.md")
    
    return objectives


def _get_today_log_path(context_path: Path) -> Path:
    """Get the path for today's log file."""
    today = datetime.now().strftime("%Y_%m_%d")
    daily_logs_dir = context_path / "daily_logs"
    daily_logs_dir.mkdir(parents=True, exist_ok=True)
    return daily_logs_dir / f"daily_logs_{today}.json"


def _load_today_log(context_path: Path) -> dict[str, Any]:
    """Load today's log file if it exists."""
    log_path = _get_today_log_path(context_path)
    if log_path.exists():
        try:
            return json.loads(log_path.read_text())
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in {log_path}, starting fresh")
            return {}
    return {}


def _generate_metric_id(lifecycle: str, metric: str) -> str:
    """Generate a unique metric ID from lifecycle and metric name."""
    # Create a simple ID: lowercase, replace spaces with underscores
    lifecycle_clean = lifecycle.lower().replace(" ", "_")
    metric_clean = metric.lower().replace(" ", "_")
    return f"{lifecycle_clean}_{metric_clean}"


def list_required_metrics(context_path: Path) -> list[dict[str, Any]]:
    """
    List metrics that need values (haven't been logged today).
    
    Args:
        context_path: Path to skene-context directory
        
    Returns:
        List of metric dictionaries with metric_id, name, source_id, target
    """
    try:
        objectives = _load_objectives(context_path)
        today_log = _load_today_log(context_path)
        skene_config = _load_skene_config(context_path)
        
        # Build a map of source names (use name as id, or id if present)
        sources_map = {}
        for source in skene_config.get("sources", []):
            source_name = source.get("name")
            source_id = source.get("id") or source_name  # Use id if present, otherwise name
            if source_name:
                sources_map[source_name] = source_id
        
        required_metrics = []
        
        for obj in objectives:
            metric_id = _generate_metric_id(obj["lifecycle"], obj["metric"])
            
            # Check if already logged today
            if metric_id in today_log.get("metrics", {}):
                continue
            
            # Find source_id if available (match by source name in metric or objective)
            source_id = None
            metric_name = obj.get("metric", "").lower()
            for source_name, source_id_val in sources_map.items():
                if source_name.lower() in metric_name:
                    source_id = source_id_val
                    break
            
            required_metrics.append({
                "metric_id": metric_id,
                "name": obj["metric"],
                "lifecycle": obj["lifecycle"],
                "target": obj.get("target"),
                "tolerance": obj.get("tolerance"),
                "source_id": source_id,
            })
        
        return required_metrics
    
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.error(f"Error listing required metrics: {e}")
        raise


def _prompt_for_metric_value(metric: dict[str, Any]) -> str | None:
    """Prompt user for a metric value interactively."""
    from rich.console import Console
    
    console = Console()
    
    lifecycle = metric.get("lifecycle", "Unknown")
    metric_name = metric.get("name", "Unknown")
    target = metric.get("target", "TBD")
    
    console.print(f"\n[cyan]Lifecycle:[/cyan] {lifecycle}")
    console.print(f"[cyan]Metric:[/cyan] {metric_name}")
    console.print(f"[cyan]Target:[/cyan] {target}")
    
    try:
        value = input(f"Enter value for {metric_name}: ").strip()
        if not value:
            return None
        return value
    except (EOFError, KeyboardInterrupt):
        # Handle Ctrl+C or EOF gracefully
        console.print("\n[yellow]Cancelled[/yellow]")
        return None


def _fetch_from_source(source: dict[str, Any], metric: dict[str, Any]) -> str | None:
    """
    Fetch metric value from a configured source.
    
    Args:
        source: Source configuration from skene.json
        metric: Metric configuration from objectives
        
    Returns:
        Metric value as string, or None if fetch failed
    """
    source_type = source.get("type", "").lower()
    
    if source_type == "api":
        # TODO: Implement API fetching
        logger.warning(f"API source fetching not yet implemented for {source.get('name')}")
        return None
    elif source_type == "database":
        # TODO: Implement database querying
        logger.warning(f"Database source fetching not yet implemented for {source.get('name')}")
        return None
    elif source_type == "file":
        # TODO: Implement file reading
        logger.warning(f"File source fetching not yet implemented for {source.get('name')}")
        return None
    
    return None


def fetch_daily_logs(
    context_path: Path,
    provided_values: dict[str, str] | None = None,
    non_interactive: bool = False,
) -> Path | None:
    """
    Fetch data from sources and store in daily logs.
    
    Args:
        context_path: Path to skene-context directory
        provided_values: Optional dict of metric_id -> value (for non-interactive mode)
        non_interactive: If True, don't prompt for missing values
        
    Returns:
        Path to the created log file, or None if no data was fetched
    """
    try:
        # Load configuration and objectives
        skene_config = _load_skene_config(context_path)
        objectives = _load_objectives(context_path)
        today_log = _load_today_log(context_path)
        
        # Initialize metrics dict if not present
        if "metrics" not in today_log:
            today_log["metrics"] = {}
        
        if "date" not in today_log:
            today_log["date"] = datetime.now().strftime("%Y-%m-%d")
        
        sources = {source.get("name"): source for source in skene_config.get("sources", [])}
        metrics_logged = 0
        
        # Process each objective
        for obj in objectives:
            metric_id = _generate_metric_id(obj["lifecycle"], obj["metric"])
            
            # Skip if already logged
            if metric_id in today_log["metrics"]:
                continue
            
            value = None
            
            # Try provided values first (non-interactive mode)
            if provided_values and metric_id in provided_values:
                value = provided_values[metric_id]
            
            # Try fetching from source
            if not value:
                # Find matching source (simplified - could be improved)
                source_name = None
                for name in sources.keys():
                    if name.lower() in obj.get("metric", "").lower():
                        source_name = name
                        break
                
                if source_name:
                    source = sources[source_name]
                    value = _fetch_from_source(source, obj)
            
            # Prompt interactively if still no value and not non-interactive
            if not value and not non_interactive:
                metric_dict = {
                    "metric_id": metric_id,
                    "name": obj["metric"],
                    "lifecycle": obj["lifecycle"],
                    "target": obj.get("target"),
                    "tolerance": obj.get("tolerance"),
                }
                value = _prompt_for_metric_value(metric_dict)
            
            # Store value if we have one
            if value:
                today_log["metrics"][metric_id] = {
                    "value": value,
                    "lifecycle": obj["lifecycle"],
                    "metric": obj["metric"],
                    "target": obj.get("target"),
                    "tolerance": obj.get("tolerance"),
                    "timestamp": datetime.now().isoformat(),
                }
                metrics_logged += 1
        
        # Save log file if we logged any metrics
        if metrics_logged > 0:
            log_path = _get_today_log_path(context_path)
            log_path.write_text(json.dumps(today_log, indent=2))
            logger.info(f"Logged {metrics_logged} metrics to {log_path}")
            return log_path
        else:
            logger.info("No new metrics to log")
            return None
    
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.error(f"Error fetching daily logs: {e}")
        raise
