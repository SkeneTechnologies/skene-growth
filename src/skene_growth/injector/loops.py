"""
Growth loop catalog and definitions.

Defines common growth loops that can be injected into codebases.
"""

from typing import Literal

from pydantic import BaseModel, Field


class GrowthLoop(BaseModel):
    """
    A growth loop definition.

    Growth loops are self-reinforcing cycles that drive user acquisition,
    activation, retention, or referral.
    """

    id: str = Field(description="Unique identifier for the loop")
    name: str = Field(description="Human-readable name")
    category: Literal["acquisition", "activation", "retention", "referral", "revenue"] = Field(
        description="Which stage of the funnel this loop targets"
    )
    description: str = Field(description="What this loop does")
    trigger: str = Field(description="What triggers this loop")
    action: str = Field(description="What action the user takes")
    reward: str = Field(description="What reward the user receives")
    implementation_hints: list[str] = Field(
        default_factory=list,
        description="Hints for implementing this loop",
    )
    required_components: list[str] = Field(
        default_factory=list,
        description="Components needed to implement this loop",
    )
    metrics: list[str] = Field(
        default_factory=list,
        description="Metrics to track for this loop",
    )


class GrowthLoopCatalog:
    """
    Catalog of common growth loops.

    Provides a library of growth loop templates that can be
    mapped to codebases and implemented.

    Example:
        catalog = GrowthLoopCatalog()
        referral_loops = catalog.get_by_category("referral")
        invite_loop = catalog.get_by_id("user-invites")
    """

    def __init__(self):
        """Initialize the catalog with built-in loops."""
        self._loops = self._build_default_catalog()

    def get_all(self) -> list[GrowthLoop]:
        """Get all growth loops in the catalog."""
        return list(self._loops.values())

    def get_by_id(self, loop_id: str) -> GrowthLoop | None:
        """Get a specific loop by ID."""
        return self._loops.get(loop_id)

    def get_by_category(
        self, category: Literal["acquisition", "activation", "retention", "referral", "revenue"]
    ) -> list[GrowthLoop]:
        """Get all loops in a category."""
        return [loop for loop in self._loops.values() if loop.category == category]

    def add_loop(self, loop: GrowthLoop) -> None:
        """Add a custom loop to the catalog."""
        self._loops[loop.id] = loop

    def load_from_csv(self, csv_path: str) -> list[GrowthLoop]:
        """
        Load growth loops from a CSV file.

        Expected columns: id, name, category, description, trigger, action, reward

        Args:
            csv_path: Path to the CSV file

        Returns:
            List of loaded loops
        """
        import csv
        from pathlib import Path

        loaded = []
        with Path(csv_path).open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                loop = GrowthLoop(
                    id=row.get("id", ""),
                    name=row.get("name", ""),
                    category=row.get("category", "activation"),
                    description=row.get("description", ""),
                    trigger=row.get("trigger", ""),
                    action=row.get("action", ""),
                    reward=row.get("reward", ""),
                )
                self._loops[loop.id] = loop
                loaded.append(loop)

        return loaded

    def _build_default_catalog(self) -> dict[str, GrowthLoop]:
        """Build the default catalog of growth loops."""
        loops = [
            GrowthLoop(
                id="user-invites",
                name="User Invites",
                category="referral",
                description="Users invite others to join, expanding the user base",
                trigger="User wants to collaborate or share",
                action="User sends invite to contacts",
                reward="New user joins, inviter gets credit/bonus",
                implementation_hints=[
                    "Add invite button to dashboard/settings",
                    "Create invite link generation endpoint",
                    "Track invite source for attribution",
                    "Send email notifications for invites",
                ],
                required_components=["email_service", "invite_tracking", "user_dashboard"],
                metrics=["invites_sent", "invite_conversion_rate", "viral_coefficient"],
            ),
            GrowthLoop(
                id="social-sharing",
                name="Social Sharing",
                category="acquisition",
                description="Users share content/achievements on social media",
                trigger="User creates content or achieves milestone",
                action="User shares to social networks",
                reward="Social validation, new users discover product",
                implementation_hints=[
                    "Add share buttons for key content",
                    "Create shareable cards/previews",
                    "Implement Open Graph meta tags",
                    "Track share events and conversions",
                ],
                required_components=["share_buttons", "og_meta", "analytics"],
                metrics=["shares", "click_through_rate", "social_signups"],
            ),
            GrowthLoop(
                id="onboarding-completion",
                name="Onboarding Completion",
                category="activation",
                description="Guide users to complete key actions that drive retention",
                trigger="User signs up",
                action="User completes onboarding steps",
                reward="User reaches 'aha moment', sees value",
                implementation_hints=[
                    "Define key activation metrics",
                    "Create step-by-step onboarding flow",
                    "Add progress indicators",
                    "Send reminder emails for incomplete onboarding",
                ],
                required_components=["onboarding_flow", "progress_tracking", "email_drips"],
                metrics=["onboarding_completion_rate", "time_to_activation", "day_1_retention"],
            ),
            GrowthLoop(
                id="usage-streaks",
                name="Usage Streaks",
                category="retention",
                description="Encourage daily/regular usage through streak mechanics",
                trigger="User uses product regularly",
                action="User maintains usage streak",
                reward="Streak badges, bonuses, status",
                implementation_hints=[
                    "Track daily active usage",
                    "Display streak counter prominently",
                    "Send streak reminder notifications",
                    "Offer streak recovery options",
                ],
                required_components=["usage_tracking", "notifications", "gamification_ui"],
                metrics=["streak_length", "streak_retention", "daily_active_users"],
            ),
            GrowthLoop(
                id="upgrade-prompts",
                name="Upgrade Prompts",
                category="revenue",
                description="Prompt users to upgrade when they hit limits",
                trigger="User hits usage limit or needs premium feature",
                action="User upgrades to paid plan",
                reward="User gets more value, company gets revenue",
                implementation_hints=[
                    "Define clear usage limits",
                    "Show contextual upgrade prompts",
                    "Highlight value of premium features",
                    "Offer trial periods for premium",
                ],
                required_components=["billing_system", "usage_limits", "upgrade_ui"],
                metrics=["upgrade_conversion", "revenue_per_user", "feature_adoption"],
            ),
            GrowthLoop(
                id="content-ugc",
                name="User-Generated Content",
                category="acquisition",
                description="Users create content that attracts new users",
                trigger="User creates valuable content",
                action="Content is shared/discovered",
                reward="Creator gets visibility, new users join",
                implementation_hints=[
                    "Enable content creation features",
                    "Make content publicly discoverable",
                    "Add SEO for user content",
                    "Feature top creators",
                ],
                required_components=["content_editor", "public_profiles", "seo"],
                metrics=["content_created", "organic_traffic", "creator_retention"],
            ),
            GrowthLoop(
                id="notification-reengagement",
                name="Re-engagement Notifications",
                category="retention",
                description="Bring back inactive users through timely notifications",
                trigger="User becomes inactive",
                action="User receives relevant notification",
                reward="User re-engages with new/updated content",
                implementation_hints=[
                    "Define inactivity thresholds",
                    "Personalize notification content",
                    "A/B test notification timing",
                    "Respect notification preferences",
                ],
                required_components=["push_notifications", "email", "user_segmentation"],
                metrics=["reactivation_rate", "notification_ctr", "churn_reduction"],
            ),
        ]

        return {loop.id: loop for loop in loops}
