"""
Heuristic tagging system for context signals.

This module provides deterministic, fast Python-based tagging that runs
before LLM synthesis. It identifies patterns in dependencies, database
tables, and file structures to generate initial tags.
"""

import re
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from skene_growth.models.context import ContextSignals


# Dependency-based tags
MONETIZATION_INDICATORS = {
    "stripe",
    "paypal",
    "paddle",
    "lemonsqueezy",
    "recurly",
    "chargebee",
    "billing",
    "payment",
    "subscription",
}

AUTH_INDICATORS = {
    "auth0",
    "clerk",
    "nextauth",
    "passport",
    "jwt",
    "oauth",
    "firebase-auth",
    "supabase-auth",
}

B2B_INDICATORS = {
    "sendgrid",
    "mailgun",
    "postmark",
    "twilio",
    "intercom",
    "customer.io",
    "hubspot",
    "salesforce",
}

FINTECH_INDICATORS = {
    "plaid",
    "stripe",
    "banking",
    "payment",
    "transaction",
    "ledger",
    "accounting",
}

HEALTHCARE_INDICATORS = {
    "hipaa",
    "hl7",
    "fhir",
    "medical",
    "patient",
    "epic",
    "cerner",
}

AI_ML_INDICATORS = {
    "openai",
    "anthropic",
    "langchain",
    "llama",
    "tensorflow",
    "pytorch",
    "transformers",
    "huggingface",
}

# Database table pattern indicators
MULTITENANT_INDICATORS = {
    "organizations",
    "workspaces",
    "teams",
    "tenants",
    "accounts",
    "companies",
}

MARKETPLACE_INDICATORS = {
    "orders",
    "cart",
    "products",
    "inventory",
    "transactions",
    "listings",
    "sellers",
    "buyers",
}

SOCIAL_INDICATORS = {
    "follows",
    "likes",
    "comments",
    "posts",
    "feed",
    "notifications",
    "friends",
}

COLLABORATION_INDICATORS = {
    "workspaces",
    "projects",
    "collaborators",
    "sharing",
    "permissions",
    "invitations",
}


def apply_heuristic_tags(signals: "ContextSignals") -> list[str]:
    """
    Apply deterministic heuristic tags to context signals.

    This function runs fast Python-based pattern matching to generate
    initial tags before LLM synthesis. Tags help guide the LLM's analysis.

    Args:
        signals: Raw context signals extracted from codebase

    Returns:
        List of string tags (e.g., ["HAS_AUTH", "B2B_MULTITENANT", "FINTECH_INDICATORS"])
    """
    tags = []

    # Normalize inputs for case-insensitive matching
    deps_lower = [dep.lower() for dep in signals.dependencies]
    tables_lower = [table.lower() for table in signals.database_tables]
    routes_lower = [route.lower() for route in signals.api_routes]

    # Monetization detection
    if any(indicator in " ".join(deps_lower) for indicator in MONETIZATION_INDICATORS):
        tags.append("HAS_MONETIZATION")
    if any("stripe" in dep for dep in deps_lower):
        tags.append("USES_STRIPE")

    # Authentication detection
    if any(indicator in " ".join(deps_lower) for indicator in AUTH_INDICATORS):
        tags.append("HAS_AUTH")
    if any("/auth" in route or "/login" in route for route in routes_lower):
        tags.append("HAS_AUTH_ROUTES")

    # B2B indicators
    if any(indicator in " ".join(deps_lower) for indicator in B2B_INDICATORS):
        tags.append("B2B_INDICATORS")
    if any(indicator in " ".join(tables_lower) for indicator in MULTITENANT_INDICATORS):
        tags.append("B2B_MULTITENANT")

    # Industry-specific indicators
    if any(indicator in " ".join(deps_lower) for indicator in FINTECH_INDICATORS):
        tags.append("FINTECH_INDICATORS")
    if any(indicator in " ".join(tables_lower) for indicator in FINTECH_INDICATORS):
        tags.append("FINTECH_INDICATORS")

    if any(indicator in " ".join(deps_lower) for indicator in HEALTHCARE_INDICATORS):
        tags.append("HEALTHCARE_INDICATORS")
    if any("patient" in table or "medical" in table for table in tables_lower):
        tags.append("HEALTHCARE_INDICATORS")

    if any(indicator in " ".join(deps_lower) for indicator in AI_ML_INDICATORS):
        tags.append("AI_ML_INDICATORS")

    # Business model indicators
    if any(indicator in " ".join(tables_lower) for indicator in MARKETPLACE_INDICATORS):
        tags.append("MARKETPLACE_INDICATORS")
    if any("order" in table or "cart" in table for table in tables_lower):
        tags.append("E_COMMERCE_INDICATORS")

    if any(indicator in " ".join(tables_lower) for indicator in SOCIAL_INDICATORS):
        tags.append("SOCIAL_INDICATORS")

    if any(indicator in " ".join(tables_lower) for indicator in COLLABORATION_INDICATORS):
        tags.append("COLLABORATION_INDICATORS")

    # Multi-tenancy detection
    if any(indicator in " ".join(tables_lower) for indicator in MULTITENANT_INDICATORS):
        tags.append("MULTITENANT_ARCHITECTURE")

    # API structure indicators
    if len(signals.api_routes) > 10:
        tags.append("RICH_API")
    if any("/api/v" in route for route in routes_lower):
        tags.append("VERSIONED_API")

    # Database complexity indicators
    if len(signals.database_tables) > 20:
        tags.append("COMPLEX_SCHEMA")
    if len(signals.database_tables) < 5:
        tags.append("SIMPLE_SCHEMA")

    logger.debug(f"Generated {len(tags)} heuristic tags: {tags}")
    return tags


