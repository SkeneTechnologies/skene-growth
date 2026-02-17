"""
Analysis steps for multi-step strategies.

Each step performs a specific operation in the analysis pipeline:
- SelectFilesStep: LLM selects relevant files
- ReadFilesStep: Read selected files into context
- AnalyzeStep: LLM analyzes content and produces structured output
- GenerateStep: LLM generates final output
- EntropyAnalysisStep: Pure-Python structural entropy analysis
- TechnicalHealthStep: Combined technical health analysis

Note: EntropyAnalysisStep and TechnicalHealthStep are lazily importable
to avoid circular imports with analyzers/ modules.
"""

from skene_growth.strategies.steps.analyze import AnalyzeStep
from skene_growth.strategies.steps.base import AnalysisStep
from skene_growth.strategies.steps.generate import GenerateStep
from skene_growth.strategies.steps.read_files import ReadFilesStep
from skene_growth.strategies.steps.select_files import SelectFilesStep


def __getattr__(name: str):
    """Lazy imports for steps that depend on analyzers/ (breaks circular import)."""
    if name == "EntropyAnalysisStep":
        from skene_growth.strategies.steps.entropy_step import EntropyAnalysisStep
        return EntropyAnalysisStep
    if name == "TechnicalHealthStep":
        from skene_growth.strategies.steps.technical_health_step import TechnicalHealthStep
        return TechnicalHealthStep
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AnalysisStep",
    "SelectFilesStep",
    "ReadFilesStep",
    "AnalyzeStep",
    "GenerateStep",
    "EntropyAnalysisStep",
    "TechnicalHealthStep",
]
