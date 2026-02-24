"""Structured schema for council memo (growth plan) output."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field


class TechnicalExecution(BaseModel):
    """Section 7: Technical Execution details."""

    next_build: str = Field(description="What activation loop to build next")
    confidence: str = Field(description="Confidence level, e.g. '85%'")
    exact_logic: str = Field(description="Specific flow changes for first-action completion")
    data_triggers: str = Field(description="Events indicating first meaningful action")
    stack_steps: str = Field(description="Tools, scripts, or structural changes required")
    sequence: str = Field(description="Now / Next / Later priorities")


class PlanSection(BaseModel):
    """A numbered section of the growth plan memo."""

    title: str = Field(description="Section heading, e.g. 'The Next Action'")
    content: str = Field(description="Free-form markdown content")


class GrowthPlan(BaseModel):
    """Complete structured council memo."""

    executive_summary: str = Field(description="High-level summary focused on first-time activation")
    sections: list[PlanSection] = Field(description="Numbered memo sections (1-6)")
    technical_execution: TechnicalExecution = Field(description="Section 7: Technical Execution")
    memo: str = Field(description="Section 8: The closing confidential engineering memo")


def render_plan_to_markdown(plan: GrowthPlan, project_name: str, generated_at: str) -> str:
    """Render a GrowthPlan to the markdown memo format.

    Args:
        plan: Validated GrowthPlan instance
        project_name: Name of the project
        generated_at: ISO timestamp string

    Returns:
        Markdown string matching the council memo format
    """
    lines: list[str] = []

    lines.append(f"# Council of Growth Engineers — {project_name}")
    lines.append(f"**Generated:** {generated_at}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(plan.executive_summary)
    lines.append("")

    # Numbered sections (1-6)
    for i, section in enumerate(plan.sections, start=1):
        lines.append(f"### {i}. {section.title}")
        lines.append("")
        lines.append(section.content)
        lines.append("")

    # Section 7: Technical Execution
    te = plan.technical_execution
    lines.append("### 7. Technical Execution")
    lines.append("")
    lines.append(f"**What is the next activation loop to build?**\n{te.next_build}")
    lines.append("")
    lines.append(f"**Confidence:** {te.confidence}")
    lines.append("")
    lines.append(f"**Exact Logic:**\n{te.exact_logic}")
    lines.append("")
    lines.append(f"**Exact Data Triggers:**\n{te.data_triggers}")
    lines.append("")
    lines.append(f"**Exact Stack/Steps:**\n{te.stack_steps}")
    lines.append("")
    lines.append(f"**Sequence:**\n{te.sequence}")
    lines.append("")

    # Section 8: The Memo
    lines.append("### 8. The Memo")
    lines.append("")
    lines.append(plan.memo)
    lines.append("")

    return "\n".join(lines)


def parse_plan_json(response: str) -> GrowthPlan:
    """Parse an LLM response as JSON into a GrowthPlan.

    Strips markdown code fences (```json ... ```) if present,
    then validates with Pydantic.

    Args:
        response: Raw LLM response text

    Returns:
        Validated GrowthPlan instance

    Raises:
        ValueError: If JSON is invalid or doesn't match schema
    """
    text = response.strip()

    # Strip code fences
    fence_pattern = re.compile(r"^```(?:json)?\s*\n(.*?)\n```\s*$", re.DOTALL)
    match = fence_pattern.match(text)
    if match:
        text = match.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM response is not valid JSON: {e}") from e

    try:
        return GrowthPlan.model_validate(data)
    except Exception as e:
        raise ValueError(f"JSON does not match GrowthPlan schema: {e}") from e
