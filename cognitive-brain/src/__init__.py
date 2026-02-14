"""
Cognitive Brain 包初始化
"""

from .config import BrainConfig, get_config, set_config
from .models import (
    DomainStatus,
    KnowledgeQuery,
    KnowledgeResponse,
    LearningResult,
    LearningTask,
    MaterialType,
    Page,
    PageLinks,
    PageMetadata,
    PageType,
    StatusResponse,
    TaskStatus,
    generate_page_id,
)

__version__ = "0.1.0"
__all__ = [
    "BrainConfig",
    "get_config",
    "set_config",
    "Page",
    "PageType",
    "PageMetadata",
    "PageLinks",
    "generate_page_id",
    "KnowledgeQuery",
    "KnowledgeResponse",
    "LearningTask",
    "LearningResult",
    "MaterialType",
    "TaskStatus",
    "DomainStatus",
    "StatusResponse",
]
