"""LLM-as-judge evaluation placeholder.

This module will be implemented in a future version. For now it provides
stub functions that return None and log a warning.
"""

from loguru import logger

from benchmarks.evaluation.models import LLMJudgeEvaluation
from benchmarks.runner.models import PipelineResult


def evaluate_with_llm_judge(
    result: PipelineResult,
    judge_provider: str | None = None,
    judge_model: str | None = None,
    judge_api_key: str | None = None,
) -> LLMJudgeEvaluation | None:
    """Evaluate pipeline output using an LLM judge.

    Not yet implemented. Returns None.
    """
    logger.warning("LLM judge evaluation is not yet implemented — skipping")
    return None


def _build_manifest_prompt(manifest_content: str) -> str:
    """Placeholder: prompt template for evaluating growth-manifest.json."""
    return ""


def _build_plan_prompt(plan_content: str) -> str:
    """Placeholder: prompt template for evaluating growth-plan.md."""
    return ""


def _build_prompt_prompt(prompt_content: str) -> str:
    """Placeholder: prompt template for evaluating the build prompt."""
    return ""
