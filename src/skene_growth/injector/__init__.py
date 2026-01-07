"""
Growth loop injection planning.

This module provides tools for mapping growth loops to codebases
and generating injection plans for implementing growth features.
"""

from skene_growth.injector.loops import GrowthLoop, GrowthLoopCatalog
from skene_growth.injector.mapper import InjectionPoint, LoopMapper, LoopMapping
from skene_growth.injector.planner import (
    CodeChange,
    InjectionPlan,
    InjectionPlanner,
    LoopInjectionPlan,
)

__all__ = [
    # Loops
    "GrowthLoop",
    "GrowthLoopCatalog",
    # Mapper
    "LoopMapper",
    "LoopMapping",
    "InjectionPoint",
    # Planner
    "InjectionPlanner",
    "InjectionPlan",
    "LoopInjectionPlan",
    "CodeChange",
]
