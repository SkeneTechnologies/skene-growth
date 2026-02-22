"""Tests for Anthropic LLM client."""

import httpx
import pytest
from anthropic import RateLimitError
from pydantic import SecretStr
from unittest.mock import AsyncMock, MagicMock, patch


def _make_rate_limit_error() -> RateLimitError:
    """Create a properly-constructed RateLimitError for anthropic >= 0.40."""
    response = httpx.Response(
        status_code=429,
        request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
    )
    return RateLimitError("Rate limited", response=response, body=None)


@pytest.fixture
def anthropic_client():
    """Create a mock Anthropic client."""
    with patch("skene_growth.llm.providers.anthropic.AsyncAnthropic") as mock_anthropic:
        from skene_growth.llm.providers.anthropic import AnthropicClient

        client = AnthropicClient(
            api_key=SecretStr("test-api-key"),
            model_name="claude-sonnet-4-20250514"
        )
        client.client = mock_anthropic.return_value
        return client


class TestAnthropicClientInitialization:
    """Test Anthropic client initialization."""

    def test_initialization_with_default_fallback(self):
        """Test client initializes with default fallback model."""
        with patch("skene_growth.llm.providers.anthropic.AsyncAnthropic"):
            from skene_growth.llm.providers.anthropic import AnthropicClient, DEFAULT_FALLBACK_MODEL

            client = AnthropicClient(
                api_key=SecretStr("test-key"),
                model_name="claude-sonnet-4-20250514"
            )

            assert client.model_name == "claude-sonnet-4-20250514"
            assert client.fallback_model == DEFAULT_FALLBACK_MODEL

    def test_initialization_with_custom_fallback(self):
        """Test client initializes with custom fallback model."""
        with patch("skene_growth.llm.providers.anthropic.AsyncAnthropic"):
            from skene_growth.llm.providers.anthropic import AnthropicClient

            client = AnthropicClient(
                api_key=SecretStr("test-key"),
                model_name="claude-sonnet-4-20250514",
                fallback_model="claude-haiku-20250203"
            )

            assert client.model_name == "claude-sonnet-4-20250514"
            assert client.fallback_model == "claude-haiku-20250203"

    def test_initialization_without_anthropic_raises_import_error(self):
        """Test that missing anthropic package raises helpful error."""
        with patch("skene_growth.llm.providers.anthropic.AsyncAnthropic", None):
            from skene_growth.llm.providers.anthropic import AnthropicClient

            with pytest.raises(ImportError, match="anthropic is required"):
                AnthropicClient(
                    api_key=SecretStr("test-key"),
                    model_name="claude-sonnet-4-20250514"
                )


class TestAnthropicClientGenerateContent:
    """Test content generation."""

    @pytest.mark.asyncio
    async def test_generate_content_success(self, anthropic_client):
        """Test successful content generation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Generated response")]
        anthropic_client.client.messages.create = AsyncMock(return_value=mock_response)

        result = await anthropic_client.generate_content("Test prompt")

        assert result == "Generated response"
        anthropic_client.client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_content_strips_whitespace(self, anthropic_client):
        """Test that generated content is stripped of whitespace."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="  Response with spaces  \n")]
        anthropic_client.client.messages.create = AsyncMock(return_value=mock_response)

        result = await anthropic_client.generate_content("Test")

        assert result == "Response with spaces"

    @pytest.mark.asyncio
    async def test_generate_content_with_rate_limit_fallback(self, anthropic_client):
        """Test fallback on rate limit error."""
        # First call fails with rate limit
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Fallback response")]

        anthropic_client.client.messages.create = AsyncMock(
            side_effect=[
                _make_rate_limit_error(),
                mock_response
            ]
        )

        result = await anthropic_client.generate_content("Test")

        assert result == "Fallback response"
        assert anthropic_client.client.messages.create.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_content_fallback_failure_raises_error(self, anthropic_client):
        """Test that fallback failure raises RuntimeError."""
        anthropic_client.client.messages.create = AsyncMock(
            side_effect=[
                _make_rate_limit_error(),
                Exception("Fallback failed")
            ]
        )

        with pytest.raises(RuntimeError, match="Error calling Anthropic \\(fallback model"):
            await anthropic_client.generate_content("Test")

    @pytest.mark.asyncio
    async def test_generate_content_generic_error_raises_runtime_error(self, anthropic_client):
        """Test that generic errors raise RuntimeError."""
        anthropic_client.client.messages.create = AsyncMock(
            side_effect=Exception("API error")
        )

        with pytest.raises(RuntimeError, match="Error calling Anthropic"):
            await anthropic_client.generate_content("Test")


class TestAnthropicClientStreaming:
    """Test streaming content generation."""

    @pytest.mark.asyncio
    async def test_generate_content_stream_success(self, anthropic_client):
        """Test successful streaming generation."""
        mock_stream = AsyncMock()
        mock_stream.__aenter__.return_value = mock_stream
        mock_stream.__aexit__.return_value = None

        async def mock_text_stream():
            yield "chunk1"
            yield "chunk2"
            yield "chunk3"

        mock_stream.text_stream = mock_text_stream()
        anthropic_client.client.messages.stream = MagicMock(return_value=mock_stream)

        chunks = []
        async for chunk in anthropic_client.generate_content_stream("Test"):
            chunks.append(chunk)

        assert chunks == ["chunk1", "chunk2", "chunk3"]

    @pytest.mark.asyncio
    async def test_generate_content_stream_with_rate_limit_fallback(self, anthropic_client):
        """Test streaming with rate limit fallback."""
        from anthropic import RateLimitError

        # First stream fails, second succeeds
        mock_stream_fallback = AsyncMock()
        mock_stream_fallback.__aenter__.return_value = mock_stream_fallback
        mock_stream_fallback.__aexit__.return_value = None

        async def mock_text_stream():
            yield "fallback1"
            yield "fallback2"

        mock_stream_fallback.text_stream = mock_text_stream()

        call_count = 0
        def stream_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise _make_rate_limit_error()
            return mock_stream_fallback

        anthropic_client.client.messages.stream = MagicMock(side_effect=stream_side_effect)

        chunks = []
        async for chunk in anthropic_client.generate_content_stream("Test"):
            chunks.append(chunk)

        assert chunks == ["fallback1", "fallback2"]


class TestAnthropicClientGetters:
    """Test getter methods."""

    def test_get_model_name(self, anthropic_client):
        """Test getting model name."""
        assert anthropic_client.get_model_name() == "claude-sonnet-4-20250514"

    def test_get_provider_name(self, anthropic_client):
        """Test getting provider name."""
        assert anthropic_client.get_provider_name() == "anthropic"
