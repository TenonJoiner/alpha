"""
API Dependencies

Provides dependency injection functions for FastAPI routes.
"""

import time
import psutil
from typing import Optional
from alpha.core.engine import AlphaEngine
from alpha.api.chat_handler import ChatHandler

# Global state
_engine: Optional[AlphaEngine] = None
_chat_handler: Optional[ChatHandler] = None
_start_time: float = time.time()


def set_engine(engine: AlphaEngine) -> None:
    """
    Set the global engine instance.

    Args:
        engine: AlphaEngine instance
    """
    global _engine, _start_time
    _engine = engine
    _start_time = time.time()


def set_chat_handler(handler: ChatHandler) -> None:
    """
    Set the global chat handler instance.

    Args:
        handler: ChatHandler instance
    """
    global _chat_handler
    _chat_handler = handler


def get_engine() -> AlphaEngine:
    """
    Get the global engine instance.

    Returns:
        AlphaEngine instance

    Raises:
        RuntimeError: If engine not initialized
    """
    if _engine is None:
        raise RuntimeError("Alpha engine not initialized")
    return _engine


def get_chat_handler() -> ChatHandler:
    """
    Get the global chat handler instance.

    Returns:
        ChatHandler instance

    Raises:
        RuntimeError: If chat handler not initialized
    """
    if _chat_handler is None:
        raise RuntimeError("Chat handler not initialized")
    return _chat_handler


def get_uptime() -> float:
    """
    Get server uptime in seconds.

    Returns:
        Uptime in seconds
    """
    return time.time() - _start_time


def get_system_stats() -> dict:
    """
    Get system resource statistics.

    Returns:
        Dictionary with CPU and memory stats
    """
    process = psutil.Process()
    return {
        "cpu_percent": process.cpu_percent(),
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "threads": process.num_threads()
    }
