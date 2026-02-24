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


class FactualCheck(BaseModel):
    """Result of a single factual accuracy check."""

    check_name: str
    category: str  # "tech_stack", "feature_detection", "industry", "file_references"
    passed: bool
    expected: str = ""
    actual: str = ""
    detail: str = ""


class FactualEvaluation(BaseModel):
    """Factual evaluation results for one pipeline run.

    Scores are broken down by category so the report can show
    a radar-chart-style breakdown per model.
    """

    codebase_name: str
    model_name: str
    run_number: int
    checks: list[FactualCheck]
    total_checks: int
    passed_checks: int
    score: float  # passed_checks / total_checks
    category_scores: dict[str, float]  # category -> score (0.0-1.0)


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
