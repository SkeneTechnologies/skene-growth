"""
Context Synthesis Analyzer.

This module implements the "brain" that understands what the product is
(Industry, Persona, Value Prop) before deeper growth analysis happens.

Uses a two-pass approach:
1. Pass 1: Heuristic Feeder (deterministic Python-based tagging)
2. Pass 2: Semantic Synthesis (LLM-based high-fidelity ProductContext)
"""

import json
import re
from typing import TYPE_CHECKING

from loguru import logger
from pydantic import ValidationError

from skene_growth.codebase import CodebaseExplorer
from skene_growth.llm import LLMClient
from skene_growth.models.context import ContextSignals, ProductContext
from skene_growth.synthesis.heuristics import (
    apply_heuristic_tags,
    extract_api_routes_from_files,
    extract_database_tables_from_files,
)

if TYPE_CHECKING:
    pass


# System prompt for LLM synthesis
CONTEXT_SYNTHESIS_PROMPT = """You are a Product Architect analyzing a codebase to reverse-engineer what the product is.

Your task is to synthesize a high-fidelity understanding of the product from raw codebase signals.

## Your Role
Act as a Product Architect who can read between the lines of code to understand:
- What industry/vertical this product serves
- Who the target audience is
- What problem it solves (value proposition)
- How it makes money (business model)

## Critical Rules
1. **NO HALLUCINATION**: Only infer what you can directly support with evidence from the provided signals
2. **CITE EVIDENCE**: Always reference specific files, tables, or patterns that support your synthesis
3. **FOCUS ON STRONG SIGNALS**: Database schema (tables) is the most reliable indicator - prioritize this
4. **HANDLE NOISE**: Ignore irrelevant files (tests, examples, boilerplate) - focus on core product logic
5. **BE SPECIFIC**: Avoid generic answers like "SaaS application" - be specific about industry and use case

## Input Signals

You will receive:
- **Database Tables**: Strong signal - these reveal the core domain model
- **API Routes**: Medium signal - these reveal user-facing functionality
- **Dependencies**: Medium signal - third-party services reveal integrations and use cases
- **Heuristic Tags**: Pre-computed tags from deterministic pattern matching
- **File Structure**: Weak signal - directory patterns may hint at organization
- **README Keywords**: Weak signal - may contain product description

## Analysis Process

1. **Start with Database Schema**: Tables reveal the core entities and relationships
   - Example: `patients`, `appointments`, `medical_records` → Healthcare
   - Example: `organizations`, `workspaces`, `members` → B2B Collaboration
   - Example: `orders`, `products`, `sellers` → Marketplace/E-commerce

2. **Cross-reference with API Routes**: Routes confirm what users can do
   - Example: `/api/patients` + `patients` table → Patient management system
   - Example: `/api/organizations` + `organizations` table → Multi-tenant B2B

3. **Validate with Dependencies**: Third-party services confirm use cases
   - Example: `stripe` + `subscriptions` table → Subscription-based monetization
   - Example: `sendgrid` + `organizations` table → B2B email communication

4. **Use Heuristic Tags as Hints**: Tags guide you but don't rely solely on them
   - `B2B_MULTITENANT` → Likely B2B SaaS
   - `FINTECH_INDICATORS` → Likely financial technology
   - `MARKETPLACE_INDICATORS` → Likely marketplace/e-commerce

5. **Synthesize Final Understanding**: Combine all signals into coherent product context

## Output Format

Return a JSON object matching the ProductContext schema:
{
    "industry": "Primary industry (e.g., 'Healthcare', 'FinTech', 'Developer Tools')",
    "secondary_industries": ["List of secondary industries if applicable"],
    "target_audience": "Who uses this product (e.g., 'B2B SaaS teams', 'Healthcare providers')",
    "target_role": "Specific role or persona (e.g., 'Developers', 'Doctors')",
    "value_proposition": "What problem it solves (1-2 sentences)",
    "business_model": "Business model type (e.g., 'B2B SaaS', 'Marketplace', 'Consumer App')",
    "monetization_strategy": "How it makes money (e.g., 'Subscription', 'Transaction fees')",
    "confidence_score": 0.0-1.0,
    "evidence": ["Specific evidence that supports each field"]
}

## Confidence Scoring

- **0.9-1.0**: Very clear signals (e.g., healthcare tables + medical dependencies + healthcare routes)
- **0.7-0.9**: Strong signals with some ambiguity
- **0.5-0.7**: Moderate signals, some inference required
- **0.3-0.5**: Weak signals, significant inference
- **0.0-0.3**: Very unclear, minimal signals

## Examples

### Example 1: Clear B2B SaaS
Tables: `organizations`, `workspaces`, `members`, `subscriptions`
Routes: `/api/organizations`, `/api/workspaces`
Dependencies: `stripe`, `sendgrid`
Tags: `B2B_MULTITENANT`, `HAS_MONETIZATION`
→ Industry: "Developer Tools", Business Model: "B2B SaaS", Monetization: "Subscription"

### Example 2: Healthcare Platform
Tables: `patients`, `appointments`, `medical_records`, `doctors`
Routes: `/api/patients`, `/api/appointments`
Dependencies: `hipaa-compliance`
Tags: `HEALTHCARE_INDICATORS`
→ Industry: "Healthcare", Business Model: "B2B SaaS", Target: "Healthcare providers"

Remember: Be evidence-based, cite your sources, and avoid generic answers."""


