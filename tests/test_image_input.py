"""
Tests for ImageInputParser

Test image input detection and parsing from CLI.
"""

import pytest
from pathlib import Path
from alpha.interface.image_input import ImageInputParser, ImageInput


@pytest.fixture
def parser():
    """Create ImageInputParser instance"""
    return ImageInputParser()


@pytest.fixture
def test_image_file(tmp_path):
    """Create a test image file"""
    from PIL import Image

    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    image_path = tmp_path / "test.png"
    img.save(image_path)
    return str(image_path)


class TestImageInputParser:
    """Test ImageInputParser"""

    def test_command_pattern_analyze(self, parser, test_image_file):
        """Test 'analyze' command pattern"""
        result = parser.parse(f"analyze {test_image_file}")

        assert result is not None
        assert result.command_type == "analyze"
        assert test_image_file in result.paths
        assert result.question == ""  # No explicit question

    def test_command_pattern_image_with_question(self, parser, test_image_file):
        """Test 'image' command with question"""
        result = parser.parse(f'image {test_image_file} "What is this?"')

        assert result is not None
        assert result.command_type == "image"
        assert test_image_file in result.paths
        assert result.question == "What is this?"

    def test_command_pattern_compare(self, parser, test_image_file, tmp_path):
        """Test 'compare' command with multiple images"""
        # Create second image
        from PIL import Image
        img2 = Image.new('RGB', (100, 100), color='blue')
        image_path2 = tmp_path / "test2.png"
        img2.save(image_path2)

        result = parser.parse(f"compare {test_image_file} {str(image_path2)}")

        assert result is not None
        assert result.command_type == "compare"
        assert len(result.paths) == 2
        assert test_image_file in result.paths
        assert str(image_path2) in result.paths

    def test_inline_pattern_brackets(self, parser, test_image_file):
        """Test inline pattern with [brackets]"""
        result = parser.parse(f"I see this error [{test_image_file}]. Can you help?")

        assert result is not None
        assert result.command_type == "inline"
        assert test_image_file in result.paths
        assert "Can you help?" in result.question

    def test_filepath_pattern(self, parser, test_image_file):
        """Test filepath pattern detection"""
        result = parser.parse(f"{test_image_file} shows an error")

        assert result is not None
        assert result.command_type == "filepath"
        assert test_image_file in result.paths
        assert "shows an error" in result.question

    def test_no_image_detected(self, parser):
        """Test no image in text"""
        result = parser.parse("Hello, how are you?")

        assert result is None

    def test_invalid_file_path(self, parser):
        """Test non-existent image path"""
        result = parser.parse("analyze /nonexistent/image.png")

        assert result is None  # Invalid path should not be detected

    def test_non_image_extension(self, parser, tmp_path):
        """Test file with non-image extension"""
        text_file = tmp_path / "document.txt"
        text_file.write_text("Hello")

        result = parser.parse(f"analyze {str(text_file)}")

        assert result is None  # .txt is not an image extension

    def test_get_preview_metadata(self, parser, test_image_file):
        """Test get_preview_metadata"""
        metadata = parser.get_preview_metadata(test_image_file)

        assert "error" not in metadata
        assert metadata["format"] == "PNG"
        assert metadata["width"] == 100
        assert metadata["height"] == 100
        assert metadata["size_bytes"] > 0

    def test_get_preview_metadata_missing_file(self, parser):
        """Test get_preview_metadata with missing file"""
        metadata = parser.get_preview_metadata("/nonexistent/file.png")

        assert "error" in metadata

    def test_multiple_inline_images(self, parser, test_image_file, tmp_path):
        """Test multiple inline image references"""
        from PIL import Image
        img2 = Image.new('RGB', (100, 100), color='green')
        image_path2 = tmp_path / "test2.png"
        img2.save(image_path2)

        result = parser.parse(
            f"Compare [{test_image_file}] and [{str(image_path2)}]"
        )

        assert result is not None
        assert result.command_type == "inline"
        assert len(result.paths) == 2

    def test_extract_paths(self, parser, test_image_file):
        """Test _extract_paths helper"""
        paths = parser._extract_paths(f"{test_image_file} other.jpg")

        assert test_image_file in paths

    def test_is_valid_path_valid(self, parser, test_image_file):
        """Test _is_valid_path with valid path"""
        assert parser._is_valid_path(test_image_file) is True

    def test_is_valid_path_invalid(self, parser):
        """Test _is_valid_path with invalid path"""
        assert parser._is_valid_path("/nonexistent/image.png") is False

    def test_is_valid_path_wrong_extension(self, parser, tmp_path):
        """Test _is_valid_path with wrong extension"""
        text_file = tmp_path / "document.txt"
        text_file.write_text("content")

        assert parser._is_valid_path(str(text_file)) is False

    def test_question_extraction_analyze(self, parser, test_image_file):
        """Test question extraction for analyze command"""
        result = parser.parse(f"analyze {test_image_file}")

        # analyze with no explicit question should have empty question
        assert result.question == ""

    def test_question_extraction_with_text(self, parser, test_image_file):
        """Test question extraction from surrounding text"""
        result = parser.parse(f"{test_image_file} What does this show?")

        assert "What does this show?" in result.question

    def test_case_insensitive_command(self, parser, test_image_file):
        """Test case-insensitive command matching"""
        result = parser.parse(f"ANALYZE {test_image_file}")

        assert result is not None
        assert result.command_type == "analyze"

    def test_case_insensitive_extension(self, parser, tmp_path):
        """Test case-insensitive extension matching"""
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        # Use uppercase extension
        image_path = tmp_path / "test.PNG"
        img.save(image_path)

        result = parser.parse(f"analyze {str(image_path)}")

        assert result is not None
        assert str(image_path) in result.paths
