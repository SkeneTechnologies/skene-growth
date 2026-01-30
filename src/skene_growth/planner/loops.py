"""
Growth loop definitions.

Defines growth loop models for LLM-based selection and planning.
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


