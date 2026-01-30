"""
Anthropic LLM client implementation.
"""

from typing import AsyncGenerator, Optional

from loguru import logger
from pydantic import SecretStr

from skene_growth.llm.base import LLMClient

# Default fallback model for rate limiting (429 errors)
DEFAULT_FALLBACK_MODEL = "claude-haiku-4-5-20251001"


class AnthropicClient(LLMClient):
    """
    Anthropic LLM client.

    Handles rate limiting by automatically falling back to a secondary model
    when the primary model returns a 429 rate limit error.

    Example:
        client = AnthropicClient(
            api_key=SecretStr("your-api-key"),
            model_name="claude-haiku-4-5-20251001"
        )
        response = await client.generate_content("Hello!")
    """

    def __init__(
        self,
        api_key: SecretStr,
        model_name: str,
        fallback_model: Optional[str] = None,
    ):
        """
        Initialize the Anthropic client.

        Args:
            api_key: Anthropic API key (wrapped in SecretStr for security)
            model_name: Primary model to use (e.g., "claude-haiku-4-5-20251001")
            fallback_model: Model to use when rate limited (default: claude-haiku-4-5-20251001)
        """
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError(
                "anthropic is required for Anthropic support. Install with: pip install skene-growth[anthropic]"
            )

        self.model_name = model_name
        self.fallback_model = fallback_model or DEFAULT_FALLBACK_MODEL
        self.client = AsyncAnthropic(api_key=api_key.get_secret_value())

    async def generate_content(
        self,
        prompt: str,
    ) -> str:
        """
        Generate text from Anthropic.

        Automatically retries with fallback model on rate limit errors.

        Args:
            prompt: The prompt to send to the model

        Returns:
            Generated text as a string

        Raises:
            RuntimeError: If generation fails on both primary and fallback models
        """
        try:
            from anthropic import RateLimitError
        except ImportError:
            RateLimitError = Exception  # Fallback if import fails

        try:
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except RateLimitError:
            logger.warning(f"Rate limit (429) hit on model {self.model_name}, falling back to {self.fallback_model}")
            try:
                response = await self.client.messages.create(
                    model=self.fallback_model,
                    max_tokens=8192,
                    messages=[{"role": "user", "content": prompt}],
                )
                logger.info(f"Successfully generated content using fallback model {self.fallback_model}")
                return response.content[0].text.strip()
            except Exception as fallback_error:
                raise RuntimeError(f"Error calling Anthropic (fallback model {self.fallback_model}): {fallback_error}")
        except Exception as e:
            raise RuntimeError(f"Error calling Anthropic: {e}")

    async def generate_content_stream(
        self,
        prompt: str,
    ) -> AsyncGenerator[str, None]:
        """
        Generate content with streaming.

        Automatically retries with fallback model on rate limit errors.

        Args:
            prompt: The prompt to send to the model

        Yields:
            Text chunks as they are generated

        Raises:
            RuntimeError: If streaming fails on both primary and fallback models
        """
        try:
            from anthropic import RateLimitError
        except ImportError:
            RateLimitError = Exception

        model_to_use = self.model_name
        try:
            async with self.client.messages.stream(
                model=model_to_use,
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except RateLimitError:
            if model_to_use == self.model_name:
                logger.warning(
                    f"Rate limit (429) hit on model {self.model_name} during streaming, "
                    f"falling back to {self.fallback_model}"
                )
                try:
                    async with self.client.messages.stream(
                        model=self.fallback_model,
                        max_tokens=8192,
                        messages=[{"role": "user", "content": prompt}],
                    ) as stream:
                        logger.info(f"Successfully started streaming with fallback model {self.fallback_model}")
                        async for text in stream.text_stream:
                            yield text
                except Exception as fallback_error:
                    raise RuntimeError(
                        f"Error in streaming generation (fallback model {self.fallback_model}): {fallback_error}"
                    )
            else:
                raise RuntimeError(f"Rate limit error in streaming generation: {model_to_use}")
        except Exception as e:
            raise RuntimeError(f"Error in streaming generation: {e}")

    def get_model_name(self) -> str:
        """Return the primary model name."""
        return self.model_name

    def get_provider_name(self) -> str:
        """Return the provider name."""
        return "anthropic"
