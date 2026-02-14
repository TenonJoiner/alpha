"""
Page 数据模型

定义知识页面的核心数据结构
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class PageType(str, Enum):
    """Page 类型枚举"""
    
    SKILL = "skill"           # 技能/能力
    PATTERN = "pattern"       # 模式/最佳实践
    CASE = "case"            # 案例
    CONCEPT = "concept"      # 概念
    FAQ = "faq"              # 常见问题


class PageMetadata(BaseModel):
    """Page 元数据"""
    
    author: Optional[str] = Field(None, description="作者")
    source: Optional[str] = Field(None, description="来源")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    difficulty: Optional[str] = Field(None, description="难度级别: beginner/intermediate/advanced")
    estimated_time: Optional[int] = Field(None, description="预计阅读时间(分钟)")
    
    class Config:
        frozen = False


class PageLinks(BaseModel):
    """Page 知识链接"""
    
    prerequisites: List[str] = Field(
        default_factory=list, 
        description="前置知识 Page IDs"
    )
    related: List[str] = Field(
        default_factory=list,
        description="相关 Page IDs"
    )
    next_steps: List[str] = Field(
        default_factory=list,
        description="后续学习 Page IDs"
    )
    
    class Config:
        frozen = False


class Page(BaseModel):
    """
    知识页面模型
    
    这是 Cognitive Brain 的核心数据单元。
    每个 Page 代表一个完整的知识单元，可以是技能、模式、案例、概念或 FAQ。
    """
    
    # 基础信息
    id: str = Field(..., description="唯一标识符: {type}-{kebab-title}-{hash}")
    type: PageType = Field(..., description="Page 类型")
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    domain: str = Field(..., description="所属领域")
    
    # 内容
    content: str = Field(..., description="Markdown 格式内容")
    summary: Optional[str] = Field(None, description="内容摘要")
    
    # 元数据与链接
    metadata: PageMetadata = Field(default_factory=PageMetadata)
    links: PageLinks = Field(default_factory=PageLinks)
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 状态
    version: int = Field(default=1, ge=1, description="版本号")
    is_published: bool = Field(default=True, description="是否已发布")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "skill-inference-storage-a1b2c3",
                "type": "skill",
                "title": "推理存储技术选型",
                "domain": "storage-architect",
                "content": "# 推理存储技术选型\n\n推理存储是...",
                "metadata": {
                    "author": "AI Assistant",
                    "tags": ["storage", "inference", "AI"],
                    "difficulty": "advanced"
                },
                "links": {
                    "prerequisites": ["concept-storage-basics-x9y8z7"],
                    "related": ["pattern-inference-optimization-b2c3d4"]
                }
            }
        }
    
    def update_timestamp(self) -> None:
        """更新修改时间戳"""
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def add_tag(self, tag: str) -> None:
        """添加标签"""
        if tag not in self.metadata.tags:
            self.metadata.tags.append(tag)
            self.update_timestamp()
    
    def add_prerequisite(self, page_id: str) -> None:
        """添加前置知识链接"""
        if page_id not in self.links.prerequisites:
            self.links.prerequisites.append(page_id)
            self.update_timestamp()
    
    def add_related(self, page_id: str) -> None:
        """添加相关知识链接"""
        if page_id not in self.links.related:
            self.links.related.append(page_id)
            self.update_timestamp()


def generate_page_id(page_type: PageType, title: str, hash_suffix: str = "") -> str:
    """
    生成 Page ID
    
    格式: {type}-{kebab-title}-{hash}
    示例: skill-inference-storage-a1b2c3
    
    Args:
        page_type: Page 类型
        title: 标题
        hash_suffix: 可选的哈希后缀
        
    Returns:
        生成的 Page ID
    """
    import hashlib
    import re
    
    # 转换为 kebab-case
    kebab_title = re.sub(r'[^\w\s-]', '', title.lower())
    kebab_title = re.sub(r'[-\s]+', '-', kebab_title).strip('-')
    kebab_title = kebab_title[:50]  # 限制长度
    
    # 生成短哈希
    if not hash_suffix:
        hash_input = f"{page_type.value}-{title}-{datetime.utcnow().isoformat()}"
        hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:6]
    
    return f"{page_type.value}-{kebab_title}-{hash_suffix}"
