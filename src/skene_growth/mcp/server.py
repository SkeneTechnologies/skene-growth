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
from skene_growth.mcp.tools import (
    analyze_features,
    analyze_growth_hubs,
    analyze_industry,
    analyze_product_overview,
    analyze_tech_stack,
    clear_cache,
    generate_growth_template_tool,
    generate_manifest,
    get_codebase_overview,
    get_manifest,
    search_codebase,
    write_analysis_outputs,
)

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
                # =============================================================
                # Tier 1: Quick Tools
                # =============================================================
                Tool(
                    name="get_codebase_overview",
                    description=(
                        "Get a quick overview of a codebase structure (<1s). "
                        "Returns directory tree, file counts by extension, and detected config files. "
                        "Use this first to understand the project structure before deeper analysis."
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
                    name="search_codebase",
                    description=(
                        "Search for files matching a glob pattern (<1s). "
                        "Use patterns like '**/*.py' for Python files or 'src/**/*.ts' for TypeScript in src."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the repository",
                            },
                            "pattern": {
                                "type": "string",
                                "description": "Glob pattern (e.g., '**/*.py', 'src/**/*.ts')",
                            },
                            "directory": {
                                "type": "string",
                                "description": "Subdirectory to search in (default: '.')",
                                "default": ".",
                            },
                        },
                        "required": ["path", "pattern"],
                    },
                ),
                # =============================================================
                # Tier 2: Analysis Phase Tools (uses LLM)
                # =============================================================
                Tool(
                    name="analyze_tech_stack",
                    description=(
                        "Analyze the technology stack of a codebase (5-15s). "
                        "Detects framework, language, database, authentication, and deployment. "
                        "Results are cached independently."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the repository",
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
                    name="analyze_product_overview",
                    description=(
                        "Extract product overview from README and documentation (5-15s). "
                        "Returns product name, tagline, description, value proposition. "
                        "Results are cached independently."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the repository",
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
                    name="analyze_growth_hubs",
                    description=(
                        "Identify growth hubs (viral/growth features) in the codebase (5-15s). "
                        "Finds features like invitations, sharing, referrals, payments. "
                        "Results are cached independently."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the repository",
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
                    name="analyze_features",
                    description=(
                        "Document user-facing features from the codebase (5-15s). "
                        "Extracts feature information from source files. "
                        "Results are cached independently."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the repository",
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
                    name="analyze_industry",
                    description=(
                        "Classify the industry/market vertical of a codebase (5-15s). "
                        "Analyzes README and documentation to determine the product's industry, "
                        "sub-verticals, and business model tags. "
                        "Results are cached independently."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the repository",
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
                # =============================================================
                # Tier 3: Generation Tools
                # =============================================================
                Tool(
                    name="generate_manifest",
                    description=(
                        "Generate a GrowthManifest from cached analysis results (5-15s). "
                        "IMPORTANT: Call analyze_tech_stack and analyze_growth_hubs FIRST to populate the cache. "
                        "For product_docs=true, also call analyze_product_overview and analyze_features first. "
                        "This tool combines the cached phase results into the final manifest."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the repository",
                            },
                            "product_docs": {
                                "type": "boolean",
                                "description": "Generate DocsManifest v2.0 with product documentation",
                                "default": False,
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
                    name="generate_growth_template",
                    description=(
                        "Generate a PLG growth template from a manifest (5-15s). "
                        "Creates a custom template with lifecycle stages, milestones, and metrics. "
                        "Results are cached independently."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the repository",
                            },
                            "business_type": {
                                "type": "string",
                                "description": (
                                    "Business type hint (e.g., 'b2b-saas', 'marketplace'). "
                                    "LLM will infer if not provided."
                                ),
                            },
                            "force_refresh": {
                                "type": "boolean",
                                "description": "Skip cache and force re-generation",
                                "default": False,
                            },
                        },
                        "required": ["path"],
                    },
                ),
                Tool(
                    name="write_analysis_outputs",
                    description=(
                        "Write analysis outputs to disk (<1s). "
                        "Writes growth-manifest.json, and optionally "
                        "product-docs.md, growth-template.json. "
                        "IMPORTANT: Run generate_manifest and generate_growth_template FIRST "
                        "to populate the cache before calling this tool."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the repository",
                            },
                            "product_docs": {
                                "type": "boolean",
                                "description": "Generate product-docs.md",
                                "default": False,
                            },
                        },
                        "required": ["path"],
                    },
                ),
                # =============================================================
                # Utility Tools
                # =============================================================
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
                                "description": ("Path to clear cache for. If not provided, clears all cache."),
                            },
                        },
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> Any:
            """Handle tool calls."""
            try:
                cache = self.cache if self.cache_enabled else _NoOpCache()

                # Tier 1: Quick Tools
                if name == "get_codebase_overview":
                    result = await get_codebase_overview(path=arguments["path"])

                elif name == "search_codebase":
                    result = await search_codebase(
                        path=arguments["path"],
                        pattern=arguments["pattern"],
                        directory=arguments.get("directory", "."),
                    )

                # Tier 2: Analysis Phase Tools
                elif name == "analyze_tech_stack":
                    result = await analyze_tech_stack(
                        path=arguments["path"],
                        cache=cache,
                        force_refresh=arguments.get("force_refresh", False),
                    )

                elif name == "analyze_product_overview":
                    result = await analyze_product_overview(
                        path=arguments["path"],
                        cache=cache,
                        force_refresh=arguments.get("force_refresh", False),
                    )

                elif name == "analyze_growth_hubs":
                    result = await analyze_growth_hubs(
                        path=arguments["path"],
                        cache=cache,
                        force_refresh=arguments.get("force_refresh", False),
                    )

                elif name == "analyze_features":
                    result = await analyze_features(
                        path=arguments["path"],
                        cache=cache,
                        force_refresh=arguments.get("force_refresh", False),
                    )

                elif name == "analyze_industry":
                    result = await analyze_industry(
                        path=arguments["path"],
                        cache=cache,
                        force_refresh=arguments.get("force_refresh", False),
                    )

                # Tier 3: Generation Tools
                elif name == "generate_manifest":
                    result = await generate_manifest(
                        path=arguments["path"],
                        cache=cache,
                        auto_analyze=False,  # Require phase tools to be called first
                        product_docs=arguments.get("product_docs", False),
                        force_refresh=arguments.get("force_refresh", False),
                    )

                elif name == "generate_growth_template":
                    result = await generate_growth_template_tool(
                        path=arguments["path"],
                        cache=cache,
                        business_type=arguments.get("business_type"),
                        force_refresh=arguments.get("force_refresh", False),
                    )

                elif name == "write_analysis_outputs":
                    result = await write_analysis_outputs(
                        path=arguments["path"],
                        cache=cache,
                        product_docs=arguments.get("product_docs", False),
                    )

                # Utility Tools
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

    async def get_phase(self, *args, **kwargs):
        return None

    async def set_phase(self, *args, **kwargs):
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
