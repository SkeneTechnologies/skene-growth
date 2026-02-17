"""
Entropy analysis step (non-LLM).

Unlike other steps, this doesn't use LLM but performs
statistical analysis on codebase structure.

Note: EntropyAnalyzer is imported lazily to break a circular import
cycle between analyzers/ and strategies/steps/.
"""

from __future__ import annotations

from skene_growth.codebase import CodebaseExplorer
from skene_growth.llm import LLMClient
from skene_growth.strategies.context import AnalysisContext, StepResult
from skene_growth.strategies.steps.base import AnalysisStep


class EntropyAnalysisStep(AnalysisStep):
    """
    Structural entropy analysis step.

    Analyzes codebase organization, module cohesion, dependency
    dispersion, and naming consistency without using LLM.

    Example:
        step = EntropyAnalysisStep(output_key="entropy_report")
        result = await step.execute(codebase, llm, context)
        entropy_report = result.data["entropy_report"]
    """

    name: str = "entropy_analysis"

    def __init__(self, output_key: str = "entropy_report"):
        """
        Initialize entropy analysis step.

        Args:
            output_key: Key to store entropy report in context
        """
        self.output_key = output_key
        self._analyzer = None

    @property
    def analyzer(self):
        """Lazy import to break circular dependency with analyzers/entropy.py."""
        if self._analyzer is None:
            from skene_growth.analyzers.entropy import EntropyAnalyzer
            self._analyzer = EntropyAnalyzer()
        return self._analyzer

    async def execute(
        self,
        codebase: CodebaseExplorer,
        llm: LLMClient,
        context: AnalysisContext,
    ) -> StepResult:
        """
        Execute entropy analysis.

        Args:
            codebase: Codebase explorer
            llm: LLM client (not used for entropy)
            context: Analysis context with file data

        Returns:
            StepResult with entropy report
        """
        # Get files from context (should be populated by previous steps)
        files = context.get("file_contents", [])

        # Convert to format expected by EntropyAnalyzer
        analysis_context = {"files": files}

        # Run entropy analysis (pure Python, no LLM)
        entropy_report = await self.analyzer.analyze(analysis_context)

        return StepResult(
            step_name=self.name,
            data={self.output_key: entropy_report},
        )
