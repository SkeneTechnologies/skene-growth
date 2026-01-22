"""
PLG Readiness Score Calculator

Calculates a PLG readiness score (0-100) and grade (A-F) from a growth manifest.
"""

from typing import Literal

from skene_growth.manifest import GrowthManifest


class PLGScoreBreakdown:
    """Breakdown of PLG score components."""

    def __init__(
        self,
        growth_hubs: int,
        gtm_gaps: int,
        tech_stack: int,
        features: int,
    ):
        self.growth_hubs = growth_hubs  # 0-40 points
        self.gtm_gaps = gtm_gaps  # 0-30 points (inverse - fewer gaps = higher score)
        self.tech_stack = tech_stack  # 0-15 points
        self.features = features  # 0-15 points


class PLGScoreResult:
    """Complete PLG score result with breakdown and grade."""

    def __init__(
        self,
        score: int,
        breakdown: PLGScoreBreakdown,
        grade: Literal["A", "B", "C", "D", "F"],
        message: str,
    ):
        self.score = score
        self.breakdown = breakdown
        self.grade = grade
        self.message = message


def calculate_plg_score(manifest: GrowthManifest) -> PLGScoreResult:
    """
    Calculate PLG readiness score from a growth manifest.

    Scoring breakdown:
    - Growth Hubs: 0-40 points (weighted by confidence)
    - GTM Gaps: 0-30 points (inverse - fewer gaps = higher score)
    - Tech Stack: 0-15 points (modern stack indicators)
    - Features: 0-15 points (more features = higher score)

    Args:
        manifest: Growth manifest to score

    Returns:
        PLGScoreResult with score, breakdown, grade, and message
    """
    # Growth Hubs Score (0-40 points)
    # More growth hubs = higher score, weighted by confidence
    growth_hubs_score = min(
        40,
        sum(hub.confidence_score * 10 for hub in manifest.growth_hubs),
    )

    # GTM Gaps Score (0-30 points)
    # Fewer gaps = higher score, weighted by priority
    gap_penalties = {"high": 10, "medium": 5, "low": 2}
    gap_penalty = sum(
        gap_penalties.get(gap.priority, 0) for gap in manifest.gtm_gaps
    )
    gtm_gaps_score = max(0, 30 - gap_penalty)

    # Tech Stack Score (0-15 points)
    tech_stack_score = _calculate_tech_stack_score(manifest.tech_stack)

    # Features Score (0-15 points)
    # More features = higher score
    # Features are only available in DocsManifest (v2.0)
    features = getattr(manifest, "features", None) or []
    features_score = min(15, len(features) * 2)

    breakdown = PLGScoreBreakdown(
        growth_hubs=round(growth_hubs_score),
        gtm_gaps=round(gtm_gaps_score),
        tech_stack=round(tech_stack_score),
        features=round(features_score),
    )

    total_score = round(
        breakdown.growth_hubs
        + breakdown.gtm_gaps
        + breakdown.tech_stack
        + breakdown.features
    )

    grade = _get_grade(total_score)
    message = _get_score_message(total_score, grade)

    return PLGScoreResult(score=total_score, breakdown=breakdown, grade=grade, message=message)


def _calculate_tech_stack_score(tech_stack) -> float:
    """Calculate tech stack score based on modern stack indicators."""
    score = 0.0

    # Modern framework (Next.js, React, etc.)
    if tech_stack.framework and tech_stack.framework in [
        "Next.js",
        "React",
        "Vue",
        "Svelte",
    ]:
        score += 5

    # TypeScript
    if tech_stack.language == "TypeScript":
        score += 3

    # Modern database
    if tech_stack.database and tech_stack.database in ["PostgreSQL", "Supabase"]:
        score += 3

    # Auth system
    if tech_stack.auth:
        score += 2

    # Additional services
    if tech_stack.services and len(tech_stack.services) > 0:
        score += min(2, len(tech_stack.services))

    return min(15, score)


def _get_grade(score: int) -> Literal["A", "B", "C", "D", "F"]:
    """Get letter grade from score."""
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _get_score_message(score: int, grade: str) -> str:
    """Get descriptive message for score and grade."""
    messages = {
        "A": "Excellent! Your product is highly PLG-ready with strong growth foundations.",
        "B": "Great! Your product has solid PLG foundations with room for optimization.",
        "C": "Good start! Your product has some PLG elements but needs more growth features.",
        "D": "Getting there! Focus on implementing core PLG features to improve readiness.",
        "F": "Early stage! Start by implementing basic growth loops and user onboarding.",
    }
    return messages.get(grade, messages["F"])
