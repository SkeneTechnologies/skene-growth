"""
Dead code analyzer using MultiStepStrategy with LLM verification.

Detects unused imports, unreachable code, orphaned functions,
and other code that can be safely removed.
"""

from skene_growth.analyzers.prompts import DEAD_CODE_PROMPT
from skene_growth.manifest import DeadCodeReport
from skene_growth.strategies import MultiStepStrategy
from skene_growth.strategies.steps import (
    AnalyzeStep,
    ReadFilesStep,
    SelectFilesStep,
)


class DeadCodeDetector(MultiStepStrategy):
    """
    Analyzer for detecting dead and unreachable code.

    This analyzer uses LLM-based analysis to identify:
    - Unused functions and classes
    - Unused variables and constants
    - Unused imports
    - Unreachable code blocks
    - Orphaned functions (never called)

    Example:
        analyzer = DeadCodeDetector()
        result = await analyzer.run(
            codebase=CodebaseExplorer("/path/to/repo"),
            llm=create_llm_client(),
            request="Detect dead code",
        )
        dead_code = result.data.get("dead_code")
    """

    def __init__(self):
        """Initialize the dead code detector with predefined steps."""
        super().__init__(
            steps=[
                SelectFilesStep(
                    prompt="Select source files for dead code analysis. "
                    "Include main implementation files and test files to understand usage patterns.",
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
                        # Package exports
                        "**/package.json",
                        "**/index.ts",
                        "**/index.js",
                        "**/__init__.py",
                    ],
                    max_files=50,
                    output_key="selected_files",
                ),
                ReadFilesStep(
                    source_key="selected_files",
                    output_key="file_contents",
                ),
                AnalyzeStep(
                    prompt=DEAD_CODE_PROMPT,
                    output_schema=DeadCodeReport,
                    output_key="dead_code",
                    source_key="file_contents",
                ),
            ]
        )
