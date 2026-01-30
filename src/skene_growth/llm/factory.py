"""
LLM client factory.
"""

from pydantic import SecretStr

from skene_growth.llm.base import LLMClient


def create_llm_client(
    provider: str,
    api_key: SecretStr,
    model_name: str,
) -> LLMClient:
    """
    Factory function to create an LLM client based on provider.

    Args:
        provider: Provider name (e.g., "gemini", "openai")
        api_key: API key wrapped in SecretStr for security
        model_name: Model name to use

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

            return LMStudioClient(api_key=api_key, model_name=model_name)
        case "ollama":
            from skene_growth.llm.providers.ollama import OllamaClient

            return OllamaClient(api_key=api_key, model_name=model_name)
        case _:
            raise ValueError(f"Unknown provider: {provider}")
