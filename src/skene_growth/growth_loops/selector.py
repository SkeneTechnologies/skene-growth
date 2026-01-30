"""
LLM-driven growth loop selection.

Selects 3 growth loops incrementally based on manifest and objectives context.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from skene_growth.llm.base import LLMClient
from skene_growth.planner.loops import SelectedGrowthLoop


def _build_selection_prompt(
    manifest_data: dict[str, Any],
    objectives_content: str = "",
    csv_loops: list[dict[str, Any]] | None = None,
    previously_selected: list[SelectedGrowthLoop] | None = None,
    iteration: int = 1,
) -> str:
    """Build a prompt for selecting ONE growth loop."""

    # Format manifest summary
    manifest_summary = _format_manifest_summary(manifest_data)

    # Format available loops (all 107 from CSV)
    loops_text = _format_available_loops(csv_loops or [])

    # Format previously selected loops
    previously_selected_text = ""
    if previously_selected:
        previously_selected_text = "\n## Previously Selected Loops (DO NOT select these again)\n"
        for i, loop in enumerate(previously_selected, 1):
            previously_selected_text += f"\n### Loop {i}: {loop.loop_name}\n"
            previously_selected_text += f"- **PLG Stage:** {loop.plg_stage}\n"
            previously_selected_text += f"- **Goal:** {loop.goal}\n"
            previously_selected_text += f"- **Why Selected:** {loop.why_selected}\n"

    objectives_section = ""
    if objectives_content:
        objectives_section = f"\n## Current Growth Objectives\n{objectives_content}\n"

    return f"""You are a Product-Led Growth (PLG) strategist. Your task is to select the SINGLE most impactful growth
loop for this project.

## Iteration {iteration} of 3
Select ONE growth loop that would have the highest impact given the current context.

## Project Manifest (Current State)
{manifest_summary}
{objectives_section}{previously_selected_text}

## Available Growth Loops (107 total)
Below are all available growth loops from the catalog. Select ONE that best addresses the project's needs:

{loops_text}

## Selection Criteria
1. **Do NOT select** any of the previously selected loops
2. **Ensure diversity**: Try to choose a loop from a different PLG stage than already selected
3. **Consider tech stack**: Choose loops compatible with the project's Implementation Stack

## Your Task
Select exactly ONE growth loop and provide:
1. The exact loop name (must match one from the list above)
2. Why this specific loop was selected for THIS project (be specific)
3. 3-5 implementation steps tailored to the codebase
4. 2-3 success metrics to track
5. A technical implementation example using the project's tech stack

**IMPORTANT:**
When providing explanations, implementation steps, and success metrics, always refer to the loop by its
name. For example, mention "The [Loop Name] loop" or "[Loop Name]" when explaining why it was selected, what it does, or
how to implement it. This helps readers understand which specific loop the information relates to.

For the **technical_example**, write a code snippet or detailed technical implementation guide that demonstrates
how to implement this loop using the project's detected tech stack (Framework, Language, Database, etc.).
The example should be concrete, practical, and directly applicable to the codebase.

Return ONLY a JSON object (not an array) in this format:
```json
{{
  "loop_name": "Exact Loop Name from CSV",
  "plg_stage": "PLG Stage",
  "goal": "Goal from CSV",
  "why_selected": "Detailed explanation specific to this project. Reference the loop name",
  "implementation_steps": [
    "Step 1: Specific action for [Loop Name]...",
    "Step 2: Specific action...",
    "Step 3: Specific action..."
  ],
  "success_metrics": [
    "Metric 1: How to measure [Loop Name] effectiveness...",
    "Metric 2: How to measure..."
  ],
  "technical_example": "Code snippet or detailed technical implementation using the project's tech stack. " \
    "Include file names, function signatures, and actual code that demonstrates the implementation."
}}
```

