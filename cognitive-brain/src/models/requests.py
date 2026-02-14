"""
请求/响应数据模型

定义 MCP Tools 的输入输出数据结构
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# 知识查询相关模型
# =============================================================================

class KnowledgeQuery(BaseModel):
    """知识查询请求"""
    
    query: str = Field(
        ..., 
        min_length=1, 
        max_length=2000,
        description="用户查询内容"
    )
    domain: str = Field(
        ...,
        min_length=1,
        description="领域标识，如 'storage-architect'"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="可选上下文信息，如用户级别、历史对话等"
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="返回结果最大数量"
    )


class KnowledgeResult(BaseModel):
    """单个知识查询结果"""
    
    page_id: str = Field(..., description="Page ID")
    title: str = Field(..., description="Page 标题")
    type: str = Field(..., description="Page 类型")
    relevance_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="相关性得分"
    )
    snippet: str = Field(
        ..., 
        max_length=1000,
        description="内容片段"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="额外元数据"
    )


class KnowledgeResponse(BaseModel):
    """知识查询响应"""
    
    query: str = Field(..., description="原始查询")
    domain: str = Field(..., description="查询领域")
    results: List[KnowledgeResult] = Field(
        default_factory=list,
        description="查询结果列表"
    )
    total_found: int = Field(
        default=0,
        ge=0,
        description="找到的总数"
    )
    reasoning_path: List[str] = Field(
        default_factory=list,
        description="推理路径，记录访问的 Page IDs"
    )
    response_time_ms: float = Field(
        default=0.0,
        description="响应时间(毫秒)"
    )
    
    @field_validator('total_found')
    @classmethod
    def validate_total_found(cls, v: int, info) -> int:
        """确保 total_found >= len(results)"""
        results = info.data.get('results', [])
        return max(v, len(results))


# =============================================================================
# 学习相关模型
# =============================================================================

class MaterialType(str, Enum):
    """材料类型枚举"""
    
    PDF = "pdf"
    MARKDOWN = "markdown"
    TXT = "txt"
    URL = "url"
    DOCX = "docx"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    
    PENDING = "pending"           # 待处理
    PROCESSING = "processing"     # 处理中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"            # 失败


class LearningTask(BaseModel):
    """学习任务模型"""
    
    id: str = Field(..., description="任务唯一标识")
    material_path: str = Field(..., description="材料路径或 URL")
    material_type: MaterialType = Field(..., description="材料类型")
    domain: str = Field(..., description="目标领域")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="处理结果"
    )
    error: Optional[str] = Field(
        default=None,
        description="错误信息"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    
    def mark_processing(self) -> None:
        """标记为处理中"""
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.utcnow()
    
    def mark_completed(self, result: Dict[str, Any]) -> None:
        """标记为已完成"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.utcnow()
    
    def mark_failed(self, error: str) -> None:
        """标记为失败"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()


class LearningResult(BaseModel):
    """学习结果响应"""
    
    task_id: str = Field(..., description="任务 ID")
    status: TaskStatus = Field(..., description="任务状态")
    pages_created: int = Field(
        default=0,
        ge=0,
        description="创建的 Page 数量"
    )
    pages_updated: int = Field(
        default=0,
        ge=0,
        description="更新的 Page 数量"
    )
    page_ids: List[str] = Field(
        default_factory=list,
        description="创建/更新的 Page IDs"
    )
    message: str = Field(
        default="",
        description="状态信息"
    )
    processing_time_seconds: float = Field(
        default=0.0,
        description="处理时间(秒)"
    )


# =============================================================================
# 状态查询相关模型
# =============================================================================

class DomainStatus(BaseModel):
    """单个领域状态"""
    
    domain: str = Field(..., description="领域标识")
    name: str = Field(..., description="领域名称")
    description: str = Field(default="", description="领域描述")
    page_count: int = Field(default=0, ge=0, description="Page 数量")
    skill_count: int = Field(default=0, ge=0, description="Skill 类型数量")
    pattern_count: int = Field(default=0, ge=0, description="Pattern 类型数量")
    case_count: int = Field(default=0, ge=0, description="Case 类型数量")
    concept_count: int = Field(default=0, ge=0, description="Concept 类型数量")
    faq_count: int = Field(default=0, ge=0, description="FAQ 类型数量")
    last_updated: Optional[datetime] = Field(
        default=None,
        description="最后更新时间"
    )
    index_status: str = Field(
        default="unknown",
        description="索引状态: ok/degraded/rebuilding/error"
    )
    is_enabled: bool = Field(default=True, description="是否启用")


class SystemMetrics(BaseModel):
    """系统指标"""
    
    total_queries: int = Field(default=0, description="总查询次数")
    total_learning_tasks: int = Field(default=0, description="总学习任务数")
    active_learning_tasks: int = Field(default=0, description="活跃学习任务数")
    avg_query_time_ms: float = Field(default=0.0, description="平均查询时间")
    cache_hit_rate: float = Field(default=0.0, description="缓存命中率")


class StatusResponse(BaseModel):
    """状态查询响应"""
    
    server_status: str = Field(
        default="healthy",
        description="服务器状态: healthy/degraded/maintenance"
    )
    version: str = Field(..., description="版本号")
    uptime_seconds: float = Field(default=0.0, description="运行时间(秒)")
    domains: List[DomainStatus] = Field(
        default_factory=list,
        description="领域状态列表"
    )
    metrics: SystemMetrics = Field(
        default_factory=SystemMetrics,
        description="系统指标"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# 错误响应模型
# =============================================================================

class ErrorDetail(BaseModel):
    """错误详情"""
    
    code: str = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="额外详情"
    )


class ErrorResponse(BaseModel):
    """错误响应"""
    
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(default=None)
