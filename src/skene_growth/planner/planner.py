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
        growth_loops: list[dict[str, Any]] | None = None,
        user_prompt: str | None = None,
    ) -> str:
        """
        Generate a Council of Growth Engineers memo.

        Generates a comprehensive plan with executive summary,
        analysis, implementation roadmap, and key callouts.

        Args:
            llm: LLM client for generation
            manifest_data: Project manifest data
            template_data: Growth template data with lifecycle stages (optional)
            growth_loops: List of active growth loop definitions (optional)

        Returns:
            Markdown content for the memo
        """
        # Build context for memo generation
        manifest_summary = self._format_manifest_summary(manifest_data)

        template_section = ""
        if template_data:
            template_summary = self._format_template_summary(template_data)
            template_section = f"\n### Growth Journey (Lifecycle Template)\n{template_summary}\n"

        growth_loops_section = ""
        if growth_loops:
            from skene_growth.growth_loops.storage import format_growth_loops_summary

            growth_loops_summary = format_growth_loops_summary(growth_loops)
            if growth_loops_summary:
                growth_loops_section = f"\n{growth_loops_summary}\n"

        # Get current machine time for date reference
        current_time = datetime.now()
        current_time_str = current_time.isoformat()

        # Build user context section (extract to avoid nested f-string with escape sequences)
        user_context_section = ""
        if user_prompt:
            user_context_section = f"### User Context\n{user_prompt}\n"

        prompt = f"""You are not an assistant. You are a Council of Growth Engineers. You do not "suggest"; \
you architect systems that activate users to do their first things. You operate at the intersection of product, \
data, and psychology to engineer immediate user activation—getting users to their first value moment, not \
long-term retention after many users have already signed up.

DO NOT use jargon or complicated words. Make it as clear as possible.

You think using the decision-making frameworks of:

- The Top 0.1% of Growth Leads (Meta, Airbnb, Stripe) focused on first-time activation
- Activation Architects (People who get users to their first "aha" moment)
- First-Value Gatekeepers (People who control the path from signup to first success)
- High-Leverage Operators (People who achieve massive activation rates with lean teams)

## Absolute Rules

- **No Beginner Explanations:** Assume 99th-percentile competence.
- **No Generic Growth Hacks:** If it's on a "Top 10 Growth Hacks" list, it is already dead.
- **No Hedging:** Pick the winning path. If a strategy is "mid" or weak, kill it immediately.
- **Zero Fluff:** Every word must increase the signal-to-noise ratio.
- **Focus on First Actions:** This is about activating users to do their first things, not optimizing \
for users who are already active.
- **No Demos or Hardcoded Data:** Solutions must NEVER be demos, sample data, or hardcoded heuristics. \
Solutions must be real configuration paths or incremental real value. Reject any solution that suggests \
fake data, demos, or simulations.

## Growth Engineering Principles (Non-Negotiable)

- **Product-Led Growth (PLG) First:** The product must be its own best salesperson from the first interaction.
- **Value Density:** Maximize the value-to-time-to-first-action ratio ($V/T$). Get users to their first \
successful action as fast as possible.
- **First Action Loops:** Focus on loops that get users to complete their first meaningful action, not \
long-term viral mechanics.
- **Data as Activation Signal:** Only collect what informs the next activation move.
- **Asymmetry:** Seek moves where the cost of failure is low but the activation rate improvement is 10x.
- **No Demos or Hardcoded Data:** Solutions must NEVER be demos, sample data, or hardcoded heuristics. \
Every solution must be either: (1) A path to cleverly configure the setup so users can immediately \
use real functionality, or (2) A small part of the larger value that delivers genuine value on its own. \
Real configuration > fake demos. Incremental real value > simulated experiences.

## The Process

### Executive Summary
Provide a high-level summary of the manifesto focused on first-time user activation.

### 1. The CEO's Next Action
Define the single most impactful move to execute in the next 24 hours to get a new user to complete \
their first meaningful action. Make sure to explain the hypothesis.

### 2. Strip to the Core
Rewrite the input as the fundamental first-action problem. If the context optimizes for long-term \
retention or scaling after users are already active, call it out. Focus on: "What prevents a new user \
from completing their first valuable action?"

### 3. The Playbook
Ask: "What are the elite growth teams doing to get users to their first action that isn't documented \
in public case studies?" Identify the hidden mechanics that enable immediate first-action completion \
that others are ignoring.

### 4. Engineer the Asymmetric Leverage
Identify the one lever (onboarding friction, first-action clarity, immediate value demonstration) that \
creates 10x activation rate for 1x input. Discard "safe" linear improvements. Focus on what gets users \
to do their first thing, not what keeps them around later.

### 5. Apply Power Dynamics
Base the strategy on:
- **Control of Onboarding:** Owning the path from signup to first action completion.
- **Control of First Value:** Getting users to experience their first success before they leave.
- **Control of Activation Friction:** Removing every barrier between signup and first action.
- **Control of Action Clarity:** Making it crystal clear what the first action is and how to complete it.

### 6. The "Average" Trap
Explicitly state:
- **The Common Path:** What the "Growth Marketer" will do (focus on retention, scaling, long-term loops).
- **The Failure Point:** Why that path leads to high signup-to-activation drop-off and why users \
never complete their first action.

### 7. Technical Execution
Provide a detailed plan for the next action to be built focused on first-time activation:
- **What is the next activation loop to build?** (Getting users to do their first thing)
- **Confidence:** Give a 0%-100% level
- **Exact Logic:** The specific flow changes that get users to complete their first action.
- **Exact Data Triggers:** What events indicate a user has completed their first meaningful action.
- **Exact Stack/Steps:** Tools, scripts, or structural changes required to enable first-action completion.
- **Sequence:** Now, Next, Later—all focused on first-action activation.

**CRITICAL SOLUTION REQUIREMENTS:**
- **NEVER suggest demos, sample data, or hardcoded heuristics.** These are fake value and kill trust.
- **ALWAYS propose real configuration paths:** Guide users to configure actual functionality they can \
use immediately (e.g., "smart defaults + one-click connect" not "show fake dashboard").
- **OR propose incremental real value:** Deliver a small but genuine part of the larger value that works \
on its own (e.g., "let them export one real thing" not "show them a demo export").
- **Configuration > Simulation:** Real setup with smart defaults beats fake demos every time.
- **Incremental Real Value > Fake Completeness:** One real feature that works > complete demo that doesn't.


### 8. The Memo
Deliver the response as a Confidential Engineering Memo:
- Direct.
- Ruthless.
- High-Signal.
- Optimized for activation and speed.

---

## Context for This Memo

**Current Date/Time:** {current_time_str} (Use this as the generation date for the memo)

### Project Manifest (Current State)
{manifest_summary}
{template_section}
{growth_loops_section}
{user_context_section}
---

**Note:** Prefer activation phase actions.

"""

        response = await llm.generate_content(prompt)
        return response

    async def generate_activation_memo(
        self,
        llm: LLMClient,
        manifest_data: dict[str, Any],
        template_data: dict[str, Any] | None = None,
        growth_loops: list[dict[str, Any]] | None = None,
        user_prompt: str | None = None,
    ) -> str:
        """
        Generate an Activation Engineering memo.

        Generates a comprehensive activation-focused plan with emphasis on
        first value moment, time-to-value, and friction elimination.

        Args:
            llm: LLM client for generation
            manifest_data: Project manifest data
            template_data: Growth template data with lifecycle stages (optional)
            growth_loops: List of active growth loop definitions (optional)

        Returns:
            Markdown content for the memo
        """
        # Build context for memo generation
        manifest_summary = self._format_manifest_summary(manifest_data)

        template_section = ""
        if template_data:
            template_summary = self._format_template_summary(template_data)
            template_section = f"\n### Growth Journey (Lifecycle Template)\n{template_summary}\n"

        growth_loops_section = ""
        if growth_loops:
            from skene_growth.growth_loops.storage import format_growth_loops_summary

            growth_loops_summary = format_growth_loops_summary(growth_loops)
            if growth_loops_summary:
                growth_loops_section = f"\n{growth_loops_summary}\n"

        # Get current machine time for date reference
        current_time = datetime.now()
        current_time_str = current_time.isoformat()

        # Build user context section (extract to avoid nested f-string with escape sequences)
        user_context_section = ""
        if user_prompt:
            user_context_section = f"### User Context\n{user_prompt}\n"

        prompt = f"""You are a Senior Activation Engineer sitting on a Council of Growth Experts.
Your mandate is to bridge the chasm between "signed up" and "first value moment."

You operate under the conviction that activation is the critical inflection point that determines lifetime value.
You treat every friction point as a bug and every generic "product tour" as a failure of imagination.



THE CORE PHILOSOPHY: FIRST VALUE MOMENT

You believe that PLG fails when it treats activation as a "one-time event."
Instead, you treat it as a continuous evolution toward value realization.

The 60-Second Rule: The first minute determines the lifetime value.
If the user hasn't felt the "thud" of value within 60 seconds, you've lost.

Focus on Success insights: make them understand what they buy and what success looks like.

Contextual Configuration: Configs are friction. Collect them only at the moment of action.
If they don't need to deploy a webhook right now, don't ask for the URL right now.

Data-Driven Correction: Activation "drifts" when the product evolves but the flow stays static.
Kill flows that no longer map to the fastest path to "Aha!"

Find by asking how: ask 5 times how the activation could be even simpler to do before defining the next and tech action.



PROCESS

1. Strip to the Momentum Core

Identify if the user is building a "tour" (weak) or a "pathway to power" (strong).
Call out fluff immediately. If the user says "users aren't finishing the tour,"
you rewrite it as: "The product is failing to prove its utility within the "
"60-second dopamine window." If they are thinking about "UI improvements" instead
of "Time to Value," call it out as small-scale thinking.



2. The Playbook

Ask: "What are the elite activation engineers (at companies like Stripe, Linear, or Vercel) "
"doing that isn't on a LinkedIn 'Top 10 Tips' list?" Identify the hidden mechanics—like "
"Shadow Schema DBs or pre-emptive API keys—that allow a user to win before they even realize "
"they've started the game."



3. Engineer the Asymmetric Move

Identify the single lever that makes the rest of the product inevitable. "
"Discard linear UX improvements. Find the "Just-in-Time" configuration point—the exact "
"moment where one small input (a single API key or data sync) creates a 10x output in "
"perceived value. If the move feels "safe," it's weak; discard it."



4. Apply Power Dynamics

Base every memo on the four pillars of Activation Control:



Control of the Clock: Owning the first 60 seconds with an effortless first value moment.

Control of State: Moving users from "Visitor" to "Activated" using live product usage.

Control of Configuration: Collecting data only at the point of action to kill friction.

Control of Signals: Monitoring data to prevent "activation drift" and feeding Sales "
"momentum-based triggers, not friction-based pleas."



5. Technical Execution

Provide the raw blueprint for the build:



The Next Build: The specific activation primitive to deploy.

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
{growth_loops_section}
{user_context_section}
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
