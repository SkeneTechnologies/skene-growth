"""
Full manifest analyzer using MultiStepStrategy.

Combines tech stack and growth hub analysis to produce
a complete GrowthManifest.
"""

from skene_growth.analyzers.prompts import (
    GROWTH_HUB_PROMPT,
    MANIFEST_PROMPT,
    TECH_STACK_PROMPT,
)
from skene_growth.manifest import GrowthManifest, TechStack
from skene_growth.strategies import MultiStepStrategy
from skene_growth.strategies.steps import (
    AnalyzeStep,
    ContextSynthesisStep,
    GenerateStep,
    ReadFilesStep,
    SelectFilesStep,
)


class ManifestAnalyzer(MultiStepStrategy):
    """
    Full-pipeline analyzer that produces a complete GrowthManifest.

    This analyzer runs in four phases:
    1. Tech stack detection (config files)
    2. Context synthesis (understanding what the product is)
    3. Growth hub identification (source files)
    4. Manifest generation (combining results + GTM gaps)

    Example:
        analyzer = ManifestAnalyzer()
        result = await analyzer.run(
            codebase=CodebaseExplorer("/path/to/repo"),
            llm=create_llm_client(),
            request="Generate a growth manifest for this project",
        )
        manifest = GrowthManifest.model_validate(result.data.get("output"))
    """

    def __init__(self):
        """Initialize the manifest analyzer with all analysis steps."""
        super().__init__(
            steps=[
                # Phase 1: Detect tech stack
                SelectFilesStep(
                    prompt="Select configuration files and representative source files for tech stack detection. "
                    "Include package managers, framework configs, dependency files, "
                    "and a few source files to identify the language.",
                    patterns=[
                        "package.json",
                        "requirements.txt",
                        "pyproject.toml",
                        "Cargo.toml",
                        "go.mod",
                        "Gemfile",
                        "*.config.js",
                        "*.config.ts",
                        "tsconfig.json",
                        "docker-compose.yml",
                        "Dockerfile",
                        # Include source files to help identify language
                        "**/*.py",
                        "**/*.js",
                        "**/*.ts",
                        "**/*.tsx",
                        "**/*.go",
                        "**/*.rs",
                        "**/*.rb",
                    ],
                    max_files=15,
                    output_key="config_files",
                ),
                ReadFilesStep(
                    source_key="config_files",
                    output_key="file_contents",
                ),
                AnalyzeStep(
                    prompt=TECH_STACK_PROMPT,
                    output_schema=TechStack,
                    output_key="tech_stack",
                    source_key="file_contents",
                ),
                # Phase 2: Context Synthesis - understand what the product is
                # Select files for context extraction (schema files, routes, etc.)
                SelectFilesStep(
                    prompt="Select files that reveal the product domain and structure. "
                    "Include database schema files, migrations, API route definitions, "
                    "and model files that show the core entities.",
                    patterns=[
                        "**/migrations/**/*",
                        "**/schema/**/*",
                        "**/models/**/*",
                        "**/routes/**/*",
                        "**/api/**/*",
                        "**/*.sql",
                        "**/prisma/schema.prisma",
                        "**/schema.rb",
                        "**/models.py",
                        "**/models/**/*.py",
                        "**/routes.ts",
                        "**/routes.js",
                        "**/api/**/*.ts",
                        "**/api/**/*.js",
                    ],
                    max_files=20,
                    output_key="context_files",
                ),
                ReadFilesStep(
                    source_key="context_files",
                    output_key="context_file_contents",
                ),
                ContextSynthesisStep(
                    output_key="product_context",
                    source_key="context_file_contents",
                ),
                # Phase 3: Find growth hubs
                # Note: file_contents will be overwritten, but tech_stack and product_context are preserved
                SelectFilesStep(
                    prompt="Select source files with potential growth features. "
                    "Look for user management, invitations, sharing, payments, "
                    "analytics, onboarding, and engagement features.",
                    patterns=[
                        "**/*.py",
                        "**/*.ts",
                        "**/*.tsx",
                        "**/*.js",
                        "**/routes/**/*",
                        "**/api/**/*",
                        "**/features/**/*",
                    ],
                    max_files=30,
                    output_key="source_files",
                ),
                ReadFilesStep(
                    source_key="source_files",
                    output_key="file_contents",
                ),
                AnalyzeStep(
                    prompt=GROWTH_HUB_PROMPT,
                    output_key="growth_hubs",
                    source_key="file_contents",
                ),
                # Phase 4: Generate final manifest
                GenerateStep(
                    prompt=MANIFEST_PROMPT,
                    output_schema=GrowthManifest,
                    include_context_keys=["tech_stack", "product_context", "growth_hubs"],
                    output_key="output",
                ),
            ]
        )
