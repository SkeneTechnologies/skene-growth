"""
Step for generating final output with LLM.
"""

import json
import re
from typing import Any, Type

from loguru import logger
from pydantic import BaseModel

from skene_growth.codebase import CodebaseExplorer
from skene_growth.llm import LLMClient
from skene_growth.strategies.context import AnalysisContext, StepResult
from skene_growth.strategies.steps.base import AnalysisStep


class GenerateStep(AnalysisStep):
    """
    LLM generates final output from accumulated context.

    This step is typically used as the final step in a strategy,
    combining all previous analysis into a final output.

    Example:
        step = GenerateStep(
            prompt="Combine the analysis into a complete growth manifest",
            output_schema=GrowthManifest,
        )
    """

    name = "generate"

    def __init__(
        self,
        prompt: str,
        output_schema: Type[BaseModel] | None = None,
        include_context_keys: list[str] | None = None,
        output_key: str = "output",
    ):
        """
        Initialize the generation step.

        Args:
            prompt: Instruction for the LLM on what to generate
            output_schema: Optional Pydantic model for structured output
            include_context_keys: Specific context keys to include (all if None)
            output_key: Context key to store generated output
        """
        self.prompt = prompt
        self.output_schema = output_schema
        self.include_context_keys = include_context_keys
        self.output_key = output_key

    async def execute(
        self,
        codebase: CodebaseExplorer,
        llm: LLMClient,
        context: AnalysisContext,
    ) -> StepResult:
        """Execute the generation step."""
        try:
            # Build prompt with context
            llm_prompt = self._build_prompt(context)

            # Get LLM response
            response = await llm.generate_content(llm_prompt)

            # Parse response
            parsed = self._parse_response(response)

            logger.info("GenerateStep completed")

            return StepResult(
                step_name=self.name,
                data={self.output_key: parsed},
                tokens_used=len(llm_prompt) // 4,  # Rough estimate
            )

        except Exception as e:
            logger.error(f"GenerateStep failed: {e}")
            return StepResult(
                step_name=self.name,
                error=str(e),
            )

    def _build_prompt(self, context: AnalysisContext) -> str:
        """Build the prompt for generation."""
        prompt_parts = [
            "You are generating structured output based on analysis results.",
            "",
            "## Task",
            self.prompt,
            "",
            "## Original Request",
            context.request,
        ]

        # Get context data to include
        all_data = context.get_all_data()
        if self.include_context_keys:
            data_to_include = {k: v for k, v in all_data.items() if k in self.include_context_keys}
        else:
            # Exclude large data like file_contents by default
            data_to_include = {k: v for k, v in all_data.items() if k != "file_contents" and not k.startswith("_")}

        if data_to_include:
            prompt_parts.extend(
                [
                    "",
                    "## Analysis Results",
                    "Use this information to generate your output:",
                    "",
                    "```json",
                    json.dumps(data_to_include, indent=2, default=str),
                    "```",
                ]
            )

        # Add output format instructions
        prompt_parts.extend(
            [
                "",
                "## Output Format",
            ]
        )

        if self.output_schema:
            schema = self.output_schema.model_json_schema()
            prompt_parts.extend(
                [
                    "Generate output as JSON matching this schema:",
                    "```json",
                    json.dumps(schema, indent=2),
                    "```",
                ]
            )
        else:
            prompt_parts.extend(
                [
                    "Generate output as a JSON object.",
                ]
            )

        prompt_parts.extend(
            [
                "",
                "Return ONLY valid JSON, no other text.",
            ]
        )

        return "\n".join(prompt_parts)

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse LLM response to extract structured data."""
        # Try direct JSON parse
        try:
            parsed = json.loads(response.strip())
            if isinstance(parsed, dict):
                return self._validate_output(parsed)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", response)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1).strip())
                if isinstance(parsed, dict):
                    return self._validate_output(parsed)
            except json.JSONDecodeError:
                pass

        # Try to find JSON object pattern
        obj_match = re.search(r"\{[\s\S]*\}", response)
        if obj_match:
            try:
                parsed = json.loads(obj_match.group(0))
                if isinstance(parsed, dict):
                    return self._validate_output(parsed)
            except json.JSONDecodeError:
                pass

        logger.warning(f"Could not parse generation response as JSON: {response[:200]}")
        return {"raw_response": response}

    def _unwrap_items(self, data: Any) -> Any:
        """Recursively unwrap {'items': [...]} dicts back to plain lists."""
        if isinstance(data, dict):
            # If dict has only 'items' key with a list value, unwrap it
            if list(data.keys()) == ["items"] and isinstance(data["items"], list):
                return [self._unwrap_items(item) for item in data["items"]]
            # Otherwise recurse into dict values
            return {k: self._unwrap_items(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._unwrap_items(item) for item in data]
        return data

    def _validate_output(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate output against schema if provided."""
        # Unwrap any {"items": [...]} patterns back to plain lists
        data = self._unwrap_items(data)

        if self.output_schema:
            try:
                validated = self.output_schema.model_validate(data)
                return validated.model_dump()
            except Exception as e:
                logger.warning(f"Output validation failed: {e}")
                return data
        return data
