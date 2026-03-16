"""
Abstract base class for LLM clients.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator


class LLMClient(ABC):
    """
    Abstract base class for LLM clients.

    Provides a unified interface to interact with different LLM providers.
    Implementations should handle provider-specific details internally.

    Subclasses must implement ``generate_content_with_usage``,
    ``generate_content_stream``, ``get_model_name``, and ``get_provider_name``.

    Example:
        client = create_llm_client("gemini", api_key, "gemini-3-flash-preview")
        response = await client.generate_content("Hello, world!")
    """

    @abstractmethod
    async def generate_content_with_usage(self, prompt: str) -> tuple[str, dict[str, int] | None]:
        """Generate content and return (content, usage_dict).

        Usage dict has ``output_tokens`` and ``input_tokens`` keys.
        Return ``None`` for usage when the provider doesn't expose token counts.
        """
        pass

    async def generate_content(self, prompt: str) -> str:
        """Generate text from the LLM (convenience wrapper that discards usage)."""
        content, _ = await self.generate_content_with_usage(prompt)
        return content

    @abstractmethod
    async def generate_content_stream(
        self,
        prompt: str,
    ) -> AsyncGenerator[str, None]:
        """
        Generate text from the LLM with streaming.

        Args:
            prompt: User input or message content

        Yields:
            Text chunks as they are generated
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the name of the underlying model."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'google', 'openai')."""
        pass
