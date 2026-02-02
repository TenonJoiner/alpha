"""
Tests for ClaudeVisionProvider
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from alpha.llm.vision_provider import ClaudeVisionProvider, VisionResponse
from alpha.llm.vision_message import VisionMessage


@pytest.fixture
def api_key():
    """Mock API key"""
    return "test-api-key-123"


@pytest.fixture
def provider(api_key):
    """Create ClaudeVisionProvider instance"""
    return ClaudeVisionProvider(api_key=api_key)


@pytest.fixture
def mock_api_response():
    """Mock Claude API response"""
    return {
        "content": [{"text": "This is a test image showing a cat."}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 150, "output_tokens": 25},
    }


class TestClaudeVisionProvider:
    """Test ClaudeVisionProvider class"""

    def test_init(self, api_key):
        """Test provider initialization"""
        provider = ClaudeVisionProvider(api_key=api_key)

        assert provider.api_key == api_key
        assert provider.model == "claude-3-5-sonnet-20241022"
        assert provider.client is not None

    def test_init_custom_model(self, api_key):
        """Test initialization with custom model"""
        provider = ClaudeVisionProvider(
            api_key=api_key, model="claude-3-opus-20240229"
        )

        assert provider.model == "claude-3-opus-20240229"

    def test_supports_vision(self, provider):
        """Test supports_vision() returns True for vision models"""
        assert provider.supports_vision()

    def test_supports_vision_non_vision_model(self, api_key):
        """Test supports_vision() returns False for non-vision models"""
        provider = ClaudeVisionProvider(api_key=api_key, model="claude-2.1")

        assert not provider.supports_vision()

    def test_calculate_cost(self, provider):
        """Test cost calculation"""
        cost = provider._calculate_cost(
            input_tokens=1_000_000,
            output_tokens=500_000,
            model="claude-3-5-sonnet-20241022",
        )

        # $3 per 1M input + $15 per 1M output * 0.5
        expected = 3.0 + (15.0 * 0.5)
        assert cost == expected

    def test_calculate_cost_unknown_model(self, provider):
        """Test cost calculation for unknown model returns 0"""
        cost = provider._calculate_cost(
            input_tokens=1_000_000, output_tokens=500_000, model="unknown-model"
        )

        assert cost == 0.0

    def test_convert_messages(self, provider):
        """Test message conversion to API format"""
        messages = [
            VisionMessage.from_text("user", "Hello"),
            VisionMessage.from_text_and_image(
                "user", "What is this?", "base64data", "image/png"
            ),
        ]

        api_messages = provider._convert_messages(messages)

        assert len(api_messages) == 2
        assert api_messages[0]["role"] == "user"
        assert api_messages[0]["content"] == "Hello"
        assert api_messages[1]["role"] == "user"
        assert isinstance(api_messages[1]["content"], list)

    @pytest.mark.asyncio
    async def test_complete(self, provider, mock_api_response):
        """Test complete() method"""
        # Mock client.create_message
        provider.client.create_message = AsyncMock(return_value=mock_api_response)

        messages = [VisionMessage.from_text("user", "Hello")]
        response = await provider.complete(messages)

        assert isinstance(response, VisionResponse)
        assert response.content == "This is a test image showing a cat."
        assert response.model == "claude-3-5-sonnet-20241022"
        assert response.input_tokens == 150
        assert response.output_tokens == 25
        assert response.tokens_used == 175

    @pytest.mark.asyncio
    async def test_complete_with_system_prompt(self, provider, mock_api_response):
        """Test complete() with system prompt"""
        provider.client.create_message = AsyncMock(return_value=mock_api_response)

        messages = [VisionMessage.from_text("user", "Analyze")]
        response = await provider.complete(messages, system="You are an expert analyst")

        # Verify system prompt was passed
        provider.client.create_message.assert_called_once()
        call_kwargs = provider.client.create_message.call_args[1]
        assert call_kwargs["system"] == "You are an expert analyst"

    @pytest.mark.asyncio
    async def test_analyze_image(self, provider, mock_api_response):
        """Test analyze_image() convenience method"""
        provider.client.create_message = AsyncMock(return_value=mock_api_response)

        response = await provider.analyze_image(
            image_base64="base64data",
            prompt="What do you see?",
            media_type="image/jpeg",
        )

        assert isinstance(response, VisionResponse)
        assert response.content == "This is a test image showing a cat."

        # Verify message was constructed correctly
        provider.client.create_message.assert_called_once()
        call_kwargs = provider.client.create_message.call_args[1]
        messages = call_kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_analyze_images(self, provider, mock_api_response):
        """Test analyze_images() with multiple images"""
        provider.client.create_message = AsyncMock(return_value=mock_api_response)

        images = [
            ("base64_1", "image/png"),
            ("base64_2", "image/jpeg"),
        ]
        response = await provider.analyze_images(
            images=images, prompt="Compare these images"
        )

        assert isinstance(response, VisionResponse)

        # Verify multiple images were included
        provider.client.create_message.assert_called_once()
        call_kwargs = provider.client.create_message.call_args[1]
        messages = call_kwargs["messages"]
        assert len(messages) == 1

        # Message should have 1 text + 2 images = 3 content blocks
        content = messages[0]["content"]
        assert len(content) == 3
        assert content[0]["type"] == "text"
        assert content[1]["type"] == "image"
        assert content[2]["type"] == "image"

    @pytest.mark.asyncio
    async def test_cost_tracking(self, provider, mock_api_response):
        """Test that cost is tracked correctly"""
        provider.client.create_message = AsyncMock(return_value=mock_api_response)

        messages = [VisionMessage.from_text("user", "Test")]
        response = await provider.complete(messages)

        # 150 input tokens * $3/1M = $0.00045
        # 25 output tokens * $15/1M = $0.000375
        # Total = $0.000825
        expected_cost = (150 / 1_000_000) * 3.0 + (25 / 1_000_000) * 15.0

        assert response.cost_usd == pytest.approx(expected_cost, abs=1e-6)

    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_stream_complete(self, provider, mock_api_response):
        """Test stream_complete() yields response"""
        provider.client.create_message = AsyncMock(return_value=mock_api_response)

        messages = [VisionMessage.from_text("user", "Stream test")]
        chunks = []

        async for chunk in provider.stream_complete(messages):
            chunks.append(chunk)

        # For now, streaming yields complete response
        assert len(chunks) == 1
        assert chunks[0] == "This is a test image showing a cat."

    @pytest.mark.asyncio
    async def test_vision_warning_non_vision_model(self, api_key, mock_api_response):
        """Test warning logged for non-vision models"""
        provider = ClaudeVisionProvider(api_key=api_key, model="claude-2.1")
        provider.client.create_message = AsyncMock(return_value=mock_api_response)

        with patch.object(provider.logger, "warning") as mock_warning:
            messages = [VisionMessage.from_text("user", "Test")]
            await provider.complete(messages)

            # Should log warning about non-vision model
            mock_warning.assert_called()
