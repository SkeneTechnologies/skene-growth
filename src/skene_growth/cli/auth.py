"""
Upstream authentication for skene deploy push.

Uses interactive login (masked token input) to avoid tokens in shell history.
"""

import getpass
import sys
from pathlib import Path

import typer
from rich.console import Console

from skene_growth.config import get_credentials_path, load_config
from skene_growth.growth_loops.upstream import validate_token, _api_base_from_upstream

console = Console()


def _set_credentials_permissions(path: Path) -> None:
    """Set restrictive permissions (0o600) on credentials file."""
    if sys.platform != "win32":
        try:
            path.chmod(0o600)
        except (OSError, PermissionError):
            pass


def cmd_login(upstream_url: str | None = None) -> None:
    """
    Interactive login for upstream push.

    Prompts for API token (masked), validates via GET /me, saves to credentials file.
    """
    config = load_config()
    url = upstream_url or config.upstream
    if not url:
        console.print(
            "[red]Error:[/red] No upstream URL configured.\n"
            "Set via --upstream or add to config:\n"
            '  upstream = "https://skene.ai/workspace/your-workspace"'
        )
        raise typer.Exit(1)

    api_base = _api_base_from_upstream(url)
    console.print(
        "[dim]Create a token at https://skene.ai/settings/tokens[/dim]"
        if "skene.ai" in url
        else "[dim]Obtain an API token from your upstream provider.[/dim]"
    )
    token = getpass.getpass("Paste your API Token: ")

    if not token or not token.strip():
        console.print("[red]No token provided. Login cancelled.[/red]")
        raise typer.Exit(1)

    if not validate_token(api_base, token.strip()):
        console.print("[red]Invalid token or connection failed.[/red]")
        raise typer.Exit(1)

    cred_path = get_credentials_path()
    cred_path.parent.mkdir(parents=True, exist_ok=True)
    raw = token.strip()
    escaped = raw.replace("\\", "\\\\").replace('"', '\\"')
    cred_path.write_text(f'token = "{escaped}"\n', encoding="utf-8")
    _set_credentials_permissions(cred_path)

    console.print("[green]Successfully logged in.[/green]")


def cmd_logout() -> None:
    """Remove saved upstream token from credentials file."""
    cred_path = get_credentials_path()
    if cred_path.exists():
        cred_path.unlink()
        console.print("[green]Logged out. Token removed.[/green]")
    else:
        console.print("[dim]No saved credentials found.[/dim]")
