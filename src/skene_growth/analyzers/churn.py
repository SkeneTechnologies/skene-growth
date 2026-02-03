"""
Churn point analyzer.

Identifies specific points-of-churn in the user journey and generates
targeted change definitions to address them.
"""

from pydantic import BaseModel, Field

from skene_growth.llm import LLMClient
from skene_growth.strategies import MultiStepStrategy
from skene_growth.strategies.steps import AnalyzeStep, ReadFilesStep, SelectFilesStep


class ChurnPoint(BaseModel):
    """A single point-of-churn identified in the user journey."""

    lifecycle_stage: str = Field(
        description="Which lifecycle stage this churn occurs in (e.g., ACQUISITION, ACTIVATION, RETENTION)"
    )
    milestone: str = Field(description="Specific milestone or step where users drop off")
    existing_process: str = Field(description="The current process or flow that is causing churn (what exists now)")
    success_definition: str = Field(
        description="What 'success' means for this process - how users know they've completed it successfully"
    )
    time_to_understand_success: int = Field(
        description="Estimated time in seconds it takes for a user to understand if they've succeeded in this process"
    )
    exceeds_60s_threshold: bool = Field(
        description="Whether the time-to-understand-success exceeds 60 seconds (indicates churn risk)"
    )
    complexity_issues: list[str] = Field(
        default_factory=list,
        description="Specific ways in which the existing process is overly complex or has friction",
    )
    churn_description: str = Field(
        description="Detailed description of why users churn at this point due to process complexity"
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Evidence from codebase or manifest supporting this churn point",
    )
    impact: str = Field(description="Estimated impact on growth metrics (e.g., 'High: 40% drop-off rate')")
    root_cause: str = Field(
        description=(
            "Root cause analysis: why the existing process complexity causes churn, "
            "especially related to time-to-understand-success"
        )
    )


class ChangeDefinition(BaseModel):
    """A specific change to address a churn point."""

    churn_point: ChurnPoint = Field(description="The churn point this change addresses")
    change_title: str = Field(description="Clear, actionable title for the change")
    change_description: str = Field(description="Detailed description of what to change and why")
    implementation_steps: list[str] = Field(default_factory=list, description="Step-by-step implementation plan")
    files_to_modify: list[str] = Field(
        default_factory=list, description="Specific files that need to be modified or created"
    )
    code_examples: list[str] = Field(
        default_factory=list, description="Code snippets or examples showing how to implement the change"
    )
    success_metrics: list[str] = Field(
        default_factory=list, description="How to measure if this change successfully addresses the churn"
    )
    estimated_impact: str = Field(description="Expected improvement in metrics after implementing this change")
    priority: str = Field(description="Priority level: 'critical', 'high', 'medium', or 'low'")


CHURN_ANALYSIS_PROMPT = """
Analyze the provided codebase and growth manifest to identify a SINGLE, specific point-of-churn
where an EXISTING PROCESS takes users MORE THAN 60 SECONDS to understand if they've succeeded.

CRITICAL METRIC: Time-to-Understand-Success (TTUS) - How long does it take a user to know
they've completed the process successfully?

IMPORTANT: Focus on EXISTING processes/flows where users cannot quickly understand success, not missing features.

A "point-of-churn" is where an existing process has unclear success indicators that cause:
- Users to abandon because they don't know if they succeeded
- Users to repeat steps unnecessarily because success isn't clear
- Users to drop off due to confusion about completion
- Significant drop-off rates because success takes >60 seconds to understand

Focus on identifying ONE existing process where TTUS > 60 seconds.

Consider:
1. **Lifecycle Stage**: Which stage (ACQUISITION, ACTIVATION, RETENTION, REVENUE, REFERRAL)?
2. **Existing Process**: What is the current process/flow that exists?
   (e.g., signup flow, onboarding steps, checkout process, feature activation)
3. **Success Definition**: What does "success" mean for this process?
   How should users know they've completed it?
4. **Time-to-Understand-Success**: Estimate how many seconds it takes for a user to understand they've succeeded:
   - Count time to read/understand success messages
   - Count time to navigate to confirmation pages
   - Count time to interpret feedback/indicators
   - Count time to verify completion
   - Include any delays or unclear indicators
5. **Specific Milestone**: What exact step in the existing process do users fail to
   complete or understand?
6. **Complexity Issues**: What makes success unclear?
   (no clear confirmation, delayed feedback, confusing UI, multiple steps to verify, etc.)
7. **Root Cause**: Why does it take >60 seconds to understand success?
   What's causing the delay/confusion?
8. **Evidence**: What in the codebase suggests success is unclear?
   (file paths, code structure, lack of clear feedback, etc.)

Return a single, well-defined churn point with:
- lifecycle_stage: The lifecycle stage where churn occurs
- milestone: The specific milestone or step where users drop off
- existing_process: Description of the current process/flow that exists (what it is now)
- success_definition: What "success" means for this process - how users should know they've succeeded
- time_to_understand_success: Estimated time in seconds (be specific, e.g., 90, 120, 180)
- exceeds_60s_threshold: Boolean - true if time_to_understand_success > 60
- complexity_issues: List of specific ways the existing process makes success unclear
  (e.g., "no immediate confirmation", "success message buried 3 pages deep",
  "requires checking email to verify")
- churn_description: Why users churn at this point due to unclear success indicators
- evidence: List of specific evidence from codebase/manifest showing unclear success indicators
- impact: Estimated impact on growth metrics
- root_cause: Root cause analysis of why it takes >60s to understand success
  and how this causes churn

Be specific and actionable. Focus on ONE existing process where TTUS > 60 seconds that,
if simplified, would have the biggest impact.
"""

