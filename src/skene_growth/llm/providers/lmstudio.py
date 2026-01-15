"""
LM Studio LLM client implementation.

LM Studio provides an OpenAI-compatible API for running local LLMs.
Default endpoint: http://localhost:1234/v1
"""

import os
from typing import AsyncGenerator, Optional

from loguru import logger
from pydantic import SecretStr

from skene_growth.llm.base import LLMClient

# Default LM Studio server URL
DEFAULT_BASE_URL = "http://localhost:1234/v1"


class LMStudioClient(LLMClient):
    """
    LM Studio LLM client.

    Uses the OpenAI-compatible API provided by LM Studio for local LLM inference.
    The base URL can be configured via the LMSTUDIO_BASE_URL environment variable
    or passed directly to the constructor.

    Example:
        client = LMStudioClient(
            api_key=SecretStr("lm-studio"),  # API key is optional for local use
            model_name="local-model"
        )
        response = await client.generate_content("Hello!")
    """

    def __init__(
        self,
        api_key: SecretStr,
        model_name: str,
        base_url: Optional[str] = None,
    ):
        """
        Initialize the LM Studio client.

        Args:
            api_key: API key (can be any value for local LM Studio)
            model_name: Model name loaded in LM Studio
            base_url: LM Studio server URL (default: http://localhost:1234/v1)
                      Can also be set via LMSTUDIO_BASE_URL environment variable
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError(
                "openai is required for LM Studio support. Install with: pip install skene-growth[openai]"
            )

        self.model_name = model_name
        self.base_url = base_url or os.environ.get("LMSTUDIO_BASE_URL", DEFAULT_BASE_URL)

        # Use the API key if provided, otherwise use a placeholder
        # LM Studio doesn't require authentication for local access
        api_key_value = api_key.get_secret_value() if api_key else "lm-studio"

        self.client = AsyncOpenAI(
            api_key=api_key_value,
            base_url=self.base_url,
        )

        logger.debug(f"LM Studio client initialized with base_url: {self.base_url}")

    async def generate_content(
        self,
        prompt: str,
    ) -> str:
        """
        Generate text from LM Studio.

        Args:
            prompt: The prompt to send to the model

        Returns:
            Generated text as a string

        Raises:
            RuntimeError: If generation fails
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"Error calling LM Studio: {e}")

    async def generate_content_stream(
        self,
        prompt: str,
    ) -> AsyncGenerator[str, None]:
        """
        Generate content with streaming.

        Args:
            prompt: The prompt to send to the model

        Yields:
            Text chunks as they are generated

        Raises:
            RuntimeError: If streaming fails
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise RuntimeError(f"Error in LM Studio streaming generation: {e}")

    def get_model_name(self) -> str:
        """Return the model name."""
        return self.model_name

    def get_provider_name(self) -> str:
        """Return the provider name."""
        return "lmstudio"