class ContextSynthesizer:
    """
    Synthesizes product context from raw codebase signals.

    This class implements the two-pass approach:
    1. Heuristic Feeder: Fast Python-based tagging
    2. Semantic Synthesis: LLM-based high-fidelity understanding

    Example:
        synthesizer = ContextSynthesizer()
        signals = ContextSignals(
            database_tables=["organizations", "users", "subscriptions"],
            dependencies=["stripe", "sendgrid"],
        )
        context = await synthesizer.analyze(signals, llm_client)
    """

    async def analyze(
        self,
        signals: ContextSignals,
        llm: LLMClient,
    ) -> ProductContext:
        """
        Analyze context signals and synthesize product understanding.

        Args:
            signals: Raw context signals extracted from codebase
            llm: LLM client for semantic synthesis

        Returns:
            ProductContext with synthesized product understanding

        Raises:
            ValueError: If synthesis fails or produces invalid output
        """
        logger.info("Starting context synthesis")

        # Pass 1: Apply heuristic tags
        logger.debug("Pass 1: Applying heuristic tags")
        heuristic_tags = apply_heuristic_tags(signals)
        logger.info(f"Generated {len(heuristic_tags)} heuristic tags")

        # Pass 2: LLM semantic synthesis
        logger.debug("Pass 2: Running LLM semantic synthesis")
        llm_prompt = self._build_synthesis_prompt(signals, heuristic_tags)

        try:
            response = await llm.generate_content(llm_prompt)
            product_context = self._parse_response(response)
            logger.info(f"Context synthesis complete: {product_context.industry} ({product_context.business_model})")
            return product_context
        except Exception as e:
            logger.error(f"Context synthesis failed: {e}")
            raise ValueError(f"Failed to synthesize product context: {e}") from e

    def _build_synthesis_prompt(
        self,
        signals: ContextSignals,
        heuristic_tags: list[str],
    ) -> str:
        """
        Build the LLM prompt for context synthesis.

        Args:
            signals: Raw context signals
            heuristic_tags: Pre-computed heuristic tags

        Returns:
            Complete prompt string for LLM
        """
        prompt_parts = [
            CONTEXT_SYNTHESIS_PROMPT,
            "",
            "## Raw Signals",
            "",
            "### Database Tables (Strong Signal)",
            json.dumps(signals.database_tables, indent=2) if signals.database_tables else "[]",
            "",
            "### API Routes (Medium Signal)",
            json.dumps(signals.api_routes, indent=2) if signals.api_routes else "[]",
            "",
            "### Dependencies (Medium Signal)",
            json.dumps(signals.dependencies, indent=2) if signals.dependencies else "[]",
            "",
            "### Heuristic Tags (Pre-computed)",
            json.dumps(heuristic_tags, indent=2) if heuristic_tags else "[]",
        ]

        # Add optional signals if present
        if signals.file_structure_patterns:
            prompt_parts.extend(
                [
                    "",
                    "### File Structure Patterns (Weak Signal)",
                    json.dumps(signals.file_structure_patterns, indent=2),
                ]
            )

        if signals.readme_keywords:
            prompt_parts.extend(
                [
                    "",
                    "### README Keywords (Weak Signal)",
                    json.dumps(signals.readme_keywords, indent=2),
                ]
            )

        if signals.comments:
            prompt_parts.extend(
                [
                    "",
                    "### Notable Comments (Weak Signal)",
                    json.dumps(signals.comments[:10], indent=2),  # Limit to avoid token bloat
                ]
            )

        prompt_parts.extend(
            [
                "",
                "## Task",
                "Analyze the signals above and synthesize a ProductContext.",
                "Remember: Focus on database tables as the strongest signal.",
                "Cite specific evidence for each field.",
                "",
                "Return ONLY valid JSON matching the ProductContext schema, no other text.",
            ]
        )

        return "\n".join(prompt_parts)

    def _parse_response(self, response: str) -> ProductContext:
        """
        Parse LLM response into ProductContext.

        Args:
            response: Raw LLM response string

        Returns:
            Validated ProductContext

        Raises:
            ValueError: If response cannot be parsed or validated
        """
        # Try direct JSON parse
        try:
            parsed = json.loads(response.strip())
            return ProductContext.model_validate(parsed)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", response)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1).strip())
                return ProductContext.model_validate(parsed)
            except (json.JSONDecodeError, ValidationError):
                pass

        # Try to find JSON object pattern
        obj_match = re.search(r"\{[\s\S]*\}", response)
        if obj_match:
            try:
                parsed = json.loads(obj_match.group(0))
                return ProductContext.model_validate(parsed)
            except (json.JSONDecodeError, ValidationError):
                pass

        logger.error(f"Could not parse context synthesis response: {response[:200]}")
        raise ValueError("Failed to parse LLM response as valid ProductContext JSON")


