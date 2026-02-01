"""
Multimodal Capabilities Module

Provides image understanding and visual AI capabilities.
"""

from .image_encoder import ImageEncoder, ImageEncodeError
from .image_processor import ImageProcessor, ImageValidationError
from .image_memory import ImageMemory, ImageRecord
from .screenshot_assistant import (
    ProactiveScreenshotAssistant,
    ScreenshotDetector,
    ScreenshotSuggestionGenerator,
    ScreenshotCaptureGuide,
    ScreenshotSuggestion,
    ScreenshotTriggerType,
)

__all__ = [
    "ImageProcessor",
    "ImageValidationError",
    "ImageEncoder",
    "ImageEncodeError",
    "ImageMemory",
    "ImageRecord",
    "ProactiveScreenshotAssistant",
    "ScreenshotDetector",
    "ScreenshotSuggestionGenerator",
    "ScreenshotCaptureGuide",
    "ScreenshotSuggestion",
    "ScreenshotTriggerType",
]
