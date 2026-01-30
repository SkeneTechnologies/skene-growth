"""
Manifest schemas for growth analysis output.

These Pydantic models define the structure of growth-manifest.json,
the primary output of PLG analysis.
"""

from skene_growth.manifest.schema import (
    DocsManifest,
    Feature,
    GrowthFeature,
    GrowthHub,
    GrowthManifest,
    GrowthOpportunity,
    GTMGap,
    ProductOverview,
    RevenueLeakage,
    TechStack,
)

__all__ = [
    "TechStack",
    "GrowthFeature",
    "GrowthHub",  # Backwards compatibility alias
    "GrowthOpportunity",
    "GTMGap",  # Backwards compatibility alias
    "RevenueLeakage",
    "GrowthManifest",
    "ProductOverview",
    "Feature",
    "DocsManifest",
]
