"""
Pydantic models for product context synthesis.

These models define the structure for:
- ContextSignals: Raw extraction data (strong/medium/weak signals)
- ProductContext: Final synthesized product understanding
"""

from typing import Literal

from pydantic import BaseModel, Field


class ContextSignals(BaseModel):
    """
    Container for raw signals extracted from the codebase.

    These signals are collected deterministically before LLM synthesis.
    Strong signals (like database schema) are most reliable indicators.
    """

    # Strong signals (high confidence indicators)
    database_tables: list[str] = Field(
        default_factory=list,
        description="Database table names extracted from schema files or migrations",
    )
    api_routes: list[str] = Field(
        default_factory=list,
        description="API route patterns extracted from route definitions",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Third-party dependencies from package.json, requirements.txt, etc.",
    )

    # Medium signals (moderate confidence)
    file_structure_patterns: list[str] = Field(
        default_factory=list,
        description="Notable directory/file patterns (e.g., 'app/patients/', 'models/order.py')",
    )
    config_keys: list[str] = Field(
        default_factory=list,
        description="Environment variable keys or config file keys",
    )

    # Weak signals (low confidence, but useful context)
    readme_keywords: list[str] = Field(
        default_factory=list,
        description="Keywords extracted from README files",
    )
    comments: list[str] = Field(
        default_factory=list,
        description="Notable comments or docstrings that mention product purpose",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "database_tables": ["organizations", "users", "subscriptions"],
                "api_routes": ["/api/organizations", "/api/users", "/api/billing"],
                "dependencies": ["stripe", "sendgrid", "postgres"],
                "file_structure_patterns": ["app/organizations/", "models/subscription.py"],
                "config_keys": ["STRIPE_SECRET_KEY", "SENDGRID_API_KEY"],
                "readme_keywords": ["SaaS", "B2B", "team collaboration"],
                "comments": ["Multi-tenant application", "Organization-based access control"],
            }
        }
    }


class ProductContext(BaseModel):
    """
    Synthesized product understanding from codebase analysis.

    This is the output of the Context Synthesis Layer, providing high-level
    understanding of what the product is before deeper growth analysis.
    """

    industry: str = Field(
        description="Primary industry or vertical (e.g., 'Healthcare', 'FinTech', 'Developer Tools')",
    )
    secondary_industries: list[str] = Field(
        default_factory=list,
        description="Secondary or adjacent industries if applicable",
    )
    target_audience: str = Field(
        description="Primary target audience description (e.g., 'B2B SaaS teams', 'Healthcare providers')",
    )
    target_role: str | None = Field(
        default=None,
        description="Specific role or persona (e.g., 'Developers', 'Product Managers', 'Doctors')",
    )
    value_proposition: str = Field(
        description="What problem the product solves and why it matters (1-2 sentences)",
    )
    business_model: str = Field(
        description="Business model type (e.g., 'B2B SaaS', 'Marketplace', 'Consumer App', 'Developer Tool')",
    )
    monetization_strategy: str | None = Field(
        default=None,
        description="How the product makes money (e.g., 'Subscription', 'Transaction fees', 'Freemium')",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the synthesis (0.0-1.0), based on signal strength and clarity",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Specific files, tables, or code patterns that support this synthesis",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "industry": "Healthcare",
                "secondary_industries": ["Telemedicine"],
                "target_audience": "Healthcare providers and medical practices",
                "target_role": "Doctors and medical staff",
                "value_proposition": "Streamlines patient management and appointment scheduling for medical practices",
                "business_model": "B2B SaaS",
                "monetization_strategy": "Subscription per practice",
                "confidence_score": 0.85,
                "evidence": [
                    "Database tables: patients, appointments, medical_records",
                    "API routes: /api/patients, /api/appointments",
                    "Dependencies: medical-calendar, hipaa-compliance",
                ],
            }
        }
    }
