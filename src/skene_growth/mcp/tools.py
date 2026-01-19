"""MCP tools for skene-growth analysis.

These tools reuse the same analysis logic as the CLI to ensure consistent behavior.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import SecretStr

from skene_growth.config import default_model_for_provider, load_config
from skene_growth.mcp.cache import AnalysisCache


def _json_serializer(obj: Any) -> str:
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


async def analyze_codebase(
    path: str,
    cache: AnalysisCache,
    product_docs: bool = False,
    business_type: str | None = None,
    force_refresh: bool = False,
    on_progress: Any = None,
) -> dict[str, Any]:
    """Analyze a codebase for growth opportunities.

    This function uses the same analysis logic as the CLI's `analyze` command.

    Args:
        path: Absolute path to the repository to analyze
        cache: Analysis cache instance
        product_docs: Generate v2.0 manifest with product documentation
        business_type: Business type hint (e.g., 'b2b-saas', 'marketplace')
        force_refresh: Skip cache and force re-analysis
        on_progress: Optional progress callback

    Returns:
        Analysis result with manifest data
    """
    from skene_growth.analyzers import DocsAnalyzer, ManifestAnalyzer
    from skene_growth.codebase import CodebaseExplorer
    from skene_growth.llm import create_llm_client

    repo_path = Path(path).resolve()

    if not repo_path.exists():
        raise ValueError(f"Path does not exist: {repo_path}")

    if not repo_path.is_dir():
        raise ValueError(f"Path is not a directory: {repo_path}")

    # Build cache params
    params = {
        "product_docs": product_docs,
        "business_type": business_type,
        "repo_path": str(repo_path),
    }

    # Check cache unless force refresh
    if not force_refresh:
        cached_entry = await cache.get(repo_path, params)
        if cached_entry:
            return {
                "manifest": cached_entry.manifest,
                "cached": True,
                "analysis_time": 0,
                "manifest_path": str(repo_path / "skene-context" / "growth-manifest.json"),
            }

    # Load config (same as CLI)
    config = load_config()

    # Resolve API key
    api_key = os.environ.get("SKENE_API_KEY") or config.api_key
    provider = os.environ.get("SKENE_PROVIDER") or config.provider
    model = os.environ.get("SKENE_MODEL") or config.get("model") or default_model_for_provider(provider)

    # Local providers don't need API key
    is_local_provider = provider.lower() in ("lmstudio", "lm-studio", "lm_studio", "ollama")

    if not api_key:
        if is_local_provider:
            api_key = provider
        else:
            raise ValueError(
                "API key not configured. Set SKENE_API_KEY environment variable "
                "or add api_key to ~/.config/skene-growth/config.toml"
            )

    # Initialize components (same as CLI _run_analysis)
    import time

    start_time = time.time()

    codebase = CodebaseExplorer(repo_path)
    llm = create_llm_client(provider, SecretStr(api_key), model)

    # Create analyzer based on mode
    if product_docs:
        analyzer = DocsAnalyzer()
        request_msg = "Generate documentation for this project"
    else:
        analyzer = ManifestAnalyzer()
        request_msg = "Analyze this codebase for growth opportunities"

    # Run analysis
    result = await analyzer.run(
        codebase=codebase,
        llm=llm,
        request=request_msg,
        on_progress=on_progress,
    )

    if not result.success:
        raise RuntimeError(f"Analysis failed: {result.error}")

    # Extract manifest (same as CLI)
    manifest_data = result.data.get("output", result.data) if "output" in result.data else result.data

    # Save manifest to disk (same locations as CLI)
    output_dir = repo_path / "skene-context"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "growth-manifest.json"
    output_path.write_text(json.dumps(manifest_data, indent=2, default=_json_serializer))

    # Generate markdown summary
    _write_manifest_markdown(manifest_data, output_path)

    # Generate product docs if requested
    if product_docs:
        _write_product_docs(manifest_data, output_path)

    # Generate growth template
    await _write_growth_template(llm, manifest_data, business_type)

    analysis_time = time.time() - start_time

    # Cache result
    await cache.set(repo_path, params, manifest_data)

    return {
        "manifest": manifest_data,
        "cached": False,
        "analysis_time": round(analysis_time, 2),
        "manifest_path": str(output_path),
    }


def _write_manifest_markdown(manifest_data: dict, output_path: Path) -> None:
    """Render a markdown summary next to the JSON manifest."""
    from skene_growth.docs import DocsGenerator
    from skene_growth.manifest import DocsManifest, GrowthManifest

    try:
        if manifest_data.get("version") == "2.0" or "product_overview" in manifest_data or "features" in manifest_data:
            manifest = DocsManifest.model_validate(manifest_data)
        else:
            manifest = GrowthManifest.model_validate(manifest_data)
    except Exception:
        return

    markdown_path = output_path.with_suffix(".md")
    try:
        generator = DocsGenerator()
        markdown_content = generator.generate_analysis(manifest)
        markdown_path.write_text(markdown_content)
    except Exception:
        pass


def _write_product_docs(manifest_data: dict, manifest_path: Path) -> None:
    """Generate and save product documentation."""
    from skene_growth.docs import DocsGenerator
    from skene_growth.manifest import DocsManifest, GrowthManifest

    try:
        if manifest_data.get("version") == "2.0" or "product_overview" in manifest_data or "features" in manifest_data:
            manifest = DocsManifest.model_validate(manifest_data)
        else:
            manifest = GrowthManifest.model_validate(manifest_data)
    except Exception:
        return

    output_dir = manifest_path.parent
    product_docs_path = output_dir / "product-docs.md"

    try:
        generator = DocsGenerator()
        product_content = generator.generate_product_docs(manifest)
        product_docs_path.write_text(product_content)
    except Exception:
        pass


async def _write_growth_template(llm, manifest_data: dict, business_type: str | None = None) -> dict | None:
    """Generate and save the growth template."""
    from skene_growth.templates import generate_growth_template, write_growth_template_outputs

    try:
        template_data = await generate_growth_template(llm, manifest_data, business_type)
        output_dir = Path("./skene-context")
        write_growth_template_outputs(template_data, output_dir)
        return template_data
    except Exception:
        return None


async def get_manifest(path: str) -> dict[str, Any]:
    """Retrieve an existing manifest from disk.

    Args:
        path: Absolute path to the repository

    Returns:
        Manifest data if exists, or info that no manifest was found
    """
    repo_path = Path(path).resolve()

    if not repo_path.exists():
        raise ValueError(f"Path does not exist: {repo_path}")

    # Look for manifest in standard locations (same as CLI)
    manifest_locations = [
        repo_path / "skene-context" / "growth-manifest.json",
        repo_path / "growth-manifest.json",
        repo_path / ".skene-growth" / "manifest.json",
    ]

    for manifest_path in manifest_locations:
        if manifest_path.exists():
            try:
                manifest_data = json.loads(manifest_path.read_text())
                return {
                    "manifest": manifest_data,
                    "manifest_path": str(manifest_path),
                    "exists": True,
                }
            except json.JSONDecodeError as e:
                raise ValueError(f"Manifest file is corrupted: {e}. Run analyze_codebase to regenerate.")

    return {
        "manifest": None,
        "manifest_path": str(repo_path / "skene-context" / "growth-manifest.json"),
        "exists": False,
        "message": "No manifest found. Run analyze_codebase to generate one.",
    }


async def clear_cache(cache: AnalysisCache, path: str | None = None) -> dict[str, Any]:
    """Clear cached analysis results.

    Args:
        cache: Analysis cache instance
        path: Optional path to clear cache for. If None, clears all cache.

    Returns:
        Number of entries cleared
    """
    if path:
        repo_path = Path(path).resolve()
        if not repo_path.exists():
            raise ValueError(f"Path does not exist: {repo_path}")
        cleared = await cache.clear(repo_path)
    else:
        cleared = await cache.clear()

    return {
        "cleared": cleared,
        "path": path,
        "message": f"Cleared {cleared} cache entries" + (f" for {path}" if path else ""),
    }
