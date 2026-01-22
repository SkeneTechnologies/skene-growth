"""
Growth loop to codebase mapper.

Maps growth loops to potential injection points in a codebase using heuristic keyword matching.
"""

from pydantic import BaseModel, Field

from skene_growth.manifest import GrowthHub
from skene_growth.planner.loops import GrowthLoop


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
    Maps growth loops to potential injection points using heuristic keyword matching.

    Example:
        mapper = LoopMapper()
        mappings = mapper.map_from_hubs(
            growth_hubs=manifest.growth_hubs,
            loops=catalog.get_all(),
        )
    """

    def map_from_hubs(
        self,
        growth_hubs: list[GrowthHub],
        loops: list[GrowthLoop],
    ) -> list[LoopMapping]:
        """
        Create basic mappings from existing growth hubs.

        This is a simpler, non-LLM approach that matches loops
        to hubs based on keywords and intents.

        Args:
            growth_hubs: Identified growth hubs
            loops: Available growth loops

        Returns:
            Basic mappings based on keyword matching
        """
        mappings = []

        for loop in loops:
            matching_hubs = self._find_matching_hubs(loop, growth_hubs)

            if matching_hubs:
                injection_points = [
                    InjectionPoint(
                        file_path=hub.file_path,
                        location=hub.entry_point or hub.feature_name,
                        confidence=hub.confidence_score * 0.8,  # Reduce for heuristic
                        rationale=f"Existing {hub.detected_intent} feature for {loop.name}",
                        changes_required=[f"Integrate {loop.name} into {hub.feature_name}"],
                    )
                    for hub in matching_hubs
                ]

                mappings.append(
                    LoopMapping(
                        loop_id=loop.id,
                        loop_name=loop.name,
                        is_applicable=True,
                        injection_points=injection_points,
                        priority=min(len(matching_hubs) * 2, 10),
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

    def _find_matching_hubs(
        self,
        loop: GrowthLoop,
        growth_hubs: list[GrowthHub],
    ) -> list[GrowthHub]:
        """Find growth hubs that match a loop's requirements."""
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

        for hub in growth_hubs:
            potential = " ".join(hub.growth_potential)
            hub_text = f"{hub.feature_name} {hub.detected_intent} {potential}".lower()
            if any(keyword in hub_text for keyword in keywords):
                matching.append(hub)

        return matching
