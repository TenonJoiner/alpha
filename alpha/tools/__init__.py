"""
Tools module

Provides the tool system for Alpha, including built-in tools and the CodeExecutionTool
for generating and executing custom code.
"""

from .registry import (
    Tool,
    ToolResult,
    ToolRegistry,
    ShellTool,
    FileTool,
    SearchTool,
    HTTPTool,
    DateTimeTool,
    CalculatorTool,
    create_default_registry
)

from .code_tool import CodeExecutionTool
from .image_tool import ImageAnalysisTool

__all__ = [
    # Base classes
    "Tool",
    "ToolResult",
    "ToolRegistry",
    # Built-in tools
    "ShellTool",
    "FileTool",
    "SearchTool",
    "HTTPTool",
    "DateTimeTool",
    "CalculatorTool",
    # Code execution tool (Phase 4.1)
    "CodeExecutionTool",
    # Image analysis tool (Phase 9.1 - Multimodal)
    "ImageAnalysisTool",
    # Registry helper
    "create_default_registry",
]
