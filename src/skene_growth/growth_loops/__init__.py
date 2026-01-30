"""
Growth loops selection module (INTERNAL).

DEPRECATED: This module is internal only. Use skene_growth.planner.Planner instead.

The Planner class now includes selection methods:
- Planner.select_loops() - LLM-based loop selection
- Planner.write_selected_loops_markdown() - Write results to markdown

This module is not exported in the public API.
"""

from skene_growth.growth_loops.selector import (
    select_growth_loops,
    select_single_loop,
    write_growth_loops_output,
)

__all__ = [
    "select_growth_loops",
    "select_single_loop",
    "write_growth_loops_output",
]
