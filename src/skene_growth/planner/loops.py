"""
Growth loop catalog and definitions.

Defines common growth loops that can be injected into codebases.
"""

import csv
from pathlib import Path
from typing import Any, Literal

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


class CSVGrowthLoop(BaseModel):
    """
    A growth loop loaded from CSV with full schema.

    This model matches the actual growth_loops.csv schema.
    """

    loop_name: str = Field(description="Loop Name from CSV")
    plg_stage: str = Field(description="PLG Stage (Acquisition, Activation, etc.)")
    goal: str = Field(description="Goal (Sell)")
    user_story: str = Field(description="User Story (The Narrative)")
    ui_ux_delivery: str = Field(default="", description="UI/UX Delivery")
    trigger: str = Field(description="Trigger (Detection)")
    action: str = Field(description="Action (What Skene Does)")
    value: str = Field(description="Value (ROI)")
    proof_metric: str = Field(default="", description="Proof Metric & Analytics")
    action_summary: str = Field(default="", description="Action (Summary)")
    value_summary: str = Field(default="", description="Value (Summary)")
    industry_benchmark: str = Field(default="", description="Industry Average ROI (Benchmark)")
    system_pattern: str = Field(default="", description="System Pattern")
    implementation: str = Field(default="", description="Implementation (Stack)")


class SelectedGrowthLoop(BaseModel):
    """
    A growth loop selected by the LLM with implementation details.
    """

    loop_name: str = Field(description="Loop Name from CSV")
    plg_stage: str = Field(description="PLG Stage")
    goal: str = Field(description="Goal from CSV")
    user_story: str = Field(default="", description="User Story from CSV")
    action: str = Field(default="", description="Action from CSV")
    value: str = Field(default="", description="Value/ROI from CSV")
    implementation: str = Field(default="", description="Implementation Stack from CSV")
    why_selected: str = Field(description="LLM explanation of why this loop was selected")
    implementation_steps: list[str] = Field(default_factory=list, description="Actionable implementation steps")
    success_metrics: list[str] = Field(default_factory=list, description="How to measure success")
    technical_example: str = Field(
        default="", description="Technical implementation example using the project's tech stack"
    )


