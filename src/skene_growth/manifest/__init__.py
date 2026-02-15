"""
Manifest schemas for growth analysis output.

These Pydantic models define the structure of growth-manifest.json,
the primary output of PLG analysis.
"""

from skene_growth.manifest.schema import (
    ArchitectureViolation,
    CodeSmell,
    DeadCodeFinding,
    DeadCodeReport,
    DependencyHealth,
    DocsManifest,
    Feature,
    GrowthHub,
    GrowthManifest,
    GTMGap,
    ProductOverview,
    TechDebtReport,
    TechnicalHealthReport,
    TechStack,
)

__all__ = [
    "TechStack",
    "GrowthHub",
    "GTMGap",
    "GrowthManifest",
    "ProductOverview",
    "Feature",
    "DocsManifest",
    "CodeSmell",
    "ArchitectureViolation",
    "DependencyHealth",
    "TechDebtReport",
    "TechnicalHealthReport",
    "DeadCodeFinding",
    "DeadCodeReport",
]
