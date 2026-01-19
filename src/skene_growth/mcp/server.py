"""MCP server for skene-growth.

This module provides an MCP server that exposes skene-growth analysis
capabilities to AI assistants.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from skene_growth import __version__
from skene_growth.mcp.cache import AnalysisCache
from skene_growth.mcp.tools import analyze_codebase, clear_cache, get_manifest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_cache_dir() -> Path:
    """Get cache directory from environment or default."""
    cache_dir = os.environ.get("SKENE_CACHE_DIR")
    if cache_dir:
        return Path(cache_dir)
    return Path.home() / ".cache" / "skene-growth-mcp"


def _get_cache_ttl() -> int:
    """Get cache TTL from environment or default."""
    try:
        return int(os.environ.get("SKENE_CACHE_TTL", "3600"))
    except ValueError:
        return 3600


def _is_cache_enabled() -> bool:
    """Check if caching is enabled."""
    value = os.environ.get("SKENE_CACHE_ENABLED", "true")
    return value.lower() in ("true", "1", "yes")


class SkeneGrowthMCPServer:
    """MCP server for skene-growth codebase analysis."""

    def __init__(self) -> None:
        """Initialize the server."""
        self.server = Server("skene-growth")
        self.cache = AnalysisCache(
            cache_dir=_get_cache_dir(),
            ttl=_get_cache_ttl(),
        )
        self.cache_enabled = _is_cache_enabled()
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="analyze_codebase",
                    description=(
                        "Analyze a codebase for growth opportunities using skene-growth. "
                        "Detects tech stack, growth hubs (features with growth potential), "
                        "and GTM gaps (missing features). Generates growth-manifest.json, "
                        "markdown summary, and growth template. "
                        "With product_docs=true, also generates user-facing documentation."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the repository to analyze",
                            },
                            "product_docs": {
                                "type": "boolean",
                                "description": (
                                    "Generate v2.0 manifest with product documentation. "
                                    "Includes product overview, features, and generates product-docs.md"
                                ),
                                "default": False,
                            },
                            "business_type": {
                                "type": "string",
                                "description": (
                                    "Business type hint for growth template "
                                    "(e.g., 'b2b-saas', 'marketplace', 'dev-tools'). "
                                    "LLM will infer if not provided."
                                ),
                            },
                            "force_refresh": {
                                "type": "boolean",
                                "description": "Skip cache and force re-analysis",
                                "default": False,
                            },
                        },
                        "required": ["path"],
                    },
                ),
                Tool(
                    name="get_manifest",
                    description=(
                        "Retrieve an existing growth manifest from disk without re-analyzing. "
                        "Use this when you just need to read a previously generated manifest."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the repository",
                            },
                        },
                        "required": ["path"],
                    },
                ),
                Tool(
                    name="clear_cache",
                    description=(
                        "Clear cached analysis results. Useful when you want to force "
                        "fresh analysis or troubleshoot caching issues."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": (
                                    "Path to clear cache for. If not provided, clears all cache."
                                ),
                            },
                        },
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> Any:
            """Handle tool calls."""
            try:
                if name == "analyze_codebase":
                    result = await analyze_codebase(
                        path=arguments["path"],
                        cache=self.cache if self.cache_enabled else _NoOpCache(),
                        product_docs=arguments.get("product_docs", False),
                        business_type=arguments.get("business_type"),
                        force_refresh=arguments.get("force_refresh", False),
                    )
                elif name == "get_manifest":
                    result = await get_manifest(path=arguments["path"])
                elif name == "clear_cache":
                    result = await clear_cache(
                        cache=self.cache,
                        path=arguments.get("path"),
                    )
                else:
                    return [{"type": "text", "text": f"Unknown tool: {name}", "isError": True}]

                return [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]

            except Exception as e:
                error_msg = str(e)
                return [{"type": "text", "text": f"Error: {error_msg}", "isError": True}]


class _NoOpCache:
    """No-op cache for when caching is disabled."""

    async def get(self, *args, **kwargs):
        return None

    async def set(self, *args, **kwargs):
        pass

    async def clear(self, *args, **kwargs):
        return 0


async def serve() -> None:
    """Run the MCP server."""
    logger.info(f"Starting skene-growth MCP server v{__version__}")

    server = SkeneGrowthMCPServer()

    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            server.server.create_initialization_options(),
        )


def main() -> None:
    """Main entry point."""
    import asyncio

    asyncio.run(serve())


if __name__ == "__main__":
    main()
