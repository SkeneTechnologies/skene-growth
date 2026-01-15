"""
Injection plan generator.

Creates detailed implementation plans for injecting growth loops into a codebase.
"""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from skene_growth.codebase import CodebaseExplorer
from skene_growth.injector.loops import GrowthLoop, GrowthLoopCatalog
from skene_growth.injector.mapper import LoopMapper, LoopMapping
from skene_growth.llm import LLMClient
from skene_growth.manifest import GrowthManifest


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


class LoopInjectionPlan(BaseModel):
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


class InjectionPlan(BaseModel):
    """Complete injection plan for all growth loops."""

    version: str = Field(default="1.0", description="Plan version")
    project_name: str = Field(description="Target project name")
    generated_at: datetime = Field(default_factory=datetime.now)
    manifest_summary: str = Field(description="Summary of the growth manifest")
    loop_plans: list[LoopInjectionPlan] = Field(
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


class InjectionPlanner:
    """
    Generates detailed implementation plans for growth loop injection.

    Takes loop mappings and generates actionable code changes
    that can be implemented manually or via automation.

    Example:
        planner = InjectionPlanner()
        plan = await planner.generate_plan(
            manifest=manifest,
            mappings=mappings,
            llm=llm,
            codebase=codebase,
        )
        plan.save_json("./injection-plan.json")
    """

    # Prompt for generating detailed implementation plans
    PLANNING_PROMPT = """
You are a senior software engineer creating an implementation plan for adding growth features.

## Project Context
- **Project**: {project_name}
- **Tech Stack**: {tech_stack}
- **Description**: {description}

## Growth Loop to Implement: {loop_name}
- **Category**: {category}
- **Description**: {loop_description}
- **Trigger**: {trigger}
- **Action**: {action}
- **Reward**: {reward}

## Identified Injection Points
{injection_points}

## Task
Create a detailed implementation plan with:
1. Specific code changes (files to create/modify)
2. Code snippets where helpful
3. New dependencies needed
4. Implementation order (what depends on what)
5. Testing approach

Return JSON with:
- estimated_complexity: "low" | "medium" | "high"
- code_changes: array of {{file_path, change_type, description, code_snippet, dependencies}}
- new_dependencies: array of package names
- testing_notes: string with testing guidance
"""

    INFRASTRUCTURE_PROMPT = """
Analyze these growth loop implementation plans and identify shared infrastructure.

## Plans
{plans_summary}

## Tech Stack
{tech_stack}

What shared infrastructure changes are needed across multiple loops?
Examples: shared hooks, utility functions, database tables, API endpoints.

Return JSON with:
- shared_changes: array of {{file_path, change_type, description, code_snippet}}
- implementation_order: recommended order of loop IDs based on dependencies
"""

    async def generate_plan(
        self,
        manifest: GrowthManifest,
        mappings: list[LoopMapping],
        llm: LLMClient,
        codebase: CodebaseExplorer,
    ) -> InjectionPlan:
        """
        Generate a complete injection plan.

        Args:
            manifest: The project's growth manifest
            mappings: Loop mappings from LoopMapper
            llm: LLM client for analysis
            codebase: Access to the codebase

        Returns:
            Complete injection plan
        """
        # Filter to applicable mappings with injection points
        applicable = [m for m in mappings if m.is_applicable and m.injection_points]

        # Generate plan for each loop
        loop_plans = []
        for mapping in applicable:
            plan = await self._generate_loop_plan(
                mapping=mapping,
                manifest=manifest,
                llm=llm,
            )
            loop_plans.append(plan)

        # Identify shared infrastructure
        shared_infra, impl_order = await self._identify_shared_infrastructure(
            loop_plans=loop_plans,
            manifest=manifest,
            llm=llm,
        )

        return InjectionPlan(
            project_name=manifest.project_name,
            manifest_summary=manifest.description or f"Growth manifest for {manifest.project_name}",
            loop_plans=loop_plans,
            shared_infrastructure=shared_infra,
            implementation_order=impl_order,
        )

    async def generate_plan_from_catalog(
        self,
        manifest: GrowthManifest,
        codebase: CodebaseExplorer,
        llm: LLMClient,
        catalog: GrowthLoopCatalog | None = None,
        categories: list[str] | None = None,
    ) -> InjectionPlan:
        """
        Generate injection plan using the loop catalog.

        Convenience method that handles mapping and planning in one call.

        Args:
            manifest: The project's growth manifest
            codebase: Access to the codebase
            llm: LLM client for analysis
            catalog: Loop catalog (uses default if None)
            categories: Filter to specific categories

        Returns:
            Complete injection plan
        """
        catalog = catalog or GrowthLoopCatalog()
        mapper = LoopMapper()

        # Get loops
        if categories:
            loops = []
            for cat in categories:
                loops.extend(catalog.get_by_category(cat))
        else:
            loops = catalog.get_all()

        # Map loops to codebase
        mappings = await mapper.map_loops(
            loops=loops,
            manifest=manifest,
            codebase=codebase,
            llm=llm,
        )

        # Generate plan
        return await self.generate_plan(
            manifest=manifest,
            mappings=mappings,
            llm=llm,
            codebase=codebase,
        )

    def generate_quick_plan(
        self,
        manifest: GrowthManifest,
        catalog: GrowthLoopCatalog | None = None,
    ) -> InjectionPlan:
        """
        Generate a quick plan without LLM (heuristic-based).

        Uses keyword matching to map loops to growth hubs
        and generates basic implementation suggestions.

        Args:
            manifest: The project's growth manifest
            catalog: Loop catalog (uses default if None)

        Returns:
            Basic injection plan
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

        return InjectionPlan(
            project_name=manifest.project_name,
            manifest_summary=manifest.description or f"Growth manifest for {manifest.project_name}",
            loop_plans=loop_plans,
            implementation_order=[p.loop_id for p in loop_plans],
        )

    def save_plan(self, plan: InjectionPlan, output_path: Path | str) -> Path:
        """
        Save injection plan to JSON file.

        Args:
            plan: The injection plan
            output_path: Path to save to

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(plan.model_dump_json(indent=2))
        return output_path

    async def _generate_loop_plan(
        self,
        mapping: LoopMapping,
        manifest: GrowthManifest,
        llm: LLMClient,
    ) -> LoopInjectionPlan:
        """Generate detailed plan for a single loop."""
        # Get loop details from catalog
        catalog = GrowthLoopCatalog()
        loop = catalog.get_by_id(mapping.loop_id)

        if not loop:
            # Create basic plan without loop details
            return self._generate_basic_plan(mapping)

        # Format injection points
        injection_points_text = "\n".join(
            [
                f"- {p.file_path}: {p.location} (confidence: {p.confidence:.0%})\n  {p.rationale}"
                for p in mapping.injection_points
            ]
        )

        # Format tech stack
        tech_stack_text = ", ".join([f"{k}: {v}" for k, v in manifest.tech_stack.model_dump().items() if v])

        # Build prompt
        prompt = self.PLANNING_PROMPT.format(
            project_name=manifest.project_name,
            tech_stack=tech_stack_text,
            description=manifest.description or "No description",
            loop_name=loop.name,
            category=loop.category,
            loop_description=loop.description,
            trigger=loop.trigger,
            action=loop.action,
            reward=loop.reward,
            injection_points=injection_points_text,
        )

        # Get LLM response
        response = await llm.generate_content(prompt)

        # Parse response
        return self._parse_loop_plan(response, mapping, loop)

    async def _identify_shared_infrastructure(
        self,
        loop_plans: list[LoopInjectionPlan],
        manifest: GrowthManifest,
        llm: LLMClient,
    ) -> tuple[list[CodeChange], list[str]]:
        """Identify shared infrastructure needs across plans."""
        if not loop_plans:
            return [], []

        # Summarize plans
        plans_summary = "\n\n".join(
            [
                f"## {plan.loop_name}\n" + "\n".join([f"- {c.description}" for c in plan.code_changes[:5]])
                for plan in loop_plans
            ]
        )

        tech_stack_text = ", ".join([f"{k}: {v}" for k, v in manifest.tech_stack.model_dump().items() if v])

        prompt = self.INFRASTRUCTURE_PROMPT.format(
            plans_summary=plans_summary,
            tech_stack=tech_stack_text,
        )

        response = await llm.generate_content(prompt)

        return self._parse_infrastructure_response(response, loop_plans)

    def _generate_basic_plan(self, mapping: LoopMapping) -> LoopInjectionPlan:
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

        return LoopInjectionPlan(
            loop_id=mapping.loop_id,
            loop_name=mapping.loop_name,
            priority=mapping.priority,
            estimated_complexity="medium",
            code_changes=code_changes,
            testing_notes="Test the integration manually after implementation.",
        )

    def _parse_loop_plan(
        self,
        response: str,
        mapping: LoopMapping,
        loop: GrowthLoop,
    ) -> LoopInjectionPlan:
        """Parse LLM response into LoopInjectionPlan."""
        import json
        import re

        # Try to extract JSON
        try:
            data = json.loads(response.strip())
        except json.JSONDecodeError:
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    data = {}
            else:
                data = {}

        # Parse code changes
        code_changes = []
        for change in data.get("code_changes", []):
            try:
                code_changes.append(
                    CodeChange(
                        file_path=change.get("file_path", "unknown"),
                        change_type=change.get("change_type", "modify"),
                        description=change.get("description", ""),
                        code_snippet=change.get("code_snippet"),
                        dependencies=change.get("dependencies", []),
                    )
                )
            except Exception:
                continue

        return LoopInjectionPlan(
            loop_id=loop.id,
            loop_name=loop.name,
            priority=mapping.priority,
            estimated_complexity=data.get("estimated_complexity", "medium"),
            code_changes=code_changes,
            new_dependencies=data.get("new_dependencies", []),
            testing_notes=data.get("testing_notes"),
        )

    def _parse_infrastructure_response(
        self,
        response: str,
        loop_plans: list[LoopInjectionPlan],
    ) -> tuple[list[CodeChange], list[str]]:
        """Parse infrastructure analysis response."""
        import json
        import re

        try:
            data = json.loads(response.strip())
        except json.JSONDecodeError:
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    data = {}
            else:
                data = {}

        # Parse shared changes
        shared_changes = []
        for change in data.get("shared_changes", []):
            try:
                shared_changes.append(
                    CodeChange(
                        file_path=change.get("file_path", "unknown"),
                        change_type=change.get("change_type", "create"),
                        description=change.get("description", ""),
                        code_snippet=change.get("code_snippet"),
                    )
                )
            except Exception:
                continue

        # Get implementation order, default to priority order
        impl_order = data.get("implementation_order", [])
        if not impl_order:
            sorted_plans = sorted(loop_plans, key=lambda p: p.priority, reverse=True)
            impl_order = [p.loop_id for p in sorted_plans]

        return shared_changes, impl_order
