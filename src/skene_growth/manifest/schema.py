"""
Pydantic schemas for growth manifest output.

These models define the structure of growth-manifest.json, which captures:
- Tech stack detection
- Growth hub identification
- Go-to-market gaps
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TechStack(BaseModel):
    """Detected technology stack of the project."""

    framework: str | None = Field(
        default=None,
        description="Primary framework (e.g., 'Next.js', 'FastAPI', 'Rails')",
    )
    language: str = Field(
        description="Primary programming language (e.g., 'Python', 'TypeScript')",
    )
    database: str | None = Field(
        default=None,
        description="Database technology (e.g., 'PostgreSQL', 'MongoDB')",
    )
    auth: str | None = Field(
        default=None,
        description="Authentication method (e.g., 'JWT', 'OAuth', 'Clerk')",
    )
    deployment: str | None = Field(
        default=None,
        description="Deployment platform (e.g., 'Vercel', 'AWS', 'Docker')",
    )
    package_manager: str | None = Field(
        default=None,
        description="Package manager (e.g., 'npm', 'poetry', 'cargo')",
    )
    services: list[str] = Field(
        default_factory=list,
        description="Third-party services and integrations (e.g., 'Stripe', 'SendGrid', 'Twilio')",
    )


class GrowthHub(BaseModel):
    """A feature or area with growth potential."""

    feature_name: str = Field(
        description="Name of the feature or growth area",
    )
    file_path: str = Field(
        description="Primary file path where this feature is implemented",
    )
    detected_intent: str = Field(
        description="Detected purpose or intent of the feature",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the detection (0.0-1.0)",
    )
    entry_point: str | None = Field(
        default=None,
        description="Entry point for users (e.g., URL path, function name)",
    )
    growth_potential: list[str] = Field(
        default_factory=list,
        description="List of growth opportunities for this feature",
    )


class GTMGap(BaseModel):
    """Go-to-market gap or missing feature."""

    feature_name: str = Field(
        description="Name of the missing feature or gap",
    )
    description: str = Field(
        description="Description of what's missing and why it matters",
    )
    priority: Literal["high", "medium", "low"] = Field(
        description="Priority level for addressing this gap",
    )


class ProductOverview(BaseModel):
    """High-level product information for documentation."""

    tagline: str | None = Field(
        default=None,
        description="Short one-liner describing the product (under 15 words)",
    )
    value_proposition: str | None = Field(
        default=None,
        description="What problem the product solves and why it matters",
    )
    target_audience: str | None = Field(
        default=None,
        description="Who the product is for (e.g., developers, businesses)",
    )


class Feature(BaseModel):
    """User-facing feature documentation."""

    name: str = Field(
        description="Human-readable feature name",
    )
    description: str = Field(
        description="User-facing description of what the feature does",
    )
    file_path: str | None = Field(
        default=None,
        description="Primary file where this feature is implemented",
    )
    usage_example: str | None = Field(
        default=None,
        description="Code snippet or usage example",
    )
    category: str | None = Field(
        default=None,
        description="Feature category (e.g., 'Authentication', 'API', 'UI')",
    )


class GrowthManifest(BaseModel):
    """
    Complete growth manifest for a project.

    This is the primary output of PLG analysis, capturing everything
    needed to understand a project's growth potential.
    """

    version: str = Field(
        default="1.0",
        description="Manifest schema version",
    )
    project_name: str = Field(
        description="Name of the analyzed project",
    )
    description: str | None = Field(
        default=None,
        description="Brief description of the project",
    )
    tech_stack: TechStack = Field(
        description="Detected technology stack",
    )
    growth_hubs: list[GrowthHub] = Field(
        default_factory=list,
        description="Identified growth hubs and features",
    )
    gtm_gaps: list[GTMGap] = Field(
        default_factory=list,
        description="Go-to-market gaps to address",
    )
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="When the manifest was generated",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version": "1.0",
                "project_name": "my-saas-app",
                "description": "A SaaS application for team collaboration",
                "tech_stack": {
                    "framework": "Next.js",
                    "language": "TypeScript",
                    "database": "PostgreSQL",
                    "auth": "NextAuth.js",
                    "deployment": "Vercel",
                    "package_manager": "npm",
                    "services": ["Stripe", "SendGrid"],
                },
                "growth_hubs": [
                    {
                        "feature_name": "Team Invitations",
                        "file_path": "src/features/invitations/index.ts",
                        "detected_intent": "Viral growth through team expansion",
                        "confidence_score": 0.85,
                        "entry_point": "/invite",
                        "growth_potential": [
                            "Add referral tracking",
                            "Implement invite rewards",
                        ],
                    }
                ],
                "gtm_gaps": [
                    {
                        "feature_name": "Analytics Dashboard",
                        "description": "No usage analytics for tracking team activity",
                        "priority": "high",
                    }
                ],
                "generated_at": "2024-01-15T10:30:00Z",
            }
        }
    )


class DocsManifest(GrowthManifest):
    """
    Extended manifest with documentation-specific fields.

    Inherits all GrowthManifest fields and adds:
    - product_overview: High-level product description
    - features: User-facing feature documentation
    """

    version: str = Field(
        default="2.0",
        description="Manifest schema version (2.0 for docs-enabled)",
    )
    product_overview: ProductOverview | None = Field(
        default=None,
        description="High-level product overview",
    )
    features: list[Feature] = Field(
        default_factory=list,
        description="User-facing feature documentation",
    )
