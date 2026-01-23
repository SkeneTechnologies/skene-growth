"""
Step for context synthesis - understanding what the product is.

This step runs before growth hub analysis to provide product context
that helps guide the growth analysis.
"""

from loguru import logger

from skene_growth.codebase import CodebaseExplorer
from skene_growth.llm import LLMClient
from skene_growth.strategies.context import AnalysisContext, StepResult
from skene_growth.strategies.steps.base import AnalysisStep
from skene_growth.synthesis.analyzer import ContextSynthesizer, extract_context_signals


class ContextSynthesisStep(AnalysisStep):
    """
    Step that synthesizes product context from codebase signals.

    This step runs the two-pass context synthesis:
    1. Extract raw signals (database tables, API routes, dependencies)
    2. Apply heuristic tags
    3. Run LLM semantic synthesis

    Example:
        step = ContextSynthesisStep(
            output_key="product_context",
            source_key="file_contents",
        )
    """

    name = "context_synthesis"

    def __init__(
        self,
        output_key: str = "product_context",
        source_key: str = "file_contents",
    ):
        """
        Initialize the context synthesis step.

        Args:
            output_key: Context key to store product context result
            source_key: Context key containing file contents to analyze
        """
        self.output_key = output_key
        self.source_key = source_key

    async def execute(
        self,
        codebase: CodebaseExplorer,
        llm: LLMClient,
        context: AnalysisContext,
    ) -> StepResult:
        """Execute the context synthesis step."""
        try:
            # Get file contents from context
            file_contents = context.get(self.source_key, {})

            if not file_contents:
                logger.warning(
                    f"ContextSynthesisStep: No file contents in context key '{self.source_key}'. "
                    "Skipping context synthesis."
                )
                # Return empty context as fallback
                return StepResult(
                    step_name=self.name,
                    data={self.output_key: None},
                )

            # Extract raw signals from file contents
            logger.info("Extracting context signals from codebase")
            signals = await extract_context_signals(codebase, file_contents)

            # Run context synthesis
            synthesizer = ContextSynthesizer()
            product_context = await synthesizer.analyze(signals, llm)

            logger.info(
                f"Context synthesis complete: {product_context.industry} "
                f"({product_context.business_model}) - Confidence: {product_context.confidence_score:.2f}"
            )

            return StepResult(
                step_name=self.name,
                data={self.output_key: product_context.model_dump()},
                tokens_used=len(str(signals)) // 4,  # Rough estimate
            )

        except Exception as e:
            logger.error(f"ContextSynthesisStep failed: {e}")
            # Don't fail the entire pipeline - return None for product_context
            return StepResult(
                step_name=self.name,
                data={self.output_key: None},
                error=str(e),
            )
