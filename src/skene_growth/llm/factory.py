"""
LLM client factory.
"""

from typing import Optional

from pydantic import SecretStr

from skene_growth.llm.base import LLMClient
from skene_growth.llm.providers.anthropic import AnthropicClient
from skene_growth.llm.providers.gemini import GoogleGeminiClient as GeminiClient
from skene_growth.llm.providers.lmstudio import LMStudioClient
from skene_growth.llm.providers.ollama import OllamaClient
from skene_growth.llm.providers.openai import OpenAIClient


def create_llm_client(
    provider: str,
    api_key: SecretStr,
    model_name: str,
    fallback_model: Optional[str] = None,
) -> LLMClient:
    """
    Factory function to create an LLM client based on provider.

    Args:
        provider: Provider name (e.g., "gemini", "openai")
        api_key: API key wrapped in SecretStr for security
        model_name: Model name to use
        fallback_model: Optional fallback model for rate limiting (Anthropic only)

    Returns:
        Instance of LLMClient implementation

    Raises:
        ValueError: If provider is not supported
        NotImplementedError: If provider is known but not yet implemented

    Example:
        client = create_llm_client(
            provider="gemini",
            api_key=SecretStr("your-api-key"),
            model_name="gemini-2.5-pro"
        )
    """
    match provider.lower():
        case "gemini":
            return GeminiClient(api_key=api_key, model_name=model_name)
        case "openai":
            return OpenAIClient(api_key=api_key, model_name=model_name)
        case "anthropic":
            return AnthropicClient(api_key=api_key, model_name=model_name, fallback_model=fallback_model)
        case "lmstudio" | "lm-studio" | "lm_studio":
            return LMStudioClient(api_key=api_key, model_name=model_name)
        case "ollama":
            return OllamaClient(api_key=api_key, model_name=model_name)
        case _:
            raise ValueError(f"Unknown provider: {provider}")
