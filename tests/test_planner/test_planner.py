"""Tests for multi-step Planner orchestration."""

import json
from unittest.mock import AsyncMock

import pytest

from skene.planner.planner import Planner
from skene.planner.schema import GrowthPlan
from skene.planner.steps import PlanStepDefinition

_MANIFEST = {
    "project_name": "TestProject",
    "description": "A test product.",
}

_TWO_STEPS = [
    PlanStepDefinition(title="Step One", instruction="Do step one."),
    PlanStepDefinition(title="Step Two", instruction="Do step two."),
]


def _make_llm(responses: list[str]) -> AsyncMock:
    """Create an LLM mock. First N-1 responses go to generate_content_with_usage, last to generate_content."""
    llm = AsyncMock()
    # Section steps use generate_content_with_usage
    section_responses = responses[:-1]
    llm.generate_content_with_usage = AsyncMock(
        side_effect=[(r, None) for r in section_responses]
    )
    # Harmonization uses generate_content
    llm.generate_content = AsyncMock(return_value=responses[-1])
    return llm


def _exec_summary_response(text: str = "The core summary.") -> str:
    return json.dumps({"executive_summary": text})


def _section_response(title: str, content: str) -> str:
    return json.dumps({"title": title, "content": content})


def _tech_exec_response() -> str:
    return json.dumps(
        {
            "next_build": "Build the activation loop.",
            "confidence": "85%",
            "exact_logic": "Step A then B.",
            "data_triggers": "Event X fires.",
            "stack_steps": "Redis + Celery.",
            "sequence": "Now: A. Next: B. Later: C.",
        }
    )


def _harmonize_response(
    exec_summary: str,
    sections: list[dict],
    tech_exec: dict,
) -> str:
    return json.dumps(
        {
            "executive_summary": exec_summary,
            "sections": sections,
            "technical_execution": tech_exec,
        }
    )


class TestGenerateGrowthPlan:
    @pytest.mark.asyncio
    async def test_calls_llm_for_each_step(self):
        """Should make 2+N+1+1 LLM calls: exec, N steps, tech exec, harmonize."""
        tech_exec_data = {
            "next_build": "Build loop.",
            "confidence": "80%",
            "exact_logic": "A then B.",
            "data_triggers": "Event Y.",
            "stack_steps": "API calls.",
            "sequence": "Now/Next/Later",
        }
        sections_data = [
            {"title": "Step One", "content": "Content one."},
            {"title": "Step Two", "content": "Content two."},
        ]
        responses = [
            _exec_summary_response("Summary here."),
            _section_response("Step One", "Content one."),
            _section_response("Step Two", "Content two."),
            _tech_exec_response(),
            _harmonize_response("Summary here.", sections_data, tech_exec_data),
        ]
        llm = _make_llm(responses)
        planner = Planner()
        markdown, plan = await planner.generate_growth_plan(
            llm=llm,
            manifest_data=_MANIFEST,
            plan_steps=_TWO_STEPS,
        )
        assert llm.generate_content_with_usage.call_count == 4  # exec + 2 sections + tech_exec
        assert isinstance(plan, GrowthPlan)
        assert plan.executive_summary == "Summary here."
        assert len(plan.sections) == 2
        assert plan.sections[0].title == "Step One"

    @pytest.mark.asyncio
    async def test_on_step_callback_called_for_each_section(self):
        """on_step should be called N+2 times (exec + steps + tech exec)."""
        tech_exec_data = {
            "next_build": "B.",
            "confidence": "90%",
            "exact_logic": "E.",
            "data_triggers": "D.",
            "stack_steps": "S.",
            "sequence": "N/N/L.",
        }
        sections_data = [{"title": "Step One", "content": "C."}]
        responses = [
            _exec_summary_response(),
            _section_response("Step One", "C."),
            _tech_exec_response(),
            _harmonize_response("The core summary.", sections_data, tech_exec_data),
        ]
        llm = _make_llm(responses)
        planner = Planner()
        step_calls: list[tuple[int, str, str]] = []

        def on_step(
            step_number: int, title: str, chunk: str, usage: dict | None = None
        ) -> None:
            step_calls.append((step_number, title, chunk))

        await planner.generate_growth_plan(
            llm=llm,
            manifest_data=_MANIFEST,
            plan_steps=[PlanStepDefinition(title="Step One", instruction="Do step one.")],
            on_step=on_step,
        )
        assert len(step_calls) == 3  # exec + 1 step + tech exec
        assert step_calls[0][1] == "Executive Summary"
        assert step_calls[1][1] == "Step One"
        assert step_calls[2][1] == "Technical Execution"

    @pytest.mark.asyncio
    async def test_uses_default_steps_when_none_provided(self):
        """Should use DEFAULT_PLAN_STEPS (4 steps) when plan_steps is not given."""
        from skene.planner.steps import DEFAULT_PLAN_STEPS

        tech_exec_data = {
            "next_build": "B.",
            "confidence": "90%",
            "exact_logic": "E.",
            "data_triggers": "D.",
            "stack_steps": "S.",
            "sequence": "N/N/L.",
        }
        sections_data = [{"title": s.title, "content": "content"} for s in DEFAULT_PLAN_STEPS]
        responses = (
            [_exec_summary_response()]
            + [_section_response(s.title, "content") for s in DEFAULT_PLAN_STEPS]
            + [_tech_exec_response()]
            + [_harmonize_response("summary", sections_data, tech_exec_data)]
        )
        llm = _make_llm(responses)
        planner = Planner()
        _, plan = await planner.generate_growth_plan(llm=llm, manifest_data=_MANIFEST)
        # exec + 4 sections + tech_exec = 6 calls (harmonize uses generate_content)
        assert llm.generate_content_with_usage.call_count == 6
        assert len(plan.sections) == 4

    @pytest.mark.asyncio
    async def test_harmonization_fallback_on_invalid_response(self):
        """If harmonization returns invalid JSON, should use assembled plan."""
        responses = [
            _exec_summary_response("Exec summary."),
            _tech_exec_response(),
            "THIS IS NOT JSON",  # harmonization fails
        ]
        llm = _make_llm(responses)
        planner = Planner()
        _, plan = await planner.generate_growth_plan(
            llm=llm,
            manifest_data=_MANIFEST,
            plan_steps=[],  # zero dynamic steps
        )
        assert plan.executive_summary == "Exec summary."
        assert plan.sections == []

    @pytest.mark.asyncio
    async def test_returns_markdown_string(self):
        """generate_growth_plan should return a non-empty markdown string."""
        tech_exec_data = {
            "next_build": "B.",
            "confidence": "90%",
            "exact_logic": "E.",
            "data_triggers": "D.",
            "stack_steps": "S.",
            "sequence": "N.",
        }
        responses = [
            _exec_summary_response("Summary."),
            _section_response("Step One", "Content."),
            _tech_exec_response(),
            _harmonize_response(
                "Summary.",
                [{"title": "Step One", "content": "Content."}],
                tech_exec_data,
            ),
        ]
        llm = _make_llm(responses)
        planner = Planner()
        markdown, _ = await planner.generate_growth_plan(
            llm=llm,
            manifest_data=_MANIFEST,
            plan_steps=[PlanStepDefinition(title="Step One", instruction="Do step one.")],
        )
        assert isinstance(markdown, str)
        assert "Executive Summary" in markdown
        assert "Technical Execution" in markdown
