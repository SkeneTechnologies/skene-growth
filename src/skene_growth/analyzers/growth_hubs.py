"""
Growth hub analyzer using MultiStepStrategy.

Identifies features and areas of a codebase with growth potential.
"""

from skene_growth.analyzers.prompts import GROWTH_HUB_PROMPT
from skene_growth.strategies import MultiStepStrategy
from skene_growth.strategies.steps import (
    AnalyzeStep,
    ReadFilesStep,
    SelectFilesStep,
)


class GrowthHubAnalyzer(MultiStepStrategy):
    """
    Analyzer for identifying growth hubs in a codebase.

    Growth hubs are features or areas that:
    - Enable viral growth (sharing, invitations, referrals)
    - Drive user engagement
    - Facilitate onboarding
    - Support monetization
    - Enable data-driven decisions

    Example:
        analyzer = GrowthHubAnalyzer()
        result = await analyzer.run(
            codebase=CodebaseExplorer("/path/to/repo"),
            llm=create_llm_client(),
            request="Find growth opportunities",
        )
        growth_hubs = result.data.get("growth_hubs", [])
    """

    def __init__(self):
        """Initialize the growth hub analyzer with predefined steps."""
        super().__init__(
            steps=[
                SelectFilesStep(
                    prompt="Select source files that might contain growth-related features. "
                    "Look for: user management, invitations, sharing, payments, "
                    "analytics, onboarding, notifications, and engagement features.",
                    patterns=[
                        "**/*.py",
                        "**/*.ts",
                        "**/*.tsx",
                        "**/*.js",
                        "**/*.jsx",
                        "**/routes/**/*",
                        "**/api/**/*",
                        "**/features/**/*",
                        "**/components/**/*",
                        "**/pages/**/*",
                        "**/app/**/*",
                    ],
                    max_files=30,
                    output_key="selected_files",
                ),
                ReadFilesStep(
                    source_key="selected_files",
                    output_key="file_contents",
                ),
                AnalyzeStep(
                    prompt=GROWTH_HUB_PROMPT,
                    output_key="growth_hubs",
                    source_key="file_contents",
                ),
            ]
        )
