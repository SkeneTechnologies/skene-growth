"""
Technical health analysis step.

Combines TechDebtAnalyzer, DeadCodeDetector, EntropyAnalyzer,
and ComplexityAnalyzer to produce a comprehensive TechnicalHealthReport.

Note: Analyzer imports are deferred to method bodies to break circular
import cycles between analyzers/ and strategies/steps/.
"""

from __future__ import annotations

from skene_growth.codebase import CodebaseExplorer
from skene_growth.llm import LLMClient
from skene_growth.manifest import TechnicalHealthReport
from skene_growth.strategies.context import AnalysisContext, StepResult
from skene_growth.strategies.steps.base import AnalysisStep


class TechnicalHealthStep(AnalysisStep):
    """
    Comprehensive technical health analysis.

    Runs all technical health analyzers and combines their results
    into a unified TechnicalHealthReport.

    Example:
        step = TechnicalHealthStep(output_key="technical_health")
        result = await step.execute(codebase, llm, context)
        health_report = result.data["technical_health"]
    """

    name: str = "technical_health_analysis"

    def __init__(self, output_key: str = "technical_health"):
        """
        Initialize technical health step.

        Args:
            output_key: Key to store health report in context
        """
        self.output_key = output_key

    async def execute(
        self,
        codebase: CodebaseExplorer,
        llm: LLMClient,
        context: AnalysisContext,
    ) -> StepResult:
        """
        Execute comprehensive technical health analysis.

        Args:
            codebase: Codebase explorer
            llm: LLM client
            context: Analysis context

        Returns:
            StepResult with TechnicalHealthReport
        """
        # Lazy imports to break circular dependency with analyzers/
        from skene_growth.analyzers.complexity import ComplexityAnalyzer
        from skene_growth.analyzers.dead_code import DeadCodeDetector
        from skene_growth.analyzers.entropy import EntropyAnalyzer
        from skene_growth.analyzers.tech_debt import TechDebtAnalyzer

        tech_debt_analyzer = TechDebtAnalyzer()
        dead_code_detector = DeadCodeDetector()
        entropy_analyzer = EntropyAnalyzer()
        complexity_analyzer = ComplexityAnalyzer()

        # Tech debt analysis (uses LLM)
        tech_debt_result = await tech_debt_analyzer.run(
            codebase=codebase,
            llm=llm,
            request="Analyze technical debt in this codebase",
        )
        debt_report = tech_debt_result.data.get("tech_debt")

        # Dead code detection (uses LLM)
        dead_code_result = await dead_code_detector.run(
            codebase=codebase,
            llm=llm,
            request="Detect dead and unused code",
        )
        dead_code_report = dead_code_result.data.get("dead_code")

        # Entropy analysis (pure Python)
        files = context.get("file_contents", [])
        entropy_report = await entropy_analyzer.analyze({"files": files})

        # Complexity analysis (pure Python)
        complexity_report = await complexity_analyzer.analyze(files)

        # Combine into TechnicalHealthReport
        # Calculate overall_health_score (weighted average)
        weights = {
            "tech_debt": 0.4,  # 40% weight
            "entropy": 0.3,  # 30% weight
            "dead_code": 0.2,  # 20% weight
            "complexity": 0.1,  # 10% weight
        }

        # Convert scores to 0-100 scale (higher = healthier)
        tech_debt_health = (
            100 - debt_report.total_debt_score if debt_report else 50.0
        )
        entropy_health = entropy_report.health_score
        dead_code_health = (
            100
            - (dead_code_report.total_unreachable * 2 if dead_code_report else 0)
            if dead_code_report
            else 50.0
        )
        complexity_health = max(
            0, 100 - (complexity_report.average_aicc * 2.5)
        )  # AICC 40 = 0 health

        overall_health_score = (
            tech_debt_health * weights["tech_debt"]
            + entropy_health * weights["entropy"]
            + dead_code_health * weights["dead_code"]
            + complexity_health * weights["complexity"]
        )

        # Combine recommendations
        recommendations = []
        if debt_report:
            recommendations.extend(debt_report.refactoring_priority[:3])
        if complexity_report:
            recommendations.extend(complexity_report.recommendations[:2])
        if entropy_report:
            recommendations.extend(entropy_report.recommendations[:2])

        # Create priority actions
        priority_actions = []

        # High priority: Critical complexity files
        if complexity_report and complexity_report.critical_files:
            for file_path in complexity_report.critical_files[:3]:
                score = next(
                    (s for s in complexity_report.files if s.file_path == file_path),
                    None,
                )
                if score:
                    priority_actions.append(
                        {
                            "type": "refactor_complexity",
                            "file": file_path,
                            "aicc_score": score.aicc_score,
                            "priority": "high",
                            "reason": f"AICC score {score.aicc_score} exceeds critical threshold (30)",
                        }
                    )

        # Medium priority: High entropy areas
        if entropy_report and entropy_report.overall_entropy > 0.6:
            priority_actions.append(
                {
                    "type": "reduce_entropy",
                    "priority": "medium",
                    "entropy_score": entropy_report.overall_entropy,
                    "reason": "High structural entropy indicates organizational issues",
                }
            )

        # Build final report
        health_report = TechnicalHealthReport(
            overall_health_score=round(overall_health_score, 2),
            tech_debt_score=debt_report.total_debt_score if debt_report else 0.0,
            entropy_score=entropy_report.overall_entropy,
            complexity_score=complexity_report.average_aicc,
            debt_report=debt_report,
            dead_code_report=dead_code_report,
            entropy_report=entropy_report,
            recommendations=recommendations,
            priority_actions=priority_actions,
        )

        return StepResult(
            step_name=self.name,
            data={self.output_key: health_report},
        )
