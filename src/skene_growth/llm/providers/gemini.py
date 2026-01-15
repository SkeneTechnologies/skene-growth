"""
Google Gemini LLM client implementation.
"""

import asyncio
from functools import partial
from typing import AsyncGenerator, Optional

from loguru import logger
from pydantic import SecretStr

from skene_growth.llm.base import LLMClient

# Default fallback model for rate limiting (429 errors)
DEFAULT_FALLBACK_MODEL = "gemini-2.5-flash"


class GoogleGeminiClient(LLMClient):
    """
    Google Gemini LLM client.

    Handles rate limiting by automatically falling back to a secondary model
    when the primary model returns a 429 RESOURCE_EXHAUSTED error.

    Example:
        client = GoogleGeminiClient(
            api_key=SecretStr("your-api-key"),
            model_name="gemini-2.5-pro"
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
        Initialize the Gemini client.

        Args:
            api_key: Google API key (wrapped in SecretStr for security)
            model_name: Primary model to use (e.g., "gemini-2.5-pro")
            fallback_model: Model to use when rate limited (default: gemini-2.5-flash)
        """
        try:
            from google import genai
        except ImportError:
            raise ImportError(
                "google-genai is required for Gemini support. Install with: pip install skene-growth[gemini]"
            )

        self.api_key = api_key.get_secret_value()
        self.model_name = model_name
        self.fallback_model = fallback_model or DEFAULT_FALLBACK_MODEL
        self.client = genai.Client(api_key=self.api_key)

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if the error is a 429 rate limit error."""
        error_str = str(error)
        return "429" in error_str and "RESOURCE_EXHAUSTED" in error_str

    async def generate_content(
        self,
        prompt: str,
    ) -> str:
        """
        Generate text from Gemini.

        Automatically retries with fallback model on rate limit errors.

        Args:
            prompt: The prompt to send to the model

        Returns:
            Generated text as a string

        Raises:
            RuntimeError: If generation fails on both primary and fallback models
        """
        try:
            # Run the blocking call in a thread pool executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    self.client.models.generate_content,
                    model=self.model_name,
                    contents=prompt,
                ),
            )

            return response.text.strip()
        except Exception as e:
            # If rate limit error, retry with fallback model
            if self._is_rate_limit_error(e):
                logger.warning(
                    f"Rate limit (429) hit on model {self.model_name}, falling back to {self.fallback_model}"
                )
                try:
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        partial(
                            self.client.models.generate_content,
                            model=self.fallback_model,
                            contents=prompt,
                        ),
                    )
                    logger.info(f"Successfully generated content using fallback model {self.fallback_model}")
                    return response.text.strip()
                except Exception as fallback_error:
                    raise RuntimeError(
                        f"Error calling Google Gemini (fallback model {self.fallback_model}): {fallback_error}"
                    )
            raise RuntimeError(f"Error calling Google Gemini: {e}")

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
        model_to_use = self.model_name
        try:
            # Use generate_content_stream method for streaming
            # Run the blocking generator creation in thread pool
            loop = asyncio.get_event_loop()
            response_stream = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content_stream(
                    model=model_to_use,
                    contents=prompt,
                ),
            )

            # Iterate through chunks
            # Each iteration needs to be run in executor since it's blocking I/O
            def get_next_chunk(iterator):
                try:
                    return next(iterator), False
                except StopIteration:
                    return None, True

            chunk_iterator = iter(response_stream)
            while True:
                chunk, done = await loop.run_in_executor(None, get_next_chunk, chunk_iterator)

                if done:
                    break

                if chunk and hasattr(chunk, "text") and chunk.text:
                    yield chunk.text

        except Exception as e:
            # If rate limit error and haven't tried fallback yet, retry with fallback model
            if self._is_rate_limit_error(e) and model_to_use == self.model_name:
                logger.warning(
                    f"Rate limit (429) hit on model {self.model_name} during streaming, "
                    f"falling back to {self.fallback_model}"
                )
                try:
                    loop = asyncio.get_event_loop()
                    response_stream = await loop.run_in_executor(
                        None,
                        lambda: self.client.models.generate_content_stream(
                            model=self.fallback_model,
                            contents=prompt,
                        ),
                    )

                    def get_next_chunk(iterator):
                        try:
                            return next(iterator), False
                        except StopIteration:
                            return None, True

                    chunk_iterator = iter(response_stream)
                    logger.info(f"Successfully started streaming with fallback model {self.fallback_model}")
                    while True:
                        chunk, done = await loop.run_in_executor(None, get_next_chunk, chunk_iterator)

                        if done:
                            break

                        if chunk and hasattr(chunk, "text") and chunk.text:
                            yield chunk.text
                except Exception as fallback_error:
                    raise RuntimeError(
                        f"Error in streaming generation (fallback model {self.fallback_model}): {fallback_error}"
                    )
            else:
                raise RuntimeError(f"Error in streaming generation: {e}")

    def get_model_name(self) -> str:
        """Return the primary model name."""
        return self.model_name

    def get_provider_name(self) -> str:
        """Return the provider name."""
        return "google"
