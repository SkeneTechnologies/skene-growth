"""
Growth loop to codebase mapper.

Maps growth loops to potential injection points in a codebase.
"""

from pydantic import BaseModel, Field

from skene_growth.codebase import CodebaseExplorer
from skene_growth.injector.loops import GrowthLoop
from skene_growth.llm import LLMClient
from skene_growth.manifest import GrowthFeature, GrowthManifest


class InjectionPoint(BaseModel):
    """A potential location to inject a growth loop."""

    file_path: str = Field(description="Path to the file")
    location: str = Field(description="Function/component/line description")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    rationale: str = Field(description="Why this is a good injection point")
    changes_required: list[str] = Field(
        default_factory=list,
        description="List of changes needed",
    )


class LoopMapping(BaseModel):
    """Mapping of a growth loop to codebase locations."""

    loop_id: str = Field(description="The growth loop ID")
    loop_name: str = Field(description="The growth loop name")
    is_applicable: bool = Field(description="Whether this loop applies to the codebase")
    injection_points: list[InjectionPoint] = Field(
        default_factory=list,
        description="Potential injection points",
    )
    existing_implementation: str | None = Field(
        default=None,
        description="Description of existing implementation if found",
    )
    priority: int = Field(
        default=0,
        ge=0,
        le=10,
        description="Priority score (0-10)",
    )


