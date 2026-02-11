"""Tests for LLM factory."""

import pytest
from pydantic import SecretStr
from unittest.mock import patch, MagicMock


class TestLLMFactory:
    """Test LLM client factory."""

    @patch("skene_growth.llm.factory.GeminiClient")
    def test_create_gemini_client(self, mock_gemini):
        """Test creating Gemini client."""
        from skene_growth.llm.factory import create_llm_client

        client = create_llm_client(
            provider="gemini",
            api_key=SecretStr("test-key"),
            model_name="gemini-2.5-pro"
        )

        mock_gemini.assert_called_once_with(
            api_key=SecretStr("test-key"),
            model_name="gemini-2.5-pro"
        )

    @patch("skene_growth.llm.factory.AnthropicClient")
    def test_create_anthropic_client(self, mock_anthropic):
        """Test creating Anthropic client."""
        from skene_growth.llm.factory import create_llm_client

        client = create_llm_client(
            provider="anthropic",
            api_key=SecretStr("test-key"),
            model_name="claude-sonnet-4-20250514"
        )

        mock_anthropic.assert_called_once()

    @patch("skene_growth.llm.factory.OpenAIClient")
    def test_create_openai_client(self, mock_openai):
        """Test creating OpenAI client."""
        from skene_growth.llm.factory import create_llm_client

        client = create_llm_client(
            provider="openai",
            api_key=SecretStr("test-key"),
            model_name="gpt-4"
        )

        mock_openai.assert_called_once()

    @patch("skene_growth.llm.factory.OllamaClient")
    def test_create_ollama_client(self, mock_ollama):
        """Test creating Ollama client."""
        from skene_growth.llm.factory import create_llm_client

        client = create_llm_client(
            provider="ollama",
            api_key=SecretStr("test-key"),
            model_name="llama2"
        )

        mock_ollama.assert_called_once()

    @patch("skene_growth.llm.factory.LMStudioClient")
    def test_create_lmstudio_client(self, mock_lmstudio):
        """Test creating LMStudio client."""
        from skene_growth.llm.factory import create_llm_client

        client = create_llm_client(
            provider="lmstudio",
            api_key=SecretStr("test-key"),
            model_name="local-model"
        )

        mock_lmstudio.assert_called_once()

    def test_unknown_provider_raises_error(self):
        """Test that unknown provider raises ValueError."""
        from skene_growth.llm.factory import create_llm_client

        with pytest.raises(ValueError, match="Unknown provider"):
            create_llm_client(
                provider="unknown",
                api_key=SecretStr("test-key"),
                model_name="test-model"
            )

    @patch("skene_growth.llm.factory.AnthropicClient")
    def test_create_with_fallback_model(self, mock_anthropic):
        """Test creating client with fallback model."""
        from skene_growth.llm.factory import create_llm_client

        client = create_llm_client(
            provider="anthropic",
            api_key=SecretStr("test-key"),
            model_name="claude-sonnet-4-20250514",
            fallback_model="claude-haiku-20250203"
        )

        # Should pass fallback_model to constructor
        call_kwargs = mock_anthropic.call_args[1]
        assert call_kwargs.get("fallback_model") == "claude-haiku-20250203"


class TestLLMBase:
    """Test LLM base class."""

    def test_llm_client_is_abstract(self):
        """Test that LLMClient cannot be instantiated."""
        from skene_growth.llm.base import LLMClient

        with pytest.raises(TypeError):
            LLMClient()

    def test_generate_content_is_abstract_method(self):
        """Test that generate_content is an abstract method."""
        from skene_growth.llm.base import LLMClient
        import inspect

        assert hasattr(LLMClient, "generate_content")
        assert inspect.iscoroutinefunction(LLMClient.generate_content)

    def test_generate_content_stream_is_abstract_method(self):
        """Test that generate_content_stream is an abstract method."""
        from skene_growth.llm.base import LLMClient
        import inspect

        assert hasattr(LLMClient, "generate_content_stream")
        assert inspect.iscoroutinefunction(LLMClient.generate_content_stream)

    def test_get_model_name_is_abstract_method(self):
        """Test that get_model_name is an abstract method."""
        from skene_growth.llm.base import LLMClient

        assert hasattr(LLMClient, "get_model_name")

    def test_get_provider_name_is_abstract_method(self):
        """Test that get_provider_name is an abstract method."""
        from skene_growth.llm.base import LLMClient

        assert hasattr(LLMClient, "get_provider_name")
