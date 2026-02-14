"""
模型单元测试
"""

import pytest
from datetime import datetime

from src.models import (
    Page,
    PageType,
    PageMetadata,
    PageLinks,
    KnowledgeQuery,
    KnowledgeResponse,
    KnowledgeResult,
    LearningTask,
    LearningResult,
    MaterialType,
    TaskStatus,
    DomainStatus,
    StatusResponse,
    SystemMetrics,
    generate_page_id,
)


class TestPage:
    """Page 模型测试"""
    
    def test_page_creation(self):
        """测试 Page 创建"""
        page = Page(
            id="skill-test-abc123",
            type=PageType.SKILL,
            title="测试技能",
            domain="storage-architect",
            content="# 测试内容"
        )
        
        assert page.id == "skill-test-abc123"
        assert page.type == PageType.SKILL
        assert page.title == "测试技能"
        assert page.domain == "storage-architect"
        assert page.version == 1
        assert page.is_published is True
    
    def test_page_with_metadata(self):
        """测试带元数据的 Page"""
        page = Page(
            id="concept-test-def456",
            type=PageType.CONCEPT,
            title="测试概念",
            domain="storage-architect",
            content="内容",
            metadata=PageMetadata(
                author="Test Author",
                tags=["test", "demo"],
                difficulty="beginner"
            ),
            links=PageLinks(
                prerequisites=["page-1"],
                related=["page-2"]
            )
        )
        
        assert page.metadata.author == "Test Author"
        assert "test" in page.metadata.tags
        assert "page-1" in page.links.prerequisites
    
    def test_page_update_timestamp(self):
        """测试更新时间戳"""
        page = Page(
            id="skill-test-ghi789",
            type=PageType.SKILL,
            title="测试",
            domain="storage-architect",
            content="内容"
        )
        
        old_updated = page.updated_at
        old_version = page.version
        
        page.update_timestamp()
        
        assert page.updated_at > old_updated
        assert page.version == old_version + 1
    
    def test_page_add_tag(self):
        """测试添加标签"""
        page = Page(
            id="skill-test",
            type=PageType.SKILL,
            title="测试",
            domain="storage-architect",
            content="内容"
        )
        
        page.add_tag("new-tag")
        assert "new-tag" in page.metadata.tags
        
        # 重复添加不应重复
        page.add_tag("new-tag")
        assert page.metadata.tags.count("new-tag") == 1
    
    def test_page_id_generation(self):
        """测试 Page ID 生成"""
        page_id = generate_page_id(
            PageType.SKILL,
            "Inference Storage Best Practice"
        )
        
        assert page_id.startswith("skill-inference-storage-best-practice")
        assert len(page_id) > 30  # 包含哈希后缀


class TestKnowledgeQuery:
    """知识查询模型测试"""
    
    def test_query_creation(self):
        """测试查询创建"""
        query = KnowledgeQuery(
            query="什么是推理存储？",
            domain="storage-architect",
            max_results=10
        )
        
        assert query.query == "什么是推理存储？"
        assert query.domain == "storage-architect"
        assert query.max_results == 10
        assert query.context is None
    
    def test_query_validation(self):
        """测试查询验证"""
        with pytest.raises(ValueError):
            KnowledgeQuery(
                query="test",
                domain="test",
                max_results=0  # 最小值为 1
            )
        
        with pytest.raises(ValueError):
            KnowledgeQuery(
                query="test",
                domain="test",
                max_results=25  # 最大值为 20
            )
    
    def test_knowledge_response(self):
        """测试查询响应"""
        result = KnowledgeResult(
            page_id="skill-test-123",
            title="测试技能",
            type="skill",
            relevance_score=0.95,
            snippet="这是摘要..."
        )
        
        response = KnowledgeResponse(
            query="测试查询",
            domain="storage-architect",
            results=[result],
            total_found=1
        )
        
        assert len(response.results) == 1
        assert response.results[0].relevance_score == 0.95
        assert response.total_found >= len(response.results)


class TestLearningTask:
    """学习任务模型测试"""
    
    def test_task_creation(self):
        """测试任务创建"""
        task = LearningTask(
            id="task-123",
            material_path="/path/to/doc.pdf",
            material_type=MaterialType.PDF,
            domain="storage-architect"
        )
        
        assert task.id == "task-123"
        assert task.status == TaskStatus.PENDING
        assert task.material_type == MaterialType.PDF
    
    def test_task_state_transitions(self):
        """测试任务状态转换"""
        task = LearningTask(
            id="task-456",
            material_path="/path/to/doc.md",
            material_type=MaterialType.MARKDOWN,
            domain="storage-architect"
        )
        
        # 处理中
        task.mark_processing()
        assert task.status == TaskStatus.PROCESSING
        assert task.started_at is not None
        
        # 完成
        task.mark_completed({"pages_created": 3})
        assert task.status == TaskStatus.COMPLETED
        assert task.result["pages_created"] == 3
        assert task.completed_at is not None
        
        # 新任务测试失败
        task2 = LearningTask(
            id="task-789",
            material_path="/path/to/doc.txt",
            material_type=MaterialType.TXT,
            domain="storage-architect"
        )
        task2.mark_failed("Parse error")
        assert task2.status == TaskStatus.FAILED
        assert task2.error == "Parse error"
    
    def test_learning_result(self):
        """测试结果模型"""
        result = LearningResult(
            task_id="task-123",
            status=TaskStatus.COMPLETED,
            pages_created=5,
            message="Success",
            processing_time_seconds=12.5
        )
        
        assert result.pages_created == 5
        assert result.processing_time_seconds == 12.5


class TestStatusModels:
    """状态模型测试"""
    
    def test_domain_status(self):
        """测试领域状态"""
        status = DomainStatus(
            domain="storage-architect",
            name="存储架构师",
            page_count=100,
            skill_count=20,
            index_status="ok"
        )
        
        assert status.domain == "storage-architect"
        assert status.page_count == 100
    
    def test_system_metrics(self):
        """测试系统指标"""
        metrics = SystemMetrics(
            total_queries=1000,
            total_learning_tasks=50,
            avg_query_time_ms=150.5,
            cache_hit_rate=0.75
        )
        
        assert metrics.total_queries == 1000
        assert metrics.cache_hit_rate == 0.75
    
    def test_status_response(self):
        """测试状态响应"""
        domain = DomainStatus(
            domain="storage-architect",
            name="存储架构师",
            page_count=50
        )
        
        response = StatusResponse(
            server_status="healthy",
            version="0.1.0",
            uptime_seconds=3600,
            domains=[domain],
            metrics=SystemMetrics()
        )
        
        assert response.server_status == "healthy"
        assert len(response.domains) == 1
        assert response.timestamp is not None


class TestPageType:
    """PageType 枚举测试"""
    
    def test_page_type_values(self):
        """测试枚举值"""
        assert PageType.SKILL.value == "skill"
        assert PageType.PATTERN.value == "pattern"
        assert PageType.CASE.value == "case"
        assert PageType.CONCEPT.value == "concept"
        assert PageType.FAQ.value == "faq"
    
    def test_page_type_from_string(self):
        """测试从字符串创建"""
        assert PageType("skill") == PageType.SKILL
        assert PageType("concept") == PageType.CONCEPT


class TestMaterialType:
    """MaterialType 枚举测试"""
    
    def test_material_type_values(self):
        """测试枚举值"""
        assert MaterialType.PDF.value == "pdf"
        assert MaterialType.MARKDOWN.value == "markdown"
        assert MaterialType.TXT.value == "txt"
        assert MaterialType.URL.value == "url"
