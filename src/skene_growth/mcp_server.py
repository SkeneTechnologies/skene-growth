"""
MCP Server for Skene Growth Scanner (Layer -1)

Exposes:
- Tech debt analysis
- Dead code detection
- Entropy analysis
- Complexity indexing (AICC)
- Growth manifest generation
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Initialize MCP server
app = Server("skene-growth-scanner")


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="skene://growth-manifest/latest",
            name="Growth Manifest (Latest)",
            description="Latest growth manifest from scanner",
            mimeType="application/json",
        ),
        Resource(
            uri="skene://tech-debt/latest",
            name="Tech Debt Report (Latest)",
            description="Latest technical debt analysis",
            mimeType="application/json",
        ),
        Resource(
            uri="skene://dead-code/latest",
            name="Dead Code Report (Latest)",
            description="Latest dead code detection results",
            mimeType="application/json",
        ),
        Resource(
            uri="skene://entropy/latest",
            name="Entropy Report (Latest)",
            description="Latest structural entropy analysis",
            mimeType="application/json",
        ),
        Resource(
            uri="skene://complexity/latest",
            name="Complexity Report (Latest)",
            description="Latest AICC complexity analysis",
            mimeType="application/json",
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content"""
    if uri == "skene://growth-manifest/latest":
        manifest_path = Path.cwd() / "growth-manifest-skene.json"
        if manifest_path.exists():
            return manifest_path.read_text()
        return json.dumps({"error": "No manifest available"})

    if uri == "skene://tech-debt/latest":
        report_path = Path.cwd() / "tech-debt-report.json"
        if report_path.exists():
            return report_path.read_text()
        return json.dumps({"error": "No tech debt report available"})

    if uri == "skene://dead-code/latest":
        report_path = Path.cwd() / "dead-code-report.json"
        if report_path.exists():
            return report_path.read_text()
        return json.dumps({"error": "No dead code report available"})

    if uri == "skene://entropy/latest":
        report_path = Path.cwd() / "entropy-report.json"
        if report_path.exists():
            return report_path.read_text()
        return json.dumps({"error": "No entropy report available"})

    if uri == "skene://complexity/latest":
        report_path = Path.cwd() / "complexity-report.json"
        if report_path.exists():
            return report_path.read_text()
        return json.dumps({"error": "No complexity report available"})

    raise ValueError(f"Unknown resource: {uri}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="analyze_tech_debt",
            description="Analyze technical debt in codebase",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to analyze (default: current directory)",
                    },
                    "quick_check": {
                        "type": "boolean",
                        "description": "Run quick static analysis without LLM",
                    },
                },
            },
        ),
        Tool(
            name="detect_dead_code",
            description="Detect unused code and imports",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to analyze (default: current directory)",
                    },
                    "quick_check": {
                        "type": "boolean",
                        "description": "Run quick regex-based detection",
                    },
                },
            },
        ),
        Tool(
            name="analyze_entropy",
            description="Analyze structural entropy and code organization",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to analyze (default: current directory)",
                    },
                },
            },
        ),
        Tool(
            name="analyze_complexity",
            description="Calculate AICC (AI-Component Complexity) metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to analyze (default: current directory)",
                    },
                },
            },
        ),
        Tool(
            name="generate_growth_manifest",
            description="Generate complete growth manifest with tech health",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to analyze (default: current directory)",
                    },
                    "include_tech_health": {
                        "type": "boolean",
                        "description": "Include technical health analysis",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Execute tool calls"""
    import subprocess

    def run_command(cmd: list[str]) -> str:
        """Run shell command and return output"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}\n{e.stdout}"

    if name == "analyze_tech_debt":
        path = arguments.get("path", ".")
        quick_check = arguments.get("quick_check", False)

        if quick_check:
            output = run_command(["node", "scripts/quick-tech-debt-check.ts", path])
        else:
            output = run_command([
                "python", "-m", "skene_growth.cli",
                "tech-debt", path,
                "--output", "tech-debt-report.json"
            ])

        return [TextContent(type="text", text=output)]

    if name == "detect_dead_code":
        path = arguments.get("path", ".")
        quick_check = arguments.get("quick_check", False)

        if quick_check:
            output = run_command(["node", "scripts/quick-dead-code-check.ts", path])
        else:
            output = run_command([
                "python", "-m", "skene_growth.cli",
                "dead-code", path,
                "--output", "dead-code-report.json"
            ])

        return [TextContent(type="text", text=output)]

    if name == "analyze_entropy":
        path = arguments.get("path", ".")
        output = run_command(["node", "scripts/entropy-analyzer.ts", path])
        return [TextContent(type="text", text=output)]

    if name == "analyze_complexity":
        path = arguments.get("path", ".")
        output = run_command(["node", "scripts/complexity-indexer.ts", path])
        return [TextContent(type="text", text=output)]

    if name == "generate_growth_manifest":
        path = arguments.get("path", ".")
        include_tech_health = arguments.get("include_tech_health", True)

        cmd = ["python", "-m", "skene_growth.cli", "analyze", path]
        if include_tech_health:
            cmd.append("--include-tech-health")

        output = run_command(cmd)
        return [TextContent(type="text", text=output)]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
