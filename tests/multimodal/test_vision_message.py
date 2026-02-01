"""
Tests for VisionMessage and related types
"""

import pytest
from alpha.llm.vision_message import (
    VisionMessage,
    TextContent,
    ImageContent,
    ImageSource,
)


class TestTextContent:
    """Test TextContent class"""

    def test_create_text_content(self):
        """Test creating TextContent"""
        text = TextContent(text="Hello world")

        assert text.type == "text"
        assert text.text == "Hello world"

    def test_default_text(self):
        """Test default empty text"""
        text = TextContent()

        assert text.type == "text"
        assert text.text == ""


class TestImageSource:
    """Test ImageSource class"""

    def test_create_base64_source(self):
        """Test creating base64 ImageSource"""
        source = ImageSource(
            type="base64", media_type="image/png", data="iVBORw0KGgoAAAANS"
        )

        assert source.type == "base64"
        assert source.media_type == "image/png"
        assert source.data.startswith("iVBORw0")

    def test_create_url_source(self):
        """Test creating URL ImageSource"""
        source = ImageSource(
            type="url",
            media_type="image/jpeg",
            data="https://example.com/image.jpg",
        )

        assert source.type == "url"
        assert source.media_type == "image/jpeg"
        assert source.data.startswith("https://")


class TestImageContent:
    """Test ImageContent class"""

    def test_create_image_content(self):
        """Test creating ImageContent"""
        source = ImageSource(type="base64", media_type="image/png", data="abc123")
        image = ImageContent(source=source)

        assert image.type == "image"
        assert image.source.type == "base64"
        assert image.source.data == "abc123"


class TestVisionMessage:
    """Test VisionMessage class"""

    def test_create_text_only_message(self):
        """Test creating text-only message"""
        msg = VisionMessage(role="user", content="Hello")

        assert msg.role == "user"
        assert msg.content == "Hello"
        assert not msg.has_images()

    def test_create_multimodal_message(self):
        """Test creating message with text and image"""
        content = [
            TextContent(text="What is this?"),
            ImageContent(
                source=ImageSource(
                    type="base64", media_type="image/png", data="base64data"
                )
            ),
        ]
        msg = VisionMessage(role="user", content=content)

        assert msg.role == "user"
        assert len(msg.content) == 2
        assert msg.has_images()

    def test_to_dict_text_only(self):
        """Test to_dict() for text-only message"""
        msg = VisionMessage(role="user", content="Hello")
        result = msg.to_dict()

        assert result == {"role": "user", "content": "Hello"}

    def test_to_dict_multimodal(self):
        """Test to_dict() for multimodal message"""
        content = [
            TextContent(text="Analyze this"),
            ImageContent(
                source=ImageSource(
                    type="base64", media_type="image/png", data="imagedata123"
                )
            ),
        ]
        msg = VisionMessage(role="user", content=content)
        result = msg.to_dict()

        assert result["role"] == "user"
        assert len(result["content"]) == 2
        assert result["content"][0] == {"type": "text", "text": "Analyze this"}
        assert result["content"][1]["type"] == "image"
        assert result["content"][1]["source"]["data"] == "imagedata123"

    def test_from_text(self):
        """Test from_text() factory method"""
        msg = VisionMessage.from_text("assistant", "Response text")

        assert msg.role == "assistant"
        assert msg.content == "Response text"
        assert not msg.has_images()

    def test_from_text_and_image(self):
        """Test from_text_and_image() factory method"""
        msg = VisionMessage.from_text_and_image(
            role="user",
            text="What's in this image?",
            image_base64="base64string",
            media_type="image/jpeg",
        )

        assert msg.role == "user"
        assert len(msg.content) == 2
        assert msg.has_images()
        assert isinstance(msg.content[0], TextContent)
        assert isinstance(msg.content[1], ImageContent)
        assert msg.content[1].source.media_type == "image/jpeg"

    def test_from_text_and_images(self):
        """Test from_text_and_images() with multiple images"""
        images = [
            ("base64_1", "image/png"),
            ("base64_2", "image/jpeg"),
            ("base64_3", "image/gif"),
        ]
        msg = VisionMessage.from_text_and_images(
            role="user", text="Compare these images", images=images
        )

        assert msg.role == "user"
        assert len(msg.content) == 4  # 1 text + 3 images
        assert msg.has_images()

        # Check all images
        image_blocks = [
            block for block in msg.content if isinstance(block, ImageContent)
        ]
        assert len(image_blocks) == 3
        assert image_blocks[0].source.data == "base64_1"
        assert image_blocks[1].source.data == "base64_2"
        assert image_blocks[2].source.data == "base64_3"

    def test_has_images_text_only(self):
        """Test has_images() returns False for text-only"""
        msg = VisionMessage(role="user", content="No images here")

        assert not msg.has_images()

    def test_has_images_with_image(self):
        """Test has_images() returns True when images present"""
        content = [
            TextContent(text="Text"),
            ImageContent(
                source=ImageSource(
                    type="base64", media_type="image/png", data="data"
                )
            ),
        ]
        msg = VisionMessage(role="user", content=content)

        assert msg.has_images()

    def test_get_text_from_string(self):
        """Test get_text() from string content"""
        msg = VisionMessage(role="user", content="Simple text")

        assert msg.get_text() == "Simple text"

    def test_get_text_from_blocks(self):
        """Test get_text() extracts text from blocks"""
        content = [
            TextContent(text="First part"),
            ImageContent(
                source=ImageSource(
                    type="base64", media_type="image/png", data="data"
                )
            ),
            TextContent(text="Second part"),
        ]
        msg = VisionMessage(role="user", content=content)

        assert msg.get_text() == "First part Second part"

    def test_get_text_no_text_blocks(self):
        """Test get_text() when only images"""
        content = [
            ImageContent(
                source=ImageSource(
                    type="base64", media_type="image/png", data="data"
                )
            )
        ]
        msg = VisionMessage(role="user", content=content)

        assert msg.get_text() == ""
