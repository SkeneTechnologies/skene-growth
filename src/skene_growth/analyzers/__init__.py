"""
Analyzers for PLG (Product-Led Growth) analysis.

Each analyzer uses the MultiStepStrategy pattern to perform
a specific type of analysis on a codebase.
"""

from skene_growth.analyzers.docs import DocsAnalyzer
from skene_growth.analyzers.growth_features import GrowthFeaturesAnalyzer, GrowthHubAnalyzer
from skene_growth.analyzers.manifest import ManifestAnalyzer
from skene_growth.analyzers.tech_stack import TechStackAnalyzer

__all__ = [
    "TechStackAnalyzer",
    "GrowthFeaturesAnalyzer",
    "GrowthHubAnalyzer",  # Backwards compatibility alias
    "ManifestAnalyzer",
    "DocsAnalyzer",
]
