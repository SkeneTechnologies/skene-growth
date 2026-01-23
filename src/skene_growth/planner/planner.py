"""
Plan generator.

Creates detailed implementation plans for growth loops in a codebase.
Includes both LLM-based selection and comprehensive mapping.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field

from skene_growth.llm import LLMClient
from skene_growth.manifest import GrowthManifest
from skene_growth.planner.loops import GrowthLoopCatalog, SelectedGrowthLoop
from skene_growth.planner.mapper import LoopMapper, LoopMapping


def load_daily_logs_summary(daily_logs_dir: Path) -> str | None:
    """
    Load and summarize daily logs for LLM context.

    Args:
        daily_logs_dir: Path to daily_logs directory

    Returns:
        Summary string or None if no logs found
    """
    if not daily_logs_dir.exists():
        return None

    # Find all log files
    log_files = sorted(daily_logs_dir.glob("daily_logs_*.json"), reverse=True)

    if not log_files:
        return None

    # Load most recent logs (up to 7 days)
    recent_logs = []
    for log_file in log_files[:7]:
        try:
            data = json.loads(log_file.read_text())
            recent_logs.append(
                {
                    "date": log_file.stem.replace("daily_logs_", "").replace("_", "-"),
                    "data": data,
                }
            )
        except (json.JSONDecodeError, IOError):
            continue

    if not recent_logs:
        return None

    # Build summary
    lines = []
    lines.append(f"**Recent Performance ({len(recent_logs)} days of data):**\n")

    # Aggregate metrics across all logs
    all_metrics: dict[str, list[Any]] = {}

    for log in recent_logs:
        data = log.get("data", {})
        date = log.get("date", "")

        # Handle different log formats
        if isinstance(data, dict):
            for key, value in data.items():
                if key not in all_metrics:
                    all_metrics[key] = []
                all_metrics[key].append({"date": date, "value": value})
        elif isinstance(data, list):
            # Handle list format: [{"metric_id": "...", "value": "..."}, ...]
            for entry in data:
                if isinstance(entry, dict):
                    metric_id = entry.get("metric_id") or entry.get("metric")
                    value = entry.get("value")
                    if metric_id and value is not None:
                        if metric_id not in all_metrics:
                            all_metrics[metric_id] = []
                        all_metrics[metric_id].append({"date": date, "value": value})

    # Identify weak areas (metrics below target or declining)
    weak_areas = []
    for metric, values in all_metrics.items():
        if len(values) >= 2:
            # Check for declining trend
            recent_values = [v.get("value") for v in values[:3] if isinstance(v.get("value"), (int, float))]
            if len(recent_values) >= 2 and recent_values[0] < recent_values[-1]:
                weak_areas.append(f"- **{metric}**: Declining trend ({recent_values[-1]} → {recent_values[0]})")

    if weak_areas:
        lines.append("**Weak Areas Identified:**")
        lines.extend(weak_areas)
        lines.append("")

    # Show recent data summary
    lines.append("**Latest Metrics:**")
    if recent_logs:
        latest = recent_logs[0]
        latest_data = latest.get("data", {})
        if isinstance(latest_data, dict):
            for key, value in latest_data.items():
                if isinstance(value, dict):
                    lines.append(f"- {key}: {json.dumps(value)}")
                else:
                    lines.append(f"- {key}: {value}")
        elif isinstance(latest_data, list):
            # Handle list format: [{"metric_id": "...", "value": "..."}, ...]
            for entry in latest_data:
                if isinstance(entry, dict):
                    metric_id = entry.get("metric_id") or entry.get("metric")
                    value = entry.get("value")
                    if metric_id and value is not None:
                        lines.append(f"- {metric_id}: {value}")

    return "\n".join(lines)


class CodeChange(BaseModel):
    """A specific code change to implement."""

    file_path: str = Field(description="Path to the file to modify")
    change_type: str = Field(description="Type of change: create, modify, delete")
    description: str = Field(description="What change to make")
    code_snippet: str | None = Field(
        default=None,
        description="Example code snippet if applicable",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Other changes this depends on",
    )


class LoopPlan(BaseModel):
    """Implementation plan for a single growth loop."""

    loop_id: str = Field(description="The growth loop ID")
    loop_name: str = Field(description="The growth loop name")
    priority: int = Field(ge=0, le=10, description="Implementation priority")
    estimated_complexity: str = Field(description="low, medium, or high")
    code_changes: list[CodeChange] = Field(
        default_factory=list,
        description="Ordered list of code changes",
    )
    new_dependencies: list[str] = Field(
        default_factory=list,
        description="New packages/dependencies needed",
    )
    testing_notes: str | None = Field(
        default=None,
        description="Notes on how to test the implementation",
    )


class Plan(BaseModel):
    """Complete plan for all growth loops."""

    version: str = Field(default="1.0", description="Plan version")
    project_name: str = Field(description="Target project name")
    generated_at: datetime = Field(default_factory=datetime.now)
    manifest_summary: str = Field(description="Summary of the growth manifest")
    loop_plans: list[LoopPlan] = Field(
        default_factory=list,
        description="Plans for each growth loop",
    )
    shared_infrastructure: list[CodeChange] = Field(
        default_factory=list,
        description="Shared infrastructure changes needed",
    )
    implementation_order: list[str] = Field(
        default_factory=list,
        description="Recommended order of loop IDs to implement",
    )


class Planner:
    """
    Generates growth loop implementation plans.

    Supports intelligent loop selection based on objectives and quick heuristic-based planning.

    Example:
        planner = Planner()
        selected_loops = await planner.select_intelligent_loops(
            llm=llm,
            manifest_data=manifest_data,
            objectives_content=objectives_content,
        )
    """

    def generate_quick_plan(
        self,
        manifest: GrowthManifest,
        catalog: GrowthLoopCatalog | None = None,
    ) -> Plan:
        """
        Generate a quick plan without LLM (heuristic-based).

        Uses keyword matching to map loops to growth hubs
        and generates basic implementation suggestions.

        Args:
            manifest: The project's growth manifest
            catalog: Loop catalog (uses default if None)

        Returns:
            Basic plan
        """
        catalog = catalog or GrowthLoopCatalog()
        mapper = LoopMapper()

        # Use heuristic mapping
        mappings = mapper.map_from_hubs(
            growth_hubs=manifest.growth_hubs,
            loops=catalog.get_all(),
        )

        # Generate basic plans for applicable loops
        loop_plans = []
        for mapping in mappings:
            if mapping.is_applicable and mapping.injection_points:
                plan = self._generate_basic_plan(mapping)
                loop_plans.append(plan)

        # Sort by priority
        loop_plans.sort(key=lambda p: p.priority, reverse=True)

        return Plan(
            project_name=manifest.project_name,
            manifest_summary=manifest.description or f"Growth manifest for {manifest.project_name}",
            loop_plans=loop_plans,
            implementation_order=[p.loop_id for p in loop_plans],
        )

    async def select_loops(
        self,
        llm: LLMClient,
        manifest_data: dict[str, Any],
        objectives_content: str,
        catalog: GrowthLoopCatalog | None = None,
        daily_logs_summary: str | None = None,
        num_loops: int = 3,
    ) -> list[SelectedGrowthLoop]:
        """
        Select growth loops using LLM based on objectives and context.

        Selects loops incrementally, ensuring diversity and alignment
        with growth objectives.

        Args:
            llm: LLM client for generation
            manifest_data: Project manifest data (from growth-manifest.json)
            objectives_content: Content from growth-objectives.md
            catalog: Growth loop catalog (uses default if None)
            daily_logs_summary: Summary of daily logs (optional)
            num_loops: Number of loops to select (default: 3)

        Returns:
            List of selected growth loops with implementation details
        """
        catalog = catalog or GrowthLoopCatalog()
        csv_loops = self._catalog_to_csv_format(catalog)

        selected_loops: list[SelectedGrowthLoop] = []

        for iteration in range(1, num_loops + 1):
            logger.info(f"Selecting loop {iteration} of {num_loops}...")

            loop = await self._select_single_loop(
                llm=llm,
                manifest_data=manifest_data,
                objectives_content=objectives_content,
                daily_logs_summary=daily_logs_summary,
                csv_loops=csv_loops,
                previously_selected=selected_loops,
                iteration=iteration,
            )

            selected_loops.append(loop)
            logger.success(f"Selected: {loop.loop_name}")

        logger.success(f"Selected {len(selected_loops)} growth loops")
        return selected_loops

    def write_selected_loops_markdown(
        self,
        selected_loops: list[SelectedGrowthLoop],
        manifest_data: dict[str, Any],
        output_path: Path | str,
        has_daily_logs: bool = False,
    ) -> Path:
        """
        Write selected growth loops to markdown file.

        Args:
            selected_loops: List of selected loops
            manifest_data: Project manifest data
            output_path: Path to write the file
            has_daily_logs: Whether daily logs were used

        Returns:
            Path to the written file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate markdown content
        lines = [
            "# Growth Loops Implementation Plan",
            "",
            f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        ]

        if has_daily_logs:
            lines.append("*Based on: growth-manifest.json, growth-objectives.md, daily logs*")
        else:
            lines.append("*Based on: growth-manifest.json, growth-objectives.md*")

        lines.extend(["", "---", ""])

        # Add each loop
        for i, loop in enumerate(selected_loops, 1):
            lines.extend(
                [
                    f"## Loop {i}: {loop.loop_name}",
                    "",
                    f"**PLG Stage:** {loop.plg_stage}",
                    f"**Goal:** {loop.goal}",
                    "",
                ]
            )

            if loop.why_selected:
                lines.extend(
                    [
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

            if loop.action or loop.value:
                lines.append("### What It Does")
                if loop.action:
                    lines.append(f"**Action:** {loop.action}")
                if loop.value:
                    lines.append(f"**Value:** {loop.value}")
                lines.append("")

            if loop.implementation_steps:
                lines.extend(
                    [
                        "### Implementation Steps",
                    ]
                )
                for j, step in enumerate(loop.implementation_steps, 1):
                    lines.append(f"{j}. {step}")
                lines.append("")

            if loop.success_metrics:
                lines.extend(
                    [
                        "### Success Metrics",
                    ]
                )
                for j, metric in enumerate(loop.success_metrics, 1):
                    lines.append(f"- Metric {j}: {metric}")
                lines.append("")

            if loop.implementation:
                lines.extend(
                    [
                        "### Technical Details",
                        f"**Implementation Stack:** {loop.implementation}",
                        "",
                    ]
                )

            lines.extend(["---", ""])

        lines.append("*Growth loops selected by skene-growth using LLM analysis.*")

        # Write to file
        output_path.write_text("\n".join(lines))
        logger.info(f"Wrote growth loops plan to {output_path}")

        return output_path

    def _catalog_to_csv_format(self, catalog: GrowthLoopCatalog) -> list[dict[str, Any]]:
        """Convert catalog loops to CSV format for LLM prompts."""
        # Get CSV loops from catalog (already in the right format)
        csv_loops = catalog.get_csv_loops()

        # If we have CSV loops, use them directly
        if csv_loops:
            formatted = []
            for loop in csv_loops:
                formatted.append(
                    {
                        "Loop Name": loop.get("loop_name", ""),
                        "PLG Stage": loop.get("plg_stage", ""),
                        "Goal": loop.get("goal", ""),
                        "User Story": loop.get("user_story", ""),
                        "Trigger": loop.get("trigger", ""),
                        "Action": loop.get("action", ""),
                        "Value": loop.get("value", ""),
                        "Implementation": loop.get("implementation", ""),
                        "Action Summary": loop.get("action_summary", ""),
                        "Value Summary": loop.get("value_summary", ""),
                    }
                )
            return formatted

        # Fallback: convert GrowthLoop objects to CSV format
        formatted = []
        for loop in catalog.get_all():
            formatted.append(
                {
                    "Loop Name": loop.name,
                    "PLG Stage": loop.category,
                    "Goal": "",
                    "User Story": loop.description,
                    "Trigger": loop.trigger,
                    "Action": loop.action,
                    "Value": loop.reward,
                    "Implementation": ", ".join(loop.implementation_hints[:2]) if loop.implementation_hints else "",
                    "Action Summary": loop.action,
                    "Value Summary": loop.reward,
                }
            )
        return formatted

    async def _select_single_loop(
        self,
        llm: LLMClient,
        manifest_data: dict[str, Any],
        objectives_content: str,
        daily_logs_summary: str | None,
        csv_loops: list[dict[str, Any]],
        previously_selected: list[SelectedGrowthLoop],
        iteration: int,
    ) -> SelectedGrowthLoop:
        """Select a single growth loop using LLM."""
        prompt = self._build_selection_prompt(
            manifest_data=manifest_data,
            objectives_content=objectives_content,
            daily_logs_summary=daily_logs_summary,
            csv_loops=csv_loops,
            previously_selected=previously_selected,
            iteration=iteration,
        )

        response = await llm.generate_content(prompt)
        try:
            loop = self._parse_single_loop_response(response, csv_loops, previously_selected)
        except ValueError as e:
            # If loop not found, select next available loop
            logger.warning(f"Loop not found: {e}. Selecting next available loop...")
            loop = self._select_fallback_loop(csv_loops, previously_selected, iteration)

        return loop

    def _build_selection_prompt(
        self,
        manifest_data: dict[str, Any],
        objectives_content: str,
        daily_logs_summary: str | None,
        csv_loops: list[dict[str, Any]],
        previously_selected: list[SelectedGrowthLoop],
        iteration: int,
    ) -> str:
        """Build a prompt for selecting ONE growth loop."""
        # Format manifest summary
        manifest_summary = self._format_manifest_summary(manifest_data)

        # Format available loops
        loops_text = self._format_available_loops(csv_loops)

        # Format previously selected loops
        previously_selected_text = ""
        if previously_selected:
            previously_selected_text = "\n## Previously Selected Loops (DO NOT select these again)\n"
            for i, loop in enumerate(previously_selected, 1):
                previously_selected_text += f"\n### Loop {i}: {loop.loop_name}\n"
                previously_selected_text += f"- **PLG Stage:** {loop.plg_stage}\n"
                previously_selected_text += f"- **Goal:** {loop.goal}\n"
                previously_selected_text += f"- **Why Selected:** {loop.why_selected}\n"

        # Format daily logs section
        daily_logs_section = ""
        if daily_logs_summary:
            daily_logs_section = f"""
## Daily Logs Analysis (Performance Metrics)
{daily_logs_summary}

**IMPORTANT:** Use these metrics to identify weak areas. Prioritize loops that address underperforming metrics.
"""

        return f"""You are a Product-Led Growth (PLG) strategist. Your task is to select the SINGLE most impactful
growth loop for this project.

## Iteration {iteration} of 3
Select ONE growth loop that would have the highest impact given the current context.

## Project Manifest (Current State)
{manifest_summary}

## Current Growth Objectives
{objectives_content}
{daily_logs_section}
{previously_selected_text}

## Available Growth Loops ({len(csv_loops)} total)
Below are all available growth loops from the catalog. Select ONE that best addresses the project's needs:

{loops_text}

## Selection Criteria
1. **Do NOT select** any of the previously selected loops
2. **Ensure diversity**: Try to choose a loop from a different PLG stage than already selected
3. **Address weak areas**: If daily logs are provided, prioritize loops that address underperforming metrics
4. **Align with objectives**: The selected loop should support the current growth objectives
5. **Consider tech stack**: Choose loops compatible with the project's Implementation Stack

## Your Task
Select exactly ONE growth loop and provide:
1. The exact loop name (must match one from the list above)
2. Why this specific loop was selected for THIS project (be specific)
3. 3-5 implementation steps tailored to the codebase
4. 2-3 success metrics to track

**CRITICAL RULES:**
1. You MUST select a loop name that EXACTLY matches one from the "Available Growth Loops" list above
2. Copy the loop name character-for-character, including capitalization and spacing
3. Do NOT create new loop names or modify existing ones
4. Do NOT generalize (e.g., don't use "Referral Program" when the actual name is "Copy Link Interceptor")
5. When providing explanations, implementation steps, and success metrics, always refer to the loop by its exact name

Return ONLY a JSON object (not an array) in this format:
```json
{{
  "loop_name": "Exact Loop Name from CSV",
  "plg_stage": "PLG Stage",
  "goal": "Goal from CSV",
  "user_story": "User Story from CSV",
  "action": "Action from CSV",
  "value": "Value from CSV",
  "implementation": "Implementation from CSV",
  "why_selected": (
    "Detailed explanation of WHY this specific loop was chosen for THIS project. "
    "Reference the loop by name."
  ),
  "implementation_steps": [
    "Step 1: Specific action (reference loop name)",
    "Step 2: Specific action (reference loop name)",
    "Step 3: Specific action (reference loop name)"
  ],
  "success_metrics": [
    "Metric 1: How to measure (reference loop name)",
    "Metric 2: How to measure (reference loop name)"
  ]
}}
```"""

    def _format_manifest_summary(self, manifest_data: dict[str, Any]) -> str:
        """Format manifest data into a readable summary."""
        lines = []

        if "project_name" in manifest_data:
            lines.append(f"**Project:** {manifest_data['project_name']}")

        if "description" in manifest_data:
            lines.append(f"**Description:** {manifest_data['description']}")

        if "tech_stack" in manifest_data:
            tech = manifest_data["tech_stack"]
            lines.append("\n**Tech Stack:**")
            for key, value in tech.items():
                if value:
                    lines.append(f"- {key}: {value}")

        if "growth_hubs" in manifest_data and manifest_data["growth_hubs"]:
            lines.append(f"\n**Existing Growth Hubs:** {len(manifest_data['growth_hubs'])} detected")
            for hub in manifest_data["growth_hubs"][:3]:
                lines.append(f"- {hub.get('feature_name', 'Unknown')}")

        if "gtm_gaps" in manifest_data and manifest_data["gtm_gaps"]:
            lines.append(f"\n**GTM Gaps:** {len(manifest_data['gtm_gaps'])} identified")
            for gap in manifest_data["gtm_gaps"][:3]:
                lines.append(f"- {gap.get('feature_name', 'Unknown')} (priority: {gap.get('priority', 'N/A')})")

        return "\n".join(lines)

    def _format_available_loops(self, csv_loops: list[dict[str, Any]]) -> str:
        """Format CSV loops into a readable list."""
        lines = []
        for i, loop in enumerate(csv_loops, 1):
            lines.append(f"\n### {i}. {loop.get('Loop Name', 'Unknown')}")
            lines.append(f"- **PLG Stage:** {loop.get('PLG Stage', 'N/A')}")
            lines.append(f"- **Goal:** {loop.get('Goal', 'N/A')}")
            if loop.get("User Story"):
                lines.append(f"- **User Story:** {loop['User Story']}")
            if loop.get("Action"):
                lines.append(f"- **Action:** {loop['Action']}")
            if loop.get("Value"):
                lines.append(f"- **Value:** {loop['Value']}")
        return "\n".join(lines)

    def _parse_single_loop_response(
        self,
        response: str,
        csv_loops: list[dict[str, Any]],
        previously_selected: list[SelectedGrowthLoop],
    ) -> SelectedGrowthLoop:
        """Parse LLM response into a SelectedGrowthLoop."""
        # Extract JSON from response
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
        if not json_match:
            json_match = re.search(r"(\{.*\})", response, re.DOTALL)

        if not json_match:
            raise ValueError("Could not find JSON in LLM response")

        try:
            data = json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in LLM response: {e}")

        # Validate loop name exists in catalog
        loop_name = data.get("loop_name", "")
        matching_loop = next((loop for loop in csv_loops if loop.get("Loop Name") == loop_name), None)

        if not matching_loop:
            # Try fuzzy match
            loop_name_lower = loop_name.lower()
            matching_loop = next(
                (loop for loop in csv_loops if loop.get("Loop Name", "").lower() == loop_name_lower), None
            )

        if not matching_loop:
            raise ValueError(
                f"Selected loop '{loop_name}' not found in catalog. "
                f"Available loops: {[loop.get('Loop Name') for loop in csv_loops[:5]]}..."
            )

        return SelectedGrowthLoop(
            loop_name=matching_loop.get("Loop Name") or data.get("loop_name") or "",
            plg_stage=matching_loop.get("PLG Stage") or data.get("plg_stage") or "",
            goal=matching_loop.get("Goal") or data.get("goal") or "",
            user_story=matching_loop.get("User Story") or data.get("user_story") or "",
            action=matching_loop.get("Action") or data.get("action") or "",
            value=matching_loop.get("Value") or data.get("value") or "",
            implementation=matching_loop.get("Implementation") or data.get("implementation") or "",
            why_selected=data.get("why_selected")
            or f"Selected as fallback after '{loop_name}' was not found in catalog",
            implementation_steps=data.get("implementation_steps") or [],
            success_metrics=data.get("success_metrics") or [],
        )

    def _select_fallback_loop(
        self,
        csv_loops: list[dict[str, Any]],
        previously_selected: list[SelectedGrowthLoop],
        iteration: int,
    ) -> SelectedGrowthLoop:
        """
        Select the next available loop when requested loop is not found.

        Args:
            csv_loops: All available loops from CSV
            previously_selected: Loops already selected
            iteration: Current iteration number

        Returns:
            SelectedGrowthLoop from next available option
        """
        # Get names of previously selected loops
        selected_names = {loop.loop_name.lower() for loop in previously_selected}

        # Find next available loop that hasn't been selected
        for loop in csv_loops:
            loop_name = loop.get("Loop Name", "")
            if loop_name and loop_name.lower() not in selected_names:
                logger.info(f"Fallback: Selecting '{loop_name}' (iteration {iteration})")
                return SelectedGrowthLoop(
                    loop_name=loop_name,
                    plg_stage=loop.get("PLG Stage", ""),
                    goal=loop.get("Goal", ""),
                    user_story=loop.get("User Story", ""),
                    action=loop.get("Action", ""),
                    value=loop.get("Value", ""),
                    implementation=loop.get("Implementation", ""),
                    why_selected=(
                        f"Selected as fallback after requested loop was not found in catalog "
                        f"(iteration {iteration})"
                    ),
                    implementation_steps=[],
                    success_metrics=[],
                )

        # If all loops are selected (shouldn't happen), return the first one
        if csv_loops:
            first_loop = csv_loops[0]
            logger.warning("All loops already selected, returning first loop as fallback")
            return SelectedGrowthLoop(
                loop_name=first_loop.get("Loop Name", ""),
                plg_stage=first_loop.get("PLG Stage", ""),
                goal=first_loop.get("Goal", ""),
                user_story=first_loop.get("User Story", ""),
                action=first_loop.get("Action", ""),
                value=first_loop.get("Value", ""),
                implementation=first_loop.get("Implementation", ""),
                why_selected="Selected as fallback - all other loops were already selected",
                implementation_steps=[],
                success_metrics=[],
            )

        raise ValueError("No loops available in catalog")

    def _generate_basic_plan(self, mapping: LoopMapping) -> LoopPlan:
        """Generate basic plan without LLM."""
        code_changes = []

        for point in mapping.injection_points:
            for change_desc in point.changes_required:
                code_changes.append(
                    CodeChange(
                        file_path=point.file_path,
                        change_type="modify",
                        description=change_desc,
                    )
                )

        return LoopPlan(
            loop_id=mapping.loop_id,
            loop_name=mapping.loop_name,
            priority=mapping.priority,
            estimated_complexity="medium",
            code_changes=code_changes,
            testing_notes="Test the integration manually after implementation.",
        )