class LoopMapper:
    """
    Maps growth loops to potential injection points in a codebase.

    Uses the growth manifest and codebase explorer to identify
    where growth loops could be implemented.

    Example:
        mapper = LoopMapper()
        mappings = await mapper.map_loops(
            manifest=manifest,
            loops=[invite_loop, share_loop],
            codebase=codebase,
            llm=llm,
        )
    """

    # Prompt for mapping loops to code
    MAPPING_PROMPT = """
Analyze this codebase and identify where the following growth loop could be implemented.

## Growth Loop: {loop_name}
- **Category**: {category}
- **Description**: {description}
- **Trigger**: {trigger}
- **Action**: {action}
- **Reward**: {reward}

## Required Components
{required_components}

## Implementation Hints
{implementation_hints}

## Codebase Context
{codebase_context}

## Current Growth Features Already Identified
{current_growth_features}

## Task
1. Determine if this growth loop is applicable to this codebase
2. If applicable, identify specific files/locations where it could be implemented
3. For each location, explain what changes would be needed
4. Assess priority based on potential impact and implementation effort

Return your analysis as JSON with:
- is_applicable: boolean
- existing_implementation: string or null (if already implemented)
- injection_points: array of {{file_path, location, confidence, rationale, changes_required}}
- priority: number 0-10
"""

    async def map_loop(
        self,
        loop: GrowthLoop,
        manifest: GrowthManifest,
        codebase: CodebaseExplorer,
        llm: LLMClient,
    ) -> LoopMapping:
        """
        Map a single growth loop to the codebase.

        Args:
            loop: The growth loop to map
            manifest: The project's growth manifest
            codebase: Access to the codebase
            llm: LLM client for analysis

        Returns:
            Mapping with injection points
        """
        # Get codebase context
        tree_result = await codebase.get_directory_tree(".", max_depth=3)
        codebase_context = tree_result.get("tree", "")

        # Format current growth features
        features_text = "\n".join(
            [
                f"- {feature.feature_name}: {feature.detected_intent} ({feature.file_path})"
                for feature in manifest.current_growth_features
            ]
        )

        # Build prompt
        prompt = self.MAPPING_PROMPT.format(
            loop_name=loop.name,
            category=loop.category,
            description=loop.description,
            trigger=loop.trigger,
            action=loop.action,
            reward=loop.reward,
            required_components="\n".join(f"- {c}" for c in loop.required_components),
            implementation_hints="\n".join(f"- {h}" for h in loop.implementation_hints),
            codebase_context=codebase_context,
            current_growth_features=features_text or "None identified",
        )

        # Get LLM analysis
        response = await llm.generate_content(prompt)

        # Parse response
        mapping = self._parse_mapping_response(response, loop)
        return mapping

    async def map_loops(
        self,
        loops: list[GrowthLoop],
        manifest: GrowthManifest,
        codebase: CodebaseExplorer,
        llm: LLMClient,
    ) -> list[LoopMapping]:
        """
        Map multiple growth loops to the codebase.

        Args:
            loops: List of growth loops to map
            manifest: The project's growth manifest
            codebase: Access to the codebase
            llm: LLM client for analysis

        Returns:
            List of mappings
        """
        mappings = []
        for loop in loops:
            mapping = await self.map_loop(loop, manifest, codebase, llm)
            mappings.append(mapping)
        return mappings

    def map_from_features(
        self,
        growth_features: list[GrowthFeature],
        loops: list[GrowthLoop],
    ) -> list[LoopMapping]:
        """
        Create basic mappings from existing growth features.

        This is a simpler, non-LLM approach that matches loops
        to features based on keywords and intents.

        Args:
            growth_features: Identified current growth features
            loops: Available growth loops

        Returns:
            Basic mappings based on keyword matching
        """
        mappings = []

        for loop in loops:
            matching_features = self._find_matching_features(loop, growth_features)

            if matching_features:
                injection_points = [
                    InjectionPoint(
                        file_path=feature.file_path,
                        location=feature.entry_point or feature.feature_name,
                        confidence=feature.confidence_score * 0.8,  # Reduce for heuristic
                        rationale=f"Existing {feature.detected_intent} feature for {loop.name}",
                        changes_required=[f"Integrate {loop.name} into {feature.feature_name}"],
                    )
                    for feature in matching_features
                ]

                mappings.append(
                    LoopMapping(
                        loop_id=loop.id,
                        loop_name=loop.name,
                        is_applicable=True,
                        injection_points=injection_points,
                        priority=min(len(matching_features) * 2, 10),
                    )
                )
            else:
                mappings.append(
                    LoopMapping(
                        loop_id=loop.id,
                        loop_name=loop.name,
                        is_applicable=False,
                        priority=0,
                    )
                )

        return mappings

    # Backwards compatibility alias
    map_from_hubs = map_from_features

    def _find_matching_features(
        self,
        loop: GrowthLoop,
        growth_features: list[GrowthFeature],
    ) -> list[GrowthFeature]:
        """Find growth features that match a loop's requirements."""
        # Keywords to match for each category
        category_keywords = {
            "referral": ["invite", "share", "refer", "team", "collaboration"],
            "acquisition": ["share", "social", "content", "seo", "marketing"],
            "activation": ["onboard", "setup", "welcome", "tutorial", "getting started"],
            "retention": ["notification", "email", "remind", "streak", "engagement"],
            "revenue": ["upgrade", "billing", "payment", "premium", "subscription", "pricing"],
        }

        keywords = category_keywords.get(loop.category, [])
        matching = []

        for feature in growth_features:
            potential = " ".join(feature.growth_potential)
            feature_text = f"{feature.feature_name} {feature.detected_intent} {potential}".lower()
            if any(keyword in feature_text for keyword in keywords):
                matching.append(feature)

        return matching

    # Backwards compatibility alias
    _find_matching_hubs = _find_matching_features

    def _parse_mapping_response(self, response: str, loop: GrowthLoop) -> LoopMapping:
        """Parse LLM response into LoopMapping."""
        import json
        import re

        # Try to extract JSON from response
        try:
            # Try direct parse
            data = json.loads(response.strip())
        except json.JSONDecodeError:
            # Try to find JSON in response
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    data = {}
            else:
                data = {}

        # Build mapping from parsed data
        injection_points = []
        for point in data.get("injection_points", []):
            try:
                injection_points.append(
                    InjectionPoint(
                        file_path=point.get("file_path", "unknown"),
                        location=point.get("location", "unknown"),
                        confidence=float(point.get("confidence", 0.5)),
                        rationale=point.get("rationale", ""),
                        changes_required=point.get("changes_required", []),
                    )
                )
            except Exception:
                continue

        return LoopMapping(
            loop_id=loop.id,
            loop_name=loop.name,
            is_applicable=data.get("is_applicable", False),
            injection_points=injection_points,
            existing_implementation=data.get("existing_implementation"),
            priority=data.get("priority", 0),
        )
