"""
PLG Readiness Report Generator

Generates Skene-branded HTML reports from growth manifests with shareable scorecards.
"""

from skene_growth.reports.html import generate_html_report
from skene_growth.reports.score import calculate_plg_score

__all__ = ["generate_html_report", "calculate_plg_score"]