Return ONLY the JSON object, no other text or markdown code blocks.
"""


def _format_manifest_summary(manifest_data: dict[str, Any]) -> str:
    """Format manifest data into a readable summary."""
    lines = []

    # Project info
    lines.append(f"**Project:** {manifest_data.get('project_name', 'Unknown')}")
    if manifest_data.get("description"):
        lines.append(f"**Description:** {manifest_data['description']}")

    # Tech stack
    tech_stack = manifest_data.get("tech_stack", {})
    if tech_stack:
        tech_items = [f"{k}: {v}" for k, v in tech_stack.items() if v and k != "services"]
        if tech_items:
            lines.append(f"**Tech Stack:** {', '.join(tech_items)}")
        services = tech_stack.get("services", [])
        if services:
            lines.append(f"**Services:** {', '.join(services)}")

    # Current growth features
    current_growth_features = manifest_data.get("current_growth_features", [])
    if current_growth_features:
        lines.append(f"\n**Current Growth Features ({len(current_growth_features)} identified):**")
        for hub in current_growth_features[:5]:
            lines.append(f"- {hub.get('feature_name', 'Unknown')}: {hub.get('detected_intent', '')}")
        if len(current_growth_features) > 5:
            lines.append(f"- ... and {len(current_growth_features) - 5} more")

    # Growth opportunities
    growth_opportunities = manifest_data.get("growth_opportunities", [])
    if growth_opportunities:
        lines.append(f"\n**Growth Opportunities ({len(growth_opportunities)} identified):**")
        for gap in growth_opportunities[:5]:
            priority = gap.get("priority", "medium")
            lines.append(f"- [{priority}] {gap.get('feature_name', 'Unknown')}: {gap.get('description', '')}")
        if len(growth_opportunities) > 5:
            lines.append(f"- ... and {len(growth_opportunities) - 5} more")

    return "\n".join(lines)


def _format_available_loops(csv_loops: list[dict[str, Any]]) -> str:
    """Format CSV loops into a summarized list."""
    lines = []

    # Group by PLG stage
    by_stage: dict[str, list[dict]] = {}
    for loop in csv_loops:
        stage = loop.get("plg_stage", "Other")
        if stage not in by_stage:
            by_stage[stage] = []
        by_stage[stage].append(loop)

    for stage, loops in by_stage.items():
        lines.append(f"\n### {stage} ({len(loops)} loops)")
        for loop in loops:
            name = loop.get("loop_name", "Unknown")
            goal = loop.get("goal", "")
            action = loop.get("action_summary", "") or loop.get("action", "")[:80]
            lines.append(f"- **{name}** (Goal: {goal})")
            if action:
                lines.append(f"  Action: {action}")

    return "\n".join(lines)


def _parse_single_loop_response(
    response: str,
    csv_loops: list[dict[str, Any]],
) -> SelectedGrowthLoop:
    """Parse LLM response to extract ONE selected loop."""
    response = response.strip()

    # Try direct JSON parse first
    data = None
    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fence
    if data is None:
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

    # Try finding JSON object in text
    if data is None:
        obj_match = re.search(r"(\{.*\})", response, re.DOTALL)
        if obj_match:
            try:
                data = json.loads(obj_match.group(1).strip())
            except json.JSONDecodeError:
                pass

    if not data or not isinstance(data, dict):
        raise ValueError("Could not parse LLM response as JSON object.")

    loop_name = data.get("loop_name", "")

    # Find matching loop from CSV to get additional data
    csv_data = {}
    for loop in csv_loops:
        if loop.get("loop_name", "").lower() == loop_name.lower():
            csv_data = loop
            break

    return SelectedGrowthLoop(
        loop_name=loop_name,
        plg_stage=data.get("plg_stage") or csv_data.get("plg_stage", ""),
        goal=data.get("goal") or csv_data.get("goal", ""),
        user_story=csv_data.get("user_story", ""),
        action=csv_data.get("action", ""),
        value=csv_data.get("value", ""),
        implementation=csv_data.get("implementation", ""),
        why_selected=data.get("why_selected", ""),
        implementation_steps=data.get("implementation_steps", []),
        success_metrics=data.get("success_metrics", []),
        technical_example=data.get("technical_example", ""),
    )


def _format_actionable_markdown(
    selected_loops: list[SelectedGrowthLoop],
    manifest_data: dict[str, Any],
) -> str:
    """Format all selected loops as actionable markdown."""
    generated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sources_text = "growth-manifest.json"

    lines = [
        "# Growth Loops Implementation Plan",
        "",
        f"*Generated on {generated_date}*",
        f"*Based on: {sources_text}*",
        "",
        "---",
        "",
    ]

    for i, loop in enumerate(selected_loops, 1):
        lines.extend(
            [
                f"## Loop {i}: {loop.loop_name}",
                "",
                f"**PLG Stage:** {loop.plg_stage}",
                f"**Goal:** {loop.goal}",
                "",
                "### Why This Loop?",
                loop.why_selected,
                "",
            ]
        )

        if loop.user_story:
            lines.extend(
                [
                    "### User Story",
                    loop.user_story,
                    "",
                ]
            )

        lines.extend(
            [
                "### What It Does",
            ]
        )

        if loop.action:
            lines.append(f"**Action:** {loop.action}")
        if loop.value:
            lines.append(f"**Value:** {loop.value}")
        lines.append("")

        if loop.implementation_steps:
            lines.append("### Implementation Steps")
            for j, step in enumerate(loop.implementation_steps, 1):
                lines.append(f"{j}. {step}")
            lines.append("")

        if loop.technical_example:
            lines.extend(
                [
                    "### Technical Implementation Example",
                    loop.technical_example,
                    "",
                ]
            )

        if loop.success_metrics:
            lines.append("### Success Metrics")
            for metric in loop.success_metrics:
                lines.append(f"- {metric}")
            lines.append("")

        if loop.implementation:
            lines.extend(
                [
                    "### Technical Details",
                    f"**Implementation Stack:** {loop.implementation}",
                    "",
                ]
            )

        lines.append("---")
        lines.append("")

    lines.append("*Growth loops selected by skene-growth using LLM analysis.*")

    return "\n".join(lines)


async def select_single_loop(
    llm: LLMClient,
    manifest_data: dict[str, Any],
    csv_loops: list[dict[str, Any]],
    previously_selected: list[SelectedGrowthLoop],
    iteration: int,
    objectives_content: str = "",
) -> SelectedGrowthLoop:
    """
    Select a single growth loop using LLM.

    Args:
        llm: LLM client for generation
        manifest_data: Project manifest data
        csv_loops: All loops from CSV
        previously_selected: List of already selected loops
        iteration: Current iteration (1, 2, or 3)
        objectives_content: Optional content from growth-objectives.md (deprecated)

    Returns:
        Selected growth loop with implementation details
    """
    prompt = _build_selection_prompt(
        manifest_data=manifest_data,
        objectives_content=objectives_content,
        csv_loops=csv_loops,
        previously_selected=previously_selected,
        iteration=iteration,
    )

    logger.info(f"Selecting loop {iteration} of 3...")
    response = await llm.generate_content(prompt)

    loop = _parse_single_loop_response(response, csv_loops)
    logger.success(f"Selected: {loop.loop_name}")

    return loop


async def select_growth_loops(
    llm: LLMClient,
    manifest_data: dict[str, Any],
    csv_loops: list[dict[str, Any]],
    on_progress: callable | None = None,
    objectives_content: str = "",
) -> list[SelectedGrowthLoop]:
    """
    Select 3 growth loops incrementally using LLM.

    The function runs 3 iterations, selecting one loop at a time.
    Each iteration considers previously selected loops to ensure diversity.

    Args:
        llm: LLM client for generation
        manifest_data: Project manifest data (from growth-manifest.json)
        csv_loops: All loops from CSV
        on_progress: Optional callback for progress updates
        objectives_content: Optional content from growth-objectives.md (deprecated, not used)

    Returns:
        List of 3 selected growth loops with implementation details
    """
    selected_loops: list[SelectedGrowthLoop] = []

    for iteration in range(1, 4):
        if on_progress:
            on_progress(f"Selecting loop {iteration} of 3...", iteration / 4)

        loop = await select_single_loop(
            llm=llm,
            manifest_data=manifest_data,
            csv_loops=csv_loops,
            previously_selected=selected_loops,
            iteration=iteration,
            objectives_content=objectives_content,
        )

        selected_loops.append(loop)

    if on_progress:
        on_progress("Formatting output...", 0.9)

    logger.success(f"Selected {len(selected_loops)} growth loops")
    return selected_loops


def write_growth_loops_output(
    selected_loops: list[SelectedGrowthLoop],
    manifest_data: dict[str, Any],
    output_path: Path | str,
) -> Path:
    """
    Write selected growth loops to markdown file.

    Args:
        selected_loops: List of selected loops
        manifest_data: Project manifest data
        output_path: Path to write the file

    Returns:
        Path to the written file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    markdown_content = _format_actionable_markdown(
        selected_loops=selected_loops,
        manifest_data=manifest_data,
    )

    output_path.write_text(markdown_content)
    logger.info(f"Wrote growth loops plan to {output_path}")

    return output_path
