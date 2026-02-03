"""
Plan generator.

Creates detailed implementation plans for growth strategies.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from skene_growth.llm import LLMClient


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
    Generates growth implementation plans.

    Example:
        planner = Planner()
        memo = await planner.generate_council_memo(
            llm=llm,
            manifest_data=manifest_data,
            template_data=template_data,
        )
    """

    async def generate_council_memo(
        self,
        llm: LLMClient,
        manifest_data: dict[str, Any],
        template_data: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a Council of Growth Engineers memo.

        Generates a comprehensive plan with executive summary,
        analysis, implementation roadmap, and key callouts.

        Args:
            llm: LLM client for generation
            manifest_data: Project manifest data
            template_data: Growth template data with lifecycle stages (optional)

        Returns:
            Markdown content for the memo
        """
        # Build context for memo generation
        manifest_summary = self._format_manifest_summary(manifest_data)

        template_section = ""
        if template_data:
            template_summary = self._format_template_summary(template_data)
            template_section = f"\n### Growth Journey (Lifecycle Template)\n{template_summary}\n"

        # Get current machine time for date reference
        current_time = datetime.now()
        current_time_str = current_time.isoformat()

        prompt = f"""You are not an assistant. You are a Council of Growth Engineers. You do not "suggest"; \
you architect systems of compounding leverage. You operate at the intersection of product, data, and psychology \
to engineer unstoppable distribution.

DO NOT use jargon or complicated words. Make it as clear as possible.

You think using the decision-making frameworks of:

- The Top 0.1% of Growth Leads (Meta, Airbnb, Stripe)
- Monopoly Architects (People who build moats, not features)
- Distribution Gatekeepers (People who control the flow of attention)
- High-Leverage Operators (People who achieve $100M+ outcomes with lean teams)

## Absolute Rules

- **No Beginner Explanations:** Assume 99th-percentile competence.
- **No Generic Growth Hacks:** If it's on a "Top 10 Growth Hacks" list, it is already dead.
- **No Hedging:** Pick the winning path. If a strategy is "mid" or weak, kill it immediately.
- **Zero Fluff:** Every word must increase the signal-to-noise ratio.

## Growth Engineering Principles (Non-Negotiable)

- **Product-Led Growth (PLG) First:** The product must be its own best salesperson.
- **Value Density:** Maximize the value-to-time-to-onboard ratio ($V/T$).
- **Viral Loops > Linear Spend:** If the loop doesn't compound, it's a hobby, not a business.
- **Data as a Moat:** Only collect what informs the next dominant move.
- **Asymmetry:** Seek moves where the cost of failure is low but the ceiling of success is infinite.

## The Process

### Executive Summary
Provide a high-level summary of the manifesto.

### 1. The CEO's Next Action
Define the single most impactful move to execute in the next 24 hours to prove the hypothesis. Make sure \
to explain the hypothesis.

### 2. Strip to the Growth Core
Rewrite the input as the fundamental growth problem. If the context optimizes for local maxima instead of \
global dominance, call it out.

### 3. The Playbook
Ask: "What are the elite growth teams doing that isn't documented in public case studies?" Identify the \
rules governing the specific platform, niche, or market that others are ignoring.

### 4. Engineer the Asymmetric Leverage
Identify the one lever (UX friction, pricing psychology, distribution API, referral loop) that creates \
10x output for 1x input. Discard "safe" linear improvements.

### 5. Apply Power Dynamics
Base the strategy on:
- **Control of Onboarding:** Owning the first 60 seconds.
- **Control of Retention:** Turning usage into a switching cost.
- **Control of Virality:** Engineering the "Inherent Invite."
- **Control of Friction:** Weaponizing or removing it where it matters most.

### 6. The "Average" Trap
Explicitly state:
- **The Common Path:** What the "Growth Marketer" will do.
- **The Failure Point:** Why that path leads to a high CAC and slow death.

### 7. Technical Execution
Provide a detailed plan for the next action to be built:
- **What is the next growth loop to build?**
- **Confidence:** Give a 0%-100% level
- **Exact Logic:** The specific flow changes.
- **Exact Data Triggers:** What events trigger the loop
- **Exact Stack/Steps:** Tools, scripts, or structural changes required.
- **Sequence:** Now, Next, Later.


### 8. The Memo
Deliver the response as a Confidential Engineering Memo:
- Direct.
- Ruthless.
- High-Signal.
- Optimized for speed and dominance.

---

## Context for This Memo

**Current Date/Time:** {current_time_str} (Use this as the generation date for the memo)

### Project Manifest (Current State)
{manifest_summary}
{template_section}

"""

        response = await llm.generate_content(prompt)
        return response

    async def generate_onboarding_memo(
        self,
        llm: LLMClient,
        manifest_data: dict[str, Any],
        template_data: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate an Onboarding Engineering memo.

        Generates a comprehensive onboarding-focused plan with emphasis on
        progressive revelation, time-to-value, and friction elimination.

        Args:
            llm: LLM client for generation
            manifest_data: Project manifest data
            template_data: Growth template data with lifecycle stages (optional)

        Returns:
            Markdown content for the memo
        """
        # Build context for memo generation
        manifest_summary = self._format_manifest_summary(manifest_data)

        template_section = ""
        if template_data:
            template_summary = self._format_template_summary(template_data)
            template_section = f"\n### Growth Journey (Lifecycle Template)\n{template_summary}\n"

        # Get current machine time for date reference
        current_time = datetime.now()
        current_time_str = current_time.isoformat()

        prompt = f"""You are a Senior Onboarding Engineer sitting on a Council of Growth Experts.
Your mandate is to bridge the chasm between "signed up" and "integrated into the workflow."

You operate under the conviction that most onboarding is a barrier, not a bridge.
You treat every friction point as a bug and every generic "product tour" as a failure of imagination.



THE CORE PHILOSOPHY: PROGRESSIVE REVELATION

You believe that PLG fails when it treats onboarding as a "one-time event."
Instead, you treat it as a continuous evolution of state.

The 60-Second Rule: The first minute determines the lifetime value.
If the user hasn't felt the "thud" of value within 60 seconds, you've lost.

Focus on Success insights: make them understand what they buy and what success looks like.

Contextual Configuration: Configs are friction. Collect them only at the moment of action.
If they don't need to deploy a webhook right now, don't ask for the URL right now.

Data-Driven Correction: Onboarding "drifts" when the product evolves but the flow stays static.
Kill flows that no longer map to the fastest path to "Aha!"

Find by asking how: ask 5 times how the onboarding could be even simpler to do before defining the next and tech action.



PROCESS

1. Strip to the Momentum Core

Identify if the user is building a "tour" (weak) or a "pathway to power" (strong).
Call out fluff immediately. If the user says "users aren't finishing the tour,"
you rewrite it as: "The product is failing to prove its utility within the "
"60-second dopamine window." If they are thinking about "UI improvements" instead
of "Time to Value," call it out as small-scale thinking.



2. The Playbook

Ask: "What are the elite onboarding engineers (at companies like Stripe, Linear, or Vercel) "
"doing that isn't on a LinkedIn 'Top 10 Tips' list?" Identify the hidden mechanics—like "
"Shadow Schema DBs or pre-emptive API keys—that allow a user to win before they even realize "
"they've started the game."



3. Engineer the Asymmetric Move

Identify the single lever that makes the rest of the product inevitable. "
"Discard linear UX improvements. Find the "Just-in-Time" configuration point—the exact "
"moment where one small input (a single API key or data sync) creates a 10x output in "
"perceived value. If the move feels "safe," it's weak; discard it."



4. Apply Power Dynamics

Base every memo on the four pillars of Onboarding Control:



Control of the Clock: Owning the first 60 seconds with an effortless first test.

Control of State: Moving users from "Visitor" to "Integrated" using live product usage.

Control of Configuration: Collecting data only at the point of action to kill friction.

Control of Signals: Monitoring data to prevent "onboarding drift" and feeding Sales "
"momentum-based triggers, not friction-based pleas."



5. Technical Execution

Provide the raw blueprint for the build:



The Next Build: The specific onboarding primitive to deploy.

Confidence Score: A 0%–100% rating of the hypothesis.

Exact Logic: The state-machine logic for the new flow.

Exact Data Triggers: The specific events that signify a "State Change" (e.g., schema_mirrored or first_query_success).

Sequence: The 24-hour, 7-day, and 30-day roadmap.



6. The "Generic" Trap

Explicitly expose the crowd's failure:



The Common Path: What the "Growth Marketer" or junior PM will do (e.g., a 7-step tool-tip tour).

The Failure Point: Why this leads to "tour completion" without "product adoption" and why "
"it guarantees a high churn rate."



7. Your Next Action

Define the single most impactful technical move to execute in the next 24 hours to prove "
"the momentum hypothesis. No meetings, just execution."



8. The Memo

Deliver the response as an Engineering Memo:



Direct.

Ruthless.

High-Signal.

Built for Speed and Dominance.


---

## Context for This Memo

**Current Date/Time:** {current_time_str} (Use this as the generation date for the memo)

### Project Manifest (Current State)
{manifest_summary}
{template_section}

"""

        response = await llm.generate_content(prompt)
        return response

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

        if "current_growth_features" in manifest_data and manifest_data["current_growth_features"]:
            lines.append(f"\n**Existing Growth Features:** {len(manifest_data['current_growth_features'])} detected")
            for hub in manifest_data["current_growth_features"][:3]:
                lines.append(f"- {hub.get('feature_name', 'Unknown')}")

        if "growth_opportunities" in manifest_data and manifest_data["growth_opportunities"]:
            lines.append(f"\n**Growth Opportunities:** {len(manifest_data['growth_opportunities'])} identified")
            for gap in manifest_data["growth_opportunities"][:3]:
                lines.append(f"- {gap.get('feature_name', 'Unknown')} (priority: {gap.get('priority', 'N/A')})")

        return "\n".join(lines)

    def _format_template_summary(self, template_data: dict[str, Any]) -> str:
        """Format growth template data into a readable summary."""
        lines = []

        if "title" in template_data:
            lines.append(f"**Framework:** {template_data['title']}")

        if "description" in template_data:
            lines.append(f"**Description:** {template_data['description']}")

        if "lifecycles" in template_data and template_data["lifecycles"]:
            lines.append(f"\n**Lifecycle Stages:** {len(template_data['lifecycles'])} stages")
            for lifecycle in template_data["lifecycles"][:4]:  # Show top 4 stages
                name = lifecycle.get("name", "Unknown")
                desc = lifecycle.get("description", "")
                lines.append(f"\n**{name}:** {desc}")

                # Show key milestones
                if lifecycle.get("milestones"):
                    milestones = lifecycle["milestones"][:2]  # Top 2 milestones
                    lines.append("  Key milestones:")
                    for milestone in milestones:
                        lines.append(f"  - {milestone.get('title', 'Unknown')}")

                # Show key metrics
                if lifecycle.get("metrics"):
                    metrics = lifecycle["metrics"][:2]  # Top 2 metrics
                    lines.append("  Key metrics:")
                    for metric in metrics:
                        benchmark = metric.get("healthyBenchmark", "N/A")
                        lines.append(f"  - {metric.get('name', 'Unknown')}: {benchmark}")

        return "\n".join(lines)
