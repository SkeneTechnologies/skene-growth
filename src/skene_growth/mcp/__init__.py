"""MCP (Model Context Protocol) server for skene-growth.

This module provides an MCP server that exposes skene-growth functionality
to AI assistants like Claude, GPT, and others.

Usage:
    # Run the MCP server
    skene-growth-mcp

    # Or via Python
    python -m skene_growth.mcp
"""

from skene_growth.mcp.server import main, serve

__all__ = ["main", "serve"]
