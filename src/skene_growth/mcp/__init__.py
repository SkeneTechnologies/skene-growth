"""MCP (Model Context Protocol) server for skene-growth.

This module provides an MCP server that exposes skene-growth functionality
to AI assistants like Claude, GPT, and others.

Usage:
    # Run the MCP server
    skene-growth-mcp

    # Or via Python
    python -m skene_growth.mcp
"""


# Lazy imports to avoid requiring mcp package when importing other mcp modules
def __getattr__(name: str):
    """Lazy import for MCP server functions."""
    if name in ("main", "serve"):
        from skene_growth.mcp.server import main, serve

        return main if name == "main" else serve
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["main", "serve"]
