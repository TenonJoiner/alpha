"""
MCP Tools 实现

实现 query_knowledge, learn_material, get_status 三个核心工具
"""

import asyncio
import hashlib
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import TextContent, Tool

from ..models import (
    DomainStatus,
    KnowledgeQuery,
    KnowledgeResponse,
    KnowledgeResult,
    LearningResult,
    LearningTask,
    MaterialType,
    Page,
    StatusResponse,
    SystemMetrics,
    TaskStatus,
)
from ..config import get_config


class ToolRegistry:
    """MCP Tool 注册器"""
    
    def __init__(self):
        self.server: Optional[Server] = None
        self._pages: Dict[str, Page] = {}  # 内存中的 Page 存储
        self._tasks: Dict[str, LearningTask] = {}  # 任务存储
        self._metrics = {
            "total_queries": 0,
            "total_learning_tasks": 0,
            "query_times": [],
        }
        self._start_time = datetime.utcnow()
    
    async def register(self, server: Server) -> None:
        """注册所有工具到 MCP Server"""
        self.server = server
        
        # 注册工具列表处理器
        @server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="query_knowledge",
                    description="查询领域知识库，获取专业信息。支持按领域查询相关技能、模式、案例、概念和FAQ。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "用户查询内容"
                            },
                            "domain": {
                                "type": "string",
                                "description": "领域标识，如 'storage-architect'"
                            },
                            "context": {
                                "type": "object",
                                "description": "可选上下文信息"
                            }
                        },
                        "required": ["query", "domain"]
                    }
                ),
                Tool(
                    name="learn_material",
                    description="学习新材料，提取知识并创建 Page。支持 PDF、Markdown、TXT 和 URL。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "material_path": {
                                "type": "string",
                                "description": "材料路径或 URL"
                            },
                            "material_type": {
                                "type": "string",
                                "enum": ["pdf", "markdown", "txt", "url"],
                                "description": "材料类型"
                            },
                            "domain": {
                                "type": "string",
                                "description": "目标领域"
                            }
                        },
                        "required": ["material_path", "material_type", "domain"]
                    }
                ),
                Tool(
                    name="get_status",
                    description="获取知识库状态信息，包括各领域的 Page 数量、索引状态等。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "domain": {
                                "type": "string",
                                "description": "领域标识，不传则返回所有领域"
                            }
                        }
                    }
                )
            ]
        
        # 注册工具调用处理器
        @server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            return await self._handle_tool_call(name, arguments)
    
    async def _handle_tool_call(
        self, 
        name: str, 
        arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """处理工具调用"""
        import json
        
        try:
            if name == "query_knowledge":
                result = await self._query_knowledge(arguments)
            elif name == "learn_material":
                result = await self._learn_material(arguments)
            elif name == "get_status":
                result = await self._get_status(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            return [TextContent(
                type="text",
                text=json.dumps(result, default=str, ensure_ascii=False, indent=2)
            )]
        
        except Exception as e:
            error_response = {
                "error": {
                    "code": "TOOL_ERROR",
                    "message": str(e),
                    "tool": name
                }
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, ensure_ascii=False)
            )]
    
    async def _query_knowledge(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理知识查询"""
        start_time = time.time()
        
        query = KnowledgeQuery(
            query=arguments.get("query", ""),
            domain=arguments.get("domain", ""),
            context=arguments.get("context"),
            max_results=arguments.get("max_results", 5)
        )
        
        # 检查领域是否存在
        config = get_config()
        if query.domain not in config.domains:
            return {
                "error": {
                    "code": "DOMAIN_NOT_FOUND",
                    "message": f"Domain '{query.domain}' not found"
                }
            }
        
        # 简单关键词匹配 (Phase 1 简化实现)
        results = []
        query_lower = query.query.lower()
        reasoning_path = []
        
        for page_id, page in self._pages.items():
            if page.domain != query.domain:
                continue
            
            # 计算相关性得分
            score = 0.0
            if query_lower in page.title.lower():
                score += 0.5
            if query_lower in page.content.lower():
                score += 0.3
            if any(query_lower in tag.lower() for tag in page.metadata.tags):
                score += 0.2
            
            if score > 0:
                results.append(KnowledgeResult(
                    page_id=page.id,
                    title=page.title,
                    type=page.type.value,
                    relevance_score=score,
                    snippet=page.content[:300] + "..." if len(page.content) > 300 else page.content,
                    metadata={
                        "tags": page.metadata.tags,
                        "difficulty": page.metadata.difficulty
                    }
                ))
                reasoning_path.append(page.id)
        
        # 按相关性排序
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        results = results[:query.max_results]
        
        response_time = (time.time() - start_time) * 1000
        
        # 更新指标
        self._metrics["total_queries"] += 1
        self._metrics["query_times"].append(response_time)
        if len(self._metrics["query_times"]) > 100:
            self._metrics["query_times"] = self._metrics["query_times"][-100:]
        
        response = KnowledgeResponse(
            query=query.query,
            domain=query.domain,
            results=results,
            total_found=len(results),
            reasoning_path=reasoning_path[:10],
            response_time_ms=response_time
        )
        
        return response.model_dump()
    
    async def _learn_material(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理学习材料"""
        start_time = time.time()
        
        material_path = arguments.get("material_path", "")
        material_type_str = arguments.get("material_type", "")
        domain = arguments.get("domain", "")
        
        # 验证参数
        try:
            material_type = MaterialType(material_type_str)
        except ValueError:
            return {
                "error": {
                    "code": "INVALID_MATERIAL_TYPE",
                    "message": f"Invalid material type: {material_type_str}"
                }
            }
        
        # 检查领域
        config = get_config()
        if domain not in config.domains:
            return {
                "error": {
                    "code": "DOMAIN_NOT_FOUND",
                    "message": f"Domain '{domain}' not found"
                }
            }
        
        # 生成任务 ID
        task_id = hashlib.md5(
            f"{material_path}-{domain}-{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # 创建任务
        task = LearningTask(
            id=task_id,
            material_path=material_path,
            material_type=material_type,
            domain=domain
        )
        self._tasks[task_id] = task
        
        # 更新指标
        self._metrics["total_learning_tasks"] += 1
        
        # Phase 1: 模拟学习过程 (实际实现需要解析材料)
        task.mark_processing()
        
        # 模拟异步处理
        # 在实际实现中，这里应该调用文档解析和 LLM 知识抽取
        await asyncio.sleep(0.1)  # 模拟处理时间
        
        # 模拟创建 Page
        pages_created = 0
        page_ids = []
        
        # 这里只是演示，实际应该根据材料内容生成
        if "pdf" in material_path or "doc" in material_path:
            pages_created = 1
        
        task.mark_completed({
            "pages_created": pages_created,
            "material_processed": True
        })
        
        processing_time = time.time() - start_time
        
        result = LearningResult(
            task_id=task_id,
            status=task.status,
            pages_created=pages_created,
            message=f"Material learning task created: {task_id}",
            processing_time_seconds=processing_time
        )
        
        return result.model_dump()
    
    async def _get_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理状态查询"""
        config = get_config()
        target_domain = arguments.get("domain")
        
        # 计算各领域的统计
        domain_stats: Dict[str, Dict[str, Any]] = {}
        
        for page_id, page in self._pages.items():
            domain = page.domain
            if target_domain and domain != target_domain:
                continue
            
            if domain not in domain_stats:
                domain_stats[domain] = {
                    "count": 0,
                    "types": {},
                    "last_updated": None
                }
            
            domain_stats[domain]["count"] += 1
            domain_stats[domain]["types"][page.type.value] = \
                domain_stats[domain]["types"].get(page.type.value, 0) + 1
            
            if (domain_stats[domain]["last_updated"] is None or 
                page.updated_at > domain_stats[domain]["last_updated"]):
                domain_stats[domain]["last_updated"] = page.updated_at
        
        # 构建领域状态列表
        domains = []
        for domain_id, domain_config in config.domains.items():
            if target_domain and domain_id != target_domain:
                continue
            
            stats = domain_stats.get(domain_id, {})
            types = stats.get("types", {})
            
            domains.append(DomainStatus(
                domain=domain_id,
                name=domain_config.name,
                description=domain_config.description,
                page_count=stats.get("count", 0),
                skill_count=types.get("skill", 0),
                pattern_count=types.get("pattern", 0),
                case_count=types.get("case", 0),
                concept_count=types.get("concept", 0),
                faq_count=types.get("faq", 0),
                last_updated=stats.get("last_updated"),
                index_status="ok",
                is_enabled=domain_config.enabled
            ))
        
        # 计算运行时间
        uptime = (datetime.utcnow() - self._start_time).total_seconds()
        
        # 计算平均查询时间
        avg_query_time = 0.0
        if self._metrics["query_times"]:
            avg_query_time = sum(self._metrics["query_times"]) / len(self._metrics["query_times"])
        
        # 计算活跃任务数
        active_tasks = sum(
            1 for task in self._tasks.values()
            if task.status == TaskStatus.PROCESSING
        )
        
        response = StatusResponse(
            server_status="healthy",
            version=config.server.version,
            uptime_seconds=uptime,
            domains=domains,
            metrics=SystemMetrics(
                total_queries=self._metrics["total_queries"],
                total_learning_tasks=self._metrics["total_learning_tasks"],
                active_learning_tasks=active_tasks,
                avg_query_time_ms=avg_query_time,
                cache_hit_rate=0.0  # Phase 1 未实现缓存
            )
        )
        
        return response.model_dump()
    
    def add_page(self, page: Page) -> None:
        """添加 Page (用于测试和演示)"""
        self._pages[page.id] = page
    
    def get_page(self, page_id: str) -> Optional[Page]:
        """获取 Page"""
        return self._pages.get(page_id)
    
    def get_all_pages(self) -> Dict[str, Page]:
        """获取所有 Pages"""
        return self._pages.copy()
