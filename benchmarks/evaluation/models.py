"""Pydantic models for evaluation results."""

from pydantic import BaseModel


class StructuralCheck(BaseModel):
    """Result of a single structural check."""

    check_name: str
    passed: bool
    detail: str = ""


class StructuralEvaluation(BaseModel):
    """Structural evaluation results for one pipeline run."""

    codebase_name: str
    model_name: str
    run_number: int
    checks: list[StructuralCheck]
    total_checks: int
    passed_checks: int
    score: float  # passed_checks / total_checks


class LLMJudgeScore(BaseModel):
    """Placeholder: a single criterion score from the LLM judge."""

    criterion: str
    score: float  # 1-10
    justification: str = ""


class LLMJudgeEvaluation(BaseModel):
    """Placeholder: LLM judge evaluation for one pipeline run."""

    codebase_name: str
    model_name: str
    run_number: int
    scores: list[LLMJudgeScore]
    average_score: float
    raw_response: str = ""