async def extract_context_signals(
    codebase: CodebaseExplorer,
    file_contents: dict[str, str] | None = None,
) -> ContextSignals:
    """
    Extract raw context signals from a codebase.

    This is a helper function that collects signals from various sources:
    - Database tables from schema/migration files
    - API routes from route definition files
    - Dependencies from package files

    Args:
        codebase: CodebaseExplorer instance for file access
        file_contents: Optional pre-loaded file contents (if available from previous steps)

    Returns:
        ContextSignals with extracted raw signals
    """
    logger.info("Extracting context signals from codebase")

    # If file_contents not provided, we'd need to read files
    # For now, assume file_contents is provided from previous analysis steps
    if file_contents is None:
        file_contents = {}

    # Extract database tables
    database_tables = extract_database_tables_from_files(file_contents)

    # Extract API routes
    api_routes = extract_api_routes_from_files(file_contents)

    # Extract dependencies (would need to read package.json, requirements.txt, etc.)
    # For now, this is a placeholder - in practice, you'd parse package files
    dependencies: list[str] = []
    for file_path, content in file_contents.items():
        if "package.json" in file_path or "requirements.txt" in file_path or "pyproject.toml" in file_path:
            # Simple extraction - in practice, use proper parsers
            if "stripe" in content.lower():
                dependencies.append("stripe")
            if "sendgrid" in content.lower():
                dependencies.append("sendgrid")
            # Add more dependency extraction logic here

    # Extract file structure patterns
    file_structure_patterns: list[str] = []
    for file_path in file_contents.keys():
        if "/app/" in file_path or "/src/" in file_path:
            # Extract notable directory patterns
            parts = file_path.split("/")
            if len(parts) > 2:
                pattern = "/".join(parts[:3])
                if pattern not in file_structure_patterns:
                    file_structure_patterns.append(pattern)

    signals = ContextSignals(
        database_tables=database_tables,
        api_routes=api_routes,
        dependencies=dependencies,
        file_structure_patterns=file_structure_patterns[:20],  # Limit to avoid bloat
    )

    logger.info(
        f"Extracted signals: {len(database_tables)} tables, {len(api_routes)} routes, {len(dependencies)} dependencies"
    )
    return signals