def extract_database_tables_from_files(file_contents: dict[str, str]) -> list[str]:
    """
    Extract database table names from file contents.

    Looks for common patterns:
    - SQL CREATE TABLE statements
    - ORM model definitions (Django, SQLAlchemy, Prisma, etc.)
    - Migration files

    Args:
        file_contents: Dictionary mapping file paths to their contents

    Returns:
        List of table names found
    """
    tables = set()

    for file_path, content in file_contents.items():
        # SQL CREATE TABLE statements
        create_table_pattern = r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:`)?(\w+)(?:`)?"
        matches = re.findall(create_table_pattern, content, re.IGNORECASE)
        tables.update(matches)

        # Django models
        django_pattern = r"class\s+(\w+)\s*\(.*models\.Model\)"
        matches = re.findall(django_pattern, content, re.IGNORECASE)
        tables.update(m.lower() + "s" for m in matches)  # Django pluralizes

        # SQLAlchemy models
        sqlalchemy_pattern = r"class\s+(\w+)\s*\(.*Base\)|__tablename__\s*=\s*['\"](\w+)['\"]"
        matches = re.findall(sqlalchemy_pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                tables.update(m for m in match if m)
            else:
                tables.add(match)

        # Prisma schema
        prisma_pattern = r"model\s+(\w+)\s*\{"
        matches = re.findall(prisma_pattern, content, re.IGNORECASE)
        tables.update(matches)

    return sorted(list(tables))


def extract_api_routes_from_files(file_contents: dict[str, str]) -> list[str]:
    """
    Extract API route patterns from file contents.

    Looks for common patterns:
    - Express.js routes
    - Next.js API routes
    - FastAPI routes
    - Django URLs
    - Flask routes

    Args:
        file_contents: Dictionary mapping file paths to their contents

    Returns:
        List of route patterns found
    """
    routes = set()

    for file_path, content in file_contents.items():
        # Express.js / Next.js API routes
        express_pattern = r"(?:router\.|app\.)(?:get|post|put|delete|patch)\s*\(['\"]([^'\"]+)['\"]"
        matches = re.findall(express_pattern, content, re.IGNORECASE)
        routes.update(matches)

        # FastAPI routes
        fastapi_pattern = r"@(?:app|router)\.(?:get|post|put|delete|patch)\s*\(['\"]([^'\"]+)['\"]"
        matches = re.findall(fastapi_pattern, content, re.IGNORECASE)
        routes.update(matches)

        # Django URLs
        django_pattern = r"path\s*\(['\"]([^'\"]+)['\"]"
        matches = re.findall(django_pattern, content, re.IGNORECASE)
        routes.update(matches)

        # Flask routes
        flask_pattern = r"@(?:app|blueprint)\.route\s*\(['\"]([^'\"]+)['\"]"
        matches = re.findall(flask_pattern, content, re.IGNORECASE)
        routes.update(matches)

        # Next.js API route file paths
        if "/api/" in file_path and file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            # Extract route from file path
            api_match = re.search(r"/api(/[^/]+)", file_path)
            if api_match:
                routes.add(api_match.group(1))

    return sorted(list(routes))