CHANGE_DEFINITION_PROMPT = """
Given the identified churn point where time-to-understand-success exceeds 60 seconds,
define a SPECIFIC, ACTIONABLE SIMPLIFICATION to reduce TTUS to under 60 seconds
and address the churn.

CRITICAL GOAL: Reduce time-to-understand-success from {current_ttus}s to under 60 seconds.

CRITICAL: This must be a SIMPLIFICATION of the existing process, NOT a new feature or addition.

The simplification should:
- Make success immediately clear and obvious (<60 seconds to understand)
- Add clear, immediate success indicators (confirmation messages, visual feedback, etc.)
- Remove steps that delay or obscure success understanding
- Streamline the current flow to reduce time-to-understand-success
- Keep the core functionality but make success clearer
- Be concrete and implementable (not vague suggestions)
- Target the specific issues making success unclear
- Be realistic given the current tech stack
- Be measurable (with clear success metrics)

DO NOT:
- Add new features or functionality beyond clarity improvements
- Create new processes or flows
- Suggest new integrations or tools
- Propose complex new UI components

DO:
- Add immediate, clear success confirmation (within the same page/step)
- Remove steps that delay success understanding
- Combine multiple steps into one with clear success indicator
- Add visual/instant feedback when success is achieved
- Simplify the success verification process
- Make success indicators more prominent and immediate
- Reduce the number of steps needed to understand completion

Provide:
1. **change_title**: Clear title focusing on reducing TTUS
   (e.g., "Add immediate success confirmation to reduce TTUS from 120s to 15s")
2. **change_description**: What exactly to simplify to make success clear and reduce TTUS
   (what to add/remove/change)
3. **implementation_steps**: Step-by-step plan for making success clear
   (what to add, what to remove, what to change)
4. **files_to_modify**: Specific files that contain the process with unclear success indicators
5. **code_examples**: Code snippets showing the BEFORE (unclear success, TTUS >60s)
   and AFTER (clear success, TTUS <60s) versions
6. **success_metrics**: How to measure if TTUS was reduced and churn decreased
7. **estimated_impact**: Expected improvement in TTUS (e.g., "Reduce from 120s to 20s")
   and churn reduction
8. **priority**: Critical, high, medium, or low

Focus on ONE specific simplification that directly reduces time-to-understand-success to under 60 seconds.
"""


