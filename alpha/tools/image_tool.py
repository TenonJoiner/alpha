"""
Image Analysis Tool

Provides image understanding capabilities through vision-capable LLMs.
"""

import logging
from typing import List, Dict, Any, Union, Optional
from pathlib import Path

from alpha.tools.registry import Tool, ToolResult
from alpha.multimodal.image_processor import ImageProcessor
from alpha.multimodal.image_encoder import ImageEncoder
from alpha.llm.vision_provider import ClaudeVisionProvider

logger = logging.getLogger(__name__)


class ImageAnalysisTool(Tool):
    """
    Analyze images, extract text, understand visual content

    Supports multiple analysis types:
    - general: General image description
    - ocr: Text extraction (OCR)
    - chart: Chart/graph analysis
    - ui: UI/screenshot analysis
    - document: Document understanding
    """

    # Analysis prompts for different types
    ANALYSIS_PROMPTS = {
        "general": "Describe this image in detail. What do you see?",
        "ocr": "Extract all visible text from this image. Provide the text exactly as shown, maintaining formatting where possible.",
        "chart": "Analyze this chart or graph. Describe the data, trends, key insights, and any notable patterns. Include specific numbers when visible.",
        "ui": "Analyze this user interface or screenshot. Describe the layout, components, any visible errors or issues, and the overall functionality.",
        "document": "Analyze this document. Extract key information including any text, numbers, dates, and structure. Identify the document type if possible.",
    }

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize ImageAnalysisTool

        Args:
            api_key: Anthropic API key
            model: Vision-capable model to use
        """
        super().__init__(
            name="image_analysis",
            description="Analyze images, extract text, understand visual content"
        )
        self.processor = ImageProcessor()
        self.encoder = ImageEncoder()
        self.vision_provider = ClaudeVisionProvider(api_key=api_key, model=model)
        self.logger = logger

    async def execute(
        self,
        image_path: Union[str, List[str]],
        analysis_type: str = "general",
        question: Optional[str] = None,
        max_images: int = 5,
        **kwargs
    ) -> ToolResult:
        """
        Analyze image(s) and return structured results

        Args:
            image_path: Single image path or list of image paths
            analysis_type: Type of analysis (general, ocr, chart, ui, document)
            question: Optional specific question about the image(s)
            max_images: Maximum number of images to process at once
            **kwargs: Additional parameters

        Returns:
            ToolResult with analysis data
        """
        try:
            # Normalize to list
            if isinstance(image_path, str):
                image_paths = [image_path]
            else:
                image_paths = image_path

            # Validate image count
            if len(image_paths) > max_images:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Too many images: {len(image_paths)} (max {max_images})"
                )

            if len(image_paths) == 0:
                return ToolResult(
                    success=False,
                    output=None,
                    error="No images provided"
                )

            # Load and encode images
            encoded_images = []
            for path in image_paths:
                path_obj = Path(path)

                if not path_obj.exists():
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"Image not found: {path}"
                    )

                # Load, validate, and optimize image
                image = self.processor.load_image(str(path_obj))
                self.processor.validate_image(image)
                optimized = self.processor.optimize_image(image)

                # Encode to base64
                base64_data = self.encoder.encode_image(optimized)
                media_type = f"image/{image.format.lower()}"

                encoded_images.append((base64_data, media_type))

                self.logger.info(f"Loaded and encoded image: {path}")

            # Build analysis prompt
            if question:
                # User-provided question takes precedence
                prompt = question
            elif analysis_type in self.ANALYSIS_PROMPTS:
                prompt = self.ANALYSIS_PROMPTS[analysis_type]
            else:
                # Fallback to general analysis
                self.logger.warning(
                    f"Unknown analysis type: {analysis_type}, using general"
                )
                prompt = self.ANALYSIS_PROMPTS["general"]

            # Add context for multiple images
            if len(encoded_images) > 1:
                prompt = f"[Analyzing {len(encoded_images)} images] {prompt}"

            # Call vision API
            self.logger.info(
                f"Analyzing {len(encoded_images)} image(s) with type: {analysis_type}"
            )

            if len(encoded_images) == 1:
                response = await self.vision_provider.analyze_image(
                    image_base64=encoded_images[0][0],
                    prompt=prompt,
                    media_type=encoded_images[0][1],
                )
            else:
                response = await self.vision_provider.analyze_images(
                    images=encoded_images, prompt=prompt
                )

            # Parse response based on analysis type
            structured_data = self._parse_response(
                response.content, analysis_type, len(encoded_images)
            )

            # Build result data
            result_data = {
                "description": response.content,
                "analysis_type": analysis_type,
                "images_analyzed": len(encoded_images),
                "confidence": 0.9,  # High confidence for vision models
                "cost_usd": response.cost_usd,
                "model_used": response.model,
                "tokens_used": response.tokens_used,
                "structured_data": structured_data,
            }

            # Add extracted_text for OCR type
            if analysis_type == "ocr":
                result_data["extracted_text"] = response.content

            self.logger.info(
                f"Analysis complete: {len(encoded_images)} images, "
                f"cost: ${response.cost_usd:.4f}"
            )

            return ToolResult(
                success=True,
                output=result_data,
                metadata={
                    "analysis_type": analysis_type,
                    "images_count": len(encoded_images),
                    "cost_usd": response.cost_usd,
                }
            )

        except Exception as e:
            self.logger.error(f"Image analysis failed: {e}")
            return ToolResult(
                success=False,
                output=None,
                error=f"Image analysis failed: {str(e)}"
            )

    def _parse_response(
        self, content: str, analysis_type: str, num_images: int
    ) -> Dict[str, Any]:
        """
        Parse vision response into structured data

        Args:
            content: Raw vision model response
            analysis_type: Type of analysis performed
            num_images: Number of images analyzed

        Returns:
            Structured data dictionary based on analysis type
        """
        # Basic structured data
        data = {
            "raw_response": content,
            "num_images": num_images,
        }

        # Type-specific parsing (basic implementation)
        # Could be enhanced with regex/NLP for better extraction

        if analysis_type == "ocr":
            # For OCR, the entire response is text
            data["extracted_text"] = content
            data["word_count"] = len(content.split())

        elif analysis_type == "chart":
            # Try to extract numeric insights
            # (Basic implementation - could use regex for numbers)
            data["contains_numbers"] = any(char.isdigit() for char in content)

        elif analysis_type == "ui":
            # Check for common UI keywords
            ui_keywords = ["button", "menu", "icon", "error", "dialog", "form"]
            data["ui_elements_mentioned"] = [
                kw for kw in ui_keywords if kw in content.lower()
            ]

        elif analysis_type == "document":
            # Document metadata hints
            doc_types = ["invoice", "receipt", "contract", "form", "letter"]
            detected_types = [dt for dt in doc_types if dt in content.lower()]
            if detected_types:
                data["document_type"] = detected_types[0]

        return data

    def validate_input(self, **kwargs) -> bool:
        """
        Validate tool input parameters

        Args:
            **kwargs: Tool parameters

        Returns:
            True if valid

        Raises:
            ToolExecutionError: If validation fails
        """
        if "image_path" not in kwargs:
            raise ToolExecutionError("Missing required parameter: image_path")

        analysis_type = kwargs.get("analysis_type", "general")
        valid_types = list(self.ANALYSIS_PROMPTS.keys())

        if analysis_type not in valid_types:
            self.logger.warning(
                f"Unknown analysis type '{analysis_type}', will use 'general'"
            )
            # Don't fail, just warn - we'll use general analysis

        return True

    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool parameter schema

        Returns:
            JSON schema for tool parameters
        """
        return {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": ["string", "array"],
                    "description": "Path to image file or list of image paths",
                    "items": {"type": "string"},
                },
                "analysis_type": {
                    "type": "string",
                    "enum": list(self.ANALYSIS_PROMPTS.keys()),
                    "default": "general",
                    "description": "Type of analysis to perform",
                },
                "question": {
                    "type": "string",
                    "description": "Optional specific question about the image(s)",
                },
                "max_images": {
                    "type": "integer",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Maximum number of images to process",
                },
            },
            "required": ["image_path"],
        }
