"""Ground truth schema and loading for factual evaluation.

Ground truth files are TOML files that describe verifiable properties
of a codebase — tech stack, known features, industry, etc. These are
used by the factual evaluator to score how accurately the pipeline
detected real properties of the codebase.
"""

import tomllib
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, Field


class GroundTruthTechStack(BaseModel):
    """Known tech stack components. Each field is optional — only specify what you know."""

    framework: str | None = Field(default=None, description="Primary framework (e.g., 'Next.js', 'Django')")
    language: str | None = Field(default=None, description="Primary language (e.g., 'TypeScript', 'Python')")
    database: str | None = Field(default=None, description="Database (e.g., 'PostgreSQL', 'MongoDB')")
    auth: str | None = Field(default=None, description="Auth method (e.g., 'Supabase Auth', 'NextAuth')")
    deployment: str | None = Field(default=None, description="Deployment platform (e.g., 'Vercel', 'AWS')")
    package_manager: str | None = Field(default=None, description="Package manager (e.g., 'npm', 'uv')")
    services: list[str] = Field(default_factory=list, description="Known third-party services (e.g., 'Stripe')")


class GroundTruthFeature(BaseModel):
    """A feature the tool should detect in the codebase."""

    name: str = Field(description="Feature name (e.g., 'billing', 'team_invites')")
    description: str = Field(default="", description="What this feature does")
    file_patterns: list[str] = Field(
        default_factory=list,
        description="File path patterns that prove this feature exists (glob-style or substring match)",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Keywords that should appear in detected feature names or descriptions",
    )


class GroundTruthIndustry(BaseModel):
    """Expected industry classification."""

    primary: str = Field(description="Expected primary industry (e.g., 'DevTools', 'E-commerce')")
    acceptable_alternatives: list[str] = Field(
        default_factory=list,
        description="Other acceptable primary classifications (e.g., 'SaaS' when 'DevTools' is primary)",
    )
    expected_tags: list[str] = Field(
        default_factory=list,
        description="Tags that should appear in secondary (e.g., 'B2B', 'SaaS')",
    )


class GroundTruth(BaseModel):
    """Complete ground truth for a codebase.

    This describes verifiable, factual properties of a codebase that the
    pipeline output can be checked against. Only include properties you
    are confident about.
    """

    name: str = Field(description="Codebase name (must match config.toml)")
    description: str = Field(default="", description="Brief description of what this codebase is")
    tech_stack: GroundTruthTechStack = Field(default_factory=GroundTruthTechStack)
    industry: GroundTruthIndustry | None = Field(default=None)
    expected_features: list[GroundTruthFeature] = Field(
        default_factory=list,
        description="Features the tool should detect",
    )
    notable_files: list[str] = Field(
        default_factory=list,
        description="Key files that should be referenced in the output (relative to codebase root)",
    )


def load_ground_truth(path: Path) -> GroundTruth:
    """Load ground truth from a TOML file.

    Args:
        path: Path to ground truth TOML file.

    Returns:
        Parsed GroundTruth model.
    """
    if not path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {path}")

    with open(path, "rb") as f:
        raw = tomllib.load(f)

    logger.debug(f"Loaded ground truth from {path}")
    return GroundTruth(**raw)
