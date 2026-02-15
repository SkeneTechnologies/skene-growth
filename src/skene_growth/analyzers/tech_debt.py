"""
Technical debt analyzer using MultiStepStrategy.

Detects code smells, architecture violations, dependency issues,
and test coverage gaps to generate a comprehensive tech debt report.
"""

from skene_growth.analyzers.prompts import TECH_DEBT_PROMPT
from skene_growth.manifest import TechDebtReport
from skene_growth.strategies import MultiStepStrategy
from skene_growth.strategies.steps import (
    AnalyzeStep,
    ReadFilesStep,
    SelectFilesStep,
)


class TechDebtAnalyzer(MultiStepStrategy):
    """
    Analyzer for detecting technical debt in a codebase.

    This analyzer examines source code and configuration files to identify:
    - Code smells (long functions, deep nesting, duplicates)
    - Architecture violations (circular dependencies, tight coupling)
    - Dependency health (outdated packages, vulnerabilities)
    - Test coverage gaps

    Example:
        analyzer = TechDebtAnalyzer()
        result = await analyzer.run(
            codebase=CodebaseExplorer("/path/to/repo"),
            llm=create_llm_client(),
            request="Analyze technical debt",
        )
        debt_report = result.data.get("tech_debt")
    """

    def __init__(self):
        """Initialize the tech debt analyzer with predefined steps."""
        super().__init__(
            steps=[
                SelectFilesStep(
                    prompt="Select source files and configuration files for technical debt analysis. "
                    "Include main implementation files, test files, and dependency manifests. "
                    "Focus on critical paths and complex modules.",
                    patterns=[
                        # Source files
                        "**/*.py",
                        "**/*.ts",
                        "**/*.tsx",
                        "**/*.js",
                        "**/*.jsx",
                        "**/*.go",
                        "**/*.rs",
                        "**/*.java",
                        "**/*.rb",
                        # Test files
                        "**/*.test.*",
                        "**/*.spec.*",
                        "**/test_*.py",
                        # Configuration files
                        "package.json",
                        "requirements.txt",
                        "pyproject.toml",
                        "Cargo.toml",
                        "go.mod",
                        "Gemfile",
                        "pom.xml",
                        # Architecture files
                        "tsconfig.json",
                        "eslint.config.*",
                        ".eslintrc.*",
                    ],
                    max_files=50,
                    output_key="selected_files",
                ),
                ReadFilesStep(
                    source_key="selected_files",
                    output_key="file_contents",
                ),
                AnalyzeStep(
                    prompt=TECH_DEBT_PROMPT,
                    output_schema=TechDebtReport,
                    output_key="tech_debt",
                    source_key="file_contents",
                ),
            ]
        )
