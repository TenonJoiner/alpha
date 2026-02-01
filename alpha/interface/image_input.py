"""
Alpha - CLI Image Input Parser

Detects and parses image paths from user input in CLI.
"""

import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class ImageInput:
    """
    Parsed image input data.

    Attributes:
        paths: List of image file paths detected
        question: Associated question or context text
        command_type: Type of image command ("analyze", "image", "inline")
    """
    paths: list[str]
    question: str
    command_type: str


class ImageInputParser:
    """
    Parse image paths from user CLI input.

    Supports multiple input formats:
    - Direct file path: "analyze error.png"
    - image command: "image screenshot.png What's this error?"
    - Inline: "I'm seeing this error [error.png]. Can you help?"
    - Multiple images: "compare design_a.png design_b.png"
    """

    # Common image extensions
    IMAGE_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp',
        '.PNG', '.JPG', '.JPEG', '.GIF', '.WEBP', '.BMP'
    }

    # Patterns for detecting image references
    PATTERNS = {
        # Pattern 1: Direct command with image (analyze/image/compare)
        'command': re.compile(
            r'^(analyze|image|compare)\s+(.+?)(?:\s+"(.+?)"|$)',
            re.IGNORECASE
        ),

        # Pattern 2: Inline image references [path] or (path)
        'inline': re.compile(
            r'[\[\(]([^\]\)]+\.(?:png|jpg|jpeg|gif|webp|bmp))[\]\)]',
            re.IGNORECASE
        ),

        # Pattern 3: File path in text (any text with image extension)
        'filepath': re.compile(
            r'(?:^|\s)([^\s]+\.(?:png|jpg|jpeg|gif|webp|bmp))(?:\s|$)',
            re.IGNORECASE
        ),
    }

    def parse(self, user_input: str) -> Optional[ImageInput]:
        """
        Parse user input for image references.

        Args:
            user_input: Raw user input string

        Returns:
            ImageInput if images detected, None otherwise
        """
        # Try command pattern first (highest priority)
        if result := self._try_command_pattern(user_input):
            return result

        # Try inline pattern
        if result := self._try_inline_pattern(user_input):
            return result

        # Try filepath pattern (lowest priority)
        if result := self._try_filepath_pattern(user_input):
            return result

        return None

    def _try_command_pattern(self, text: str) -> Optional[ImageInput]:
        """Try to match command pattern (analyze/image/compare)."""
        match = self.PATTERNS['command'].match(text)
        if not match:
            return None

        command = match.group(1).lower()
        rest = match.group(2).strip()
        question = match.group(3) or ""

        # Extract all image paths from the rest of the command
        paths = self._extract_paths(rest)

        if not paths:
            return None

        # If no explicit question, use the command as context
        if not question and command != 'analyze':
            question = f"{command} these images"

        return ImageInput(
            paths=paths,
            question=question,
            command_type=command
        )

    def _try_inline_pattern(self, text: str) -> Optional[ImageInput]:
        """Try to match inline image references [path] or (path)."""
        matches = self.PATTERNS['inline'].findall(text)
        if not matches:
            return None

        # Validate paths
        paths = []
        for match in matches:
            if self._is_valid_path(match):
                paths.append(match)

        if not paths:
            return None

        # Remove image references from text to get the question
        question = text
        for match in matches:
            question = question.replace(f"[{match}]", "").replace(f"({match})", "")
        question = question.strip()

        return ImageInput(
            paths=paths,
            question=question or "Analyze this image",
            command_type="inline"
        )

    def _try_filepath_pattern(self, text: str) -> Optional[ImageInput]:
        """Try to extract file paths with image extensions."""
        matches = self.PATTERNS['filepath'].findall(text)
        if not matches:
            return None

        # Validate paths
        paths = []
        for match in matches:
            if self._is_valid_path(match):
                paths.append(match)

        if not paths:
            return None

        # Remove paths from text to get the question
        question = text
        for match in matches:
            question = question.replace(match, "").strip()

        # If question is empty, use default
        if not question:
            question = "Analyze this image"

        return ImageInput(
            paths=paths,
            question=question,
            command_type="filepath"
        )

    def _extract_paths(self, text: str) -> list[str]:
        """
        Extract valid image file paths from text.

        Args:
            text: Text to extract paths from

        Returns:
            List of valid image file paths
        """
        paths = []

        # Split by whitespace and check each token
        tokens = text.split()
        for token in tokens:
            # Remove quotes if present
            token = token.strip('"\'')

            # Check if it's a valid image path
            if self._is_valid_path(token):
                paths.append(token)

        return paths

    def _is_valid_path(self, path_str: str) -> bool:
        """
        Check if a string is a valid image file path.

        Args:
            path_str: Path string to validate

        Returns:
            True if valid image path, False otherwise
        """
        # Check file extension
        path = Path(path_str)
        if path.suffix not in self.IMAGE_EXTENSIONS:
            return False

        # Check if file exists
        if not path.exists():
            # Try resolving relative to current directory
            current_path = Path.cwd() / path
            if not current_path.exists():
                return False

        # Check if it's a file (not directory)
        resolved_path = path if path.exists() else Path.cwd() / path
        if not resolved_path.is_file():
            return False

        return True

    def get_preview_metadata(self, path: str) -> dict:
        """
        Get image metadata for preview display.

        Args:
            path: Image file path

        Returns:
            Dictionary with image metadata
        """
        file_path = Path(path)
        if not file_path.exists():
            file_path = Path.cwd() / path

        if not file_path.exists():
            return {
                "error": "File not found",
                "path": str(path)
            }

        try:
            from PIL import Image

            img = Image.open(file_path)
            return {
                "path": str(file_path.absolute()),
                "format": img.format,
                "mode": img.mode,
                "width": img.width,
                "height": img.height,
                "size_bytes": file_path.stat().st_size,
                "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2)
            }
        except Exception as e:
            return {
                "error": str(e),
                "path": str(file_path.absolute())
            }
