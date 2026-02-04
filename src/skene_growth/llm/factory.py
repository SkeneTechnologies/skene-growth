"""
LLM client factory.
"""

from typing import Optional

from pydantic import SecretStr

from skene_growth.llm.base import LLMClient


def create_llm_client(
    provider: str,
    api_key: SecretStr,
    model_name: str,
    base_url: Optional[str] = None,
) -> LLMClient:
    """
    Factory function to create an LLM client based on provider.

    Args:
        provider: Provider name (e.g., "gemini", "openai", "generic")
        api_key: API key wrapped in SecretStr for security
        model_name: Model name to use
        base_url: Optional base URL for the API endpoint (required for "generic" provider)

    Returns:
        Instance of LLMClient implementation

    Raises:
        ValueError: If provider is not supported or required parameters are missing
        NotImplementedError: If provider is known but not yet implemented

    Example:
        # Using a known provider
        client = create_llm_client(
            provider="gemini",
            api_key=SecretStr("your-api-key"),
            model_name="gemini-2.5-pro"
        )

        # Using a generic OpenAI-compatible endpoint
        client = create_llm_client(
            provider="generic",
            api_key=SecretStr("your-api-key"),
            model_name="your-model",
            base_url="https://your-service.com/v1"
        )
    """
    match provider.lower():
        case "gemini":
            from skene_growth.llm.providers.gemini import GoogleGeminiClient

            return GoogleGeminiClient(api_key=api_key, model_name=model_name)
        case "openai":
            from skene_growth.llm.providers.openai import OpenAIClient

            return OpenAIClient(api_key=api_key, model_name=model_name)
        case "anthropic" | "claude":
            from skene_growth.llm.providers.anthropic import AnthropicClient

            return AnthropicClient(api_key=api_key, model_name=model_name)
        case "lmstudio" | "lm-studio" | "lm_studio":
            from skene_growth.llm.providers.lmstudio import LMStudioClient

            return LMStudioClient(api_key=api_key, model_name=model_name, base_url=base_url)
        case "ollama":
            from skene_growth.llm.providers.ollama import OllamaClient

            return OllamaClient(api_key=api_key, model_name=model_name, base_url=base_url)
        case "generic" | "openai-compatible" | "openai_compatible":
            from skene_growth.llm.providers.generic import GenericClient

            if not base_url:
                raise ValueError("base_url is required for the generic provider")
            return GenericClient(api_key=api_key, model_name=model_name, base_url=base_url)
        case "local" | "llama-cpp" | "gguf":
            from skene_growth.llm.providers.local import LocalClient

            return LocalClient(api_key=api_key, model_name=model_name)
        case _:
            raise ValueError(f"Unknown provider: {provider}")