class GrowthLoopCatalog:
    """
    Catalog of common growth loops.

    Provides a library of growth loop templates that can be
    mapped to codebases and implemented.

    Automatically loads growth loops from the built-in CSV file if available.

    Example:
        catalog = GrowthLoopCatalog()
        referral_loops = catalog.get_by_category("referral")
        invite_loop = catalog.get_by_id("user-invites")
    """

    def __init__(self):
        """Initialize the catalog with built-in loops and load CSV if available."""
        self._loops: dict[str, GrowthLoop] = self._build_default_catalog()
        self._csv_loops: list[dict[str, Any]] = []
        self._load_builtin_csv()

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

    def get_csv_loops(self) -> list[dict[str, Any]]:
        """Get all loops loaded from CSV with full data."""
        return self._csv_loops

    def _load_builtin_csv(self) -> None:
        """
        Load the built-in CSV file if it exists.

        Tries multiple methods to locate the CSV file since assets/ is outside
        the package directory. Silently fails if CSV cannot be found, as default
        loops are still available.
        """
        csv_path = self._find_builtin_csv_path()

        if csv_path and csv_path.exists():
            try:
                self.load_from_csv(str(csv_path))
            except Exception:
                # Silently fail - default loops are still available
                pass

    def _find_builtin_csv_path(self) -> Path | None:
        """
        Find the built-in CSV file path using multiple fallback methods.

        Returns:
            Path to CSV file if found, None otherwise
        """
        # Method 1: Via package directory (works for installed packages)
        # This assumes assets/ is at the same level as skene_growth/ in src/
        try:
            import skene_growth

            package_dir = Path(skene_growth.__file__).parent.parent
            csv_path = package_dir / "assets" / "growth_loops.csv"
            if csv_path.exists():
                return csv_path
        except Exception:
            pass

        # Method 2: Via relative path from this file (works in development)
        try:
            csv_path = Path(__file__).parent.parent.parent / "assets" / "growth_loops.csv"
            if csv_path.exists():
                return csv_path
        except Exception:
            pass

        return None

    def load_from_csv(self, csv_path: str) -> list[dict[str, Any]]:
        """
        Load growth loops from a CSV file.

        Handles two CSV schemas:
        1. Simple format:
            id,name,category,description,trigger,action,reward,implementation_hints,required_components,metrics
        2. Detailed format:
            Loop Name, PLG Stage, Goal (Sell), User Story, UI/UX Delivery, etc.

        Args:
            csv_path: Path to the CSV file

        Returns:
            List of loop dictionaries with all CSV data
        """
        loaded = []

        with Path(csv_path).open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Check which format we have
                if "Loop Name" in row or "PLG Stage" in row:
                    # Detailed format
                    loop_data = {
                        "loop_name": row.get("Loop Name", "").strip(),
                        "plg_stage": row.get("PLG Stage", "").strip(),
                        "goal": row.get("Goal (Sell)", "").strip(),
                        "user_story": row.get("User Story (The Narrative)", "").strip(),
                        "ui_ux_delivery": row.get("UI/UX Delivery", "").strip(),
                        "trigger": row.get("Trigger (Detection)", "").strip(),
                        "action": row.get("Action (What Skene Does)", "").strip(),
                        "value": row.get("Value (ROI)", "").strip(),
                        "proof_metric": row.get("Proof Metric & Analytics", "").strip(),
                        "action_summary": row.get("Action (Summary)", "").strip(),
                        "value_summary": row.get("Value (Summary)", "").strip(),
                        "industry_benchmark": row.get("Industry Average ROI (Benchmark)", "").strip(),
                        "system_pattern": row.get("System Pattern", "").strip(),
                        "implementation": row.get("Implementation (Stack)", "").strip(),
                    }
                    # Skip empty rows
                    if not loop_data["loop_name"]:
                        continue
                else:
                    # Simple format: id,name,category,description,trigger,action,reward,...
                    loop_name = row.get("name", "").strip()
                    if not loop_name:
                        continue

                    # Map simple format to detailed format structure
                    loop_data = {
                        "loop_name": loop_name,
                        "plg_stage": row.get("category", "").strip(),
                        "goal": "",
                        "user_story": row.get("description", "").strip(),
                        "ui_ux_delivery": "",
                        "trigger": row.get("trigger", "").strip(),
                        "action": row.get("action", "").strip(),
                        "value": row.get("reward", "").strip(),
                        "proof_metric": row.get("metrics", "").strip(),
                        "action_summary": row.get("action", "").strip(),
                        "value_summary": row.get("reward", "").strip(),
                        "industry_benchmark": "",
                        "system_pattern": row.get("required_components", "").strip(),
                        "implementation": row.get("implementation_hints", "").strip(),
                        # Also include original fields for compatibility
                        "id": row.get("id", "").strip(),
                        "category": row.get("category", "").strip(),
                        "description": row.get("description", "").strip(),
                    }

                loaded.append(loop_data)

                # Also create a GrowthLoop for backward compatibility
                # Map PLG Stage to category
                stage_to_category = {
                    "acquisition": "acquisition",
                    "activation": "activation",
                    "retention": "retention",
                    "referral": "referral",
                    "revenue": "revenue",
                    "monetization": "revenue",
                    "expansion": "revenue",
                }
                category = stage_to_category.get(loop_data["plg_stage"].lower(), "activation")

                # Create simplified GrowthLoop
                loop_id = loop_data["loop_name"].lower().replace(" ", "-").replace('"', "").replace("'", "")
                growth_loop = GrowthLoop(
                    id=loop_id,
                    name=loop_data["loop_name"],
                    category=category,
                    description=loop_data["user_story"],
                    trigger=loop_data["trigger"],
                    action=loop_data["action"],
                    reward=loop_data["value"],
                )
                self._loops[loop_id] = growth_loop

        self._csv_loops = loaded
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