class ChurnAnalyzer:
    """Analyzes codebase to identify churn points and define changes."""

    def __init__(self):
        """Initialize the churn analyzer."""
        pass

    async def identify_churn_point(
        self,
        codebase,
        llm: LLMClient,
    ) -> ChurnPoint:
        """
        Identify a single point-of-churn in the user journey.

        Args:
            codebase: CodebaseExplorer instance
            llm: LLM client for analysis

        Returns:
            ChurnPoint identifying the single churn point
        """
        # Use MultiStepStrategy to analyze codebase for churn indicators
        analyzer = MultiStepStrategy(
            steps=[
                SelectFilesStep(
                    prompt=(
                        "Select files that contain EXISTING user processes/flows that might be "
                        "overly complex. Look for: "
                        "- User onboarding flows, signup processes, activation steps "
                        "(existing implementations)\n"
                        "- Authentication/authorization flows (current multi-step processes)\n"
                        "- Form handling, multi-step wizards, or complex user inputs\n"
                        "- Payment/subscription flows (checkout processes)\n"
                        "- User settings or configuration flows\n"
                        "- Any multi-step processes or flows with many components/steps"
                    ),
                    patterns=[
                        "**/*auth*.py",
                        "**/*auth*.ts",
                        "**/*auth*.tsx",
                        "**/*onboard*.py",
                        "**/*onboard*.ts",
                        "**/*signup*.py",
                        "**/*signup*.ts",
                        "**/routes/**/*",
                        "**/api/**/*",
                        "**/pages/**/*",
                        "**/components/**/*",
                    ],
                    max_files=20,
                    output_key="churn_files",
                ),
                ReadFilesStep(
                    source_key="churn_files",
                    output_key="churn_contents",
                ),
                AnalyzeStep(
                    prompt=CHURN_ANALYSIS_PROMPT,
                    output_schema=ChurnPoint,
                    output_key="churn_point",
                    source_key="churn_contents",
                ),
            ]
        )

        result = await analyzer.run(
            codebase=codebase,
            llm=llm,
            request="Identify the single most impactful point-of-churn",
        )

        if not result.success:
            raise RuntimeError(f"Churn analysis failed: {result.error}")

        churn_point_data = result.data.get("churn_point", {})
        return ChurnPoint(**churn_point_data)

    async def define_change(
        self,
        codebase,
        llm: LLMClient,
        churn_point: ChurnPoint,
    ) -> ChangeDefinition:
        """
        Define a specific change to address the identified churn point.

        Args:
            codebase: CodebaseExplorer instance
            llm: LLM client for generation
            churn_point: The identified churn point

        Returns:
            ChangeDefinition with specific implementation plan
        """
        churn_context = f"""
## Identified Churn Point

**Lifecycle Stage:** {churn_point.lifecycle_stage}
**Milestone:** {churn_point.milestone}
**Existing Process:** {churn_point.existing_process}
**Success Definition:** {churn_point.success_definition}
**Time-to-Understand-Success:** {churn_point.time_to_understand_success} seconds
**Exceeds 60s Threshold:** {churn_point.exceeds_60s_threshold} {
            "⚠️ CRITICAL: TTUS > 60s" if churn_point.exceeds_60s_threshold else "✓ TTUS within threshold"
        }
**Complexity Issues:**
{chr(10).join(f"- {issue}" for issue in churn_point.complexity_issues)}
**Description:** {churn_point.churn_description}
**Root Cause:** {churn_point.root_cause}
**Impact:** {churn_point.impact}

**Evidence:**
{chr(10).join(f"- {e}" for e in churn_point.evidence)}
"""

        # Analyze relevant files for implementation context
        analyzer = MultiStepStrategy(
            steps=[
                SelectFilesStep(
                    prompt=(
                        f"Select files that contain the EXISTING process to simplify: "
                        f"{churn_point.existing_process} at {churn_point.milestone} "
                        f"in {churn_point.lifecycle_stage}. "
                        f"Look for files implementing the current complex flow: "
                        f"{churn_point.churn_description}. "
                        f"Focus on files that contain the process with complexity issues: "
                        f"{', '.join(churn_point.complexity_issues[:3])}"
                    ),
                    patterns=[
                        "**/*.py",
                        "**/*.ts",
                        "**/*.tsx",
                        "**/*.js",
                        "**/routes/**/*",
                        "**/api/**/*",
                    ],
                    max_files=15,
                    output_key="implementation_files",
                ),
                ReadFilesStep(
                    source_key="implementation_files",
                    output_key="implementation_contents",
                ),
                AnalyzeStep(
                    prompt=CHANGE_DEFINITION_PROMPT.format(current_ttus=churn_point.time_to_understand_success)
                    + "\n\n"
                    + churn_context,
                    output_schema=ChangeDefinition,
                    output_key="change_definition",
                    source_key="implementation_contents",
                ),
            ]
        )

        result = await analyzer.run(
            codebase=codebase,
            llm=llm,
            request=(
                f"Define a specific simplification to reduce time-to-understand-success "
                f"from {churn_point.time_to_understand_success}s to under 60s for process "
                f"'{churn_point.existing_process}' at {churn_point.milestone}"
            ),
        )

        if not result.success:
            raise RuntimeError(f"Change definition failed: {result.error}")

        change_data = result.data.get("change_definition", {})
        # Ensure churn_point is included in the change definition
        change_data["churn_point"] = churn_point.model_dump()
        return ChangeDefinition(**change_data)
