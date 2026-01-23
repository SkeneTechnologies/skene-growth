"""
Context synthesis module.

Provides tools for understanding what a product is before
deeper growth analysis happens.
"""

from skene_growth.synthesis.analyzer import ContextSynthesizer, extract_context_signals
from skene_growth.synthesis.heuristics import apply_heuristic_tags

__all__ = [
    "ContextSynthesizer",
    "extract_context_signals",
    "apply_heuristic_tags",
]
