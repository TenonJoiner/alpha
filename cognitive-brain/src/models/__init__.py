"""
模型模块初始化
"""

from .page import Page, PageType, PageMetadata, PageLinks, generate_page_id
from .requests import (
    # 知识查询
    KnowledgeQuery,
    KnowledgeResult,
    KnowledgeResponse,
    # 学习
    MaterialType,
    TaskStatus,
    LearningTask,
    LearningResult,
    # 状态
    DomainStatus,
    SystemMetrics,
    StatusResponse,
    # 错误
    ErrorDetail,
    ErrorResponse,
)

__all__ = [
    # Page
    "Page",
    "PageType",
    "PageMetadata",
    "PageLinks",
    "generate_page_id",
    # Query
    "KnowledgeQuery",
    "KnowledgeResult",
    "KnowledgeResponse",
    # Learning
    "MaterialType",
    "TaskStatus",
    "LearningTask",
    "LearningResult",
    # Status
    "DomainStatus",
    "SystemMetrics",
    "StatusResponse",
    # Error
    "ErrorDetail",
    "ErrorResponse",
]
