# cb-mcp-core Design

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Client (OpenClaw)                    │
└───────────────────────────┬─────────────────────────────────┘
                            │ MCP Protocol (stdio/sse)
┌───────────────────────────┼─────────────────────────────────┐
│                           ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              MCP Server (FastAPI + mcp SDK)            │  │
│  │                                                        │  │
│  │   ┌──────────────┐    ┌──────────────┐               │  │
│  │   │   Tool:      │    │   Tool:      │               │  │
│  │   │ query_       │    │ learn_       │               │  │
│  │   │ knowledge    │    │ material     │               │  │
│  │   └──────────────┘    └──────────────┘               │  │
│  │                                                        │  │
│  │   ┌──────────────┐                                    │  │
│  │   │   Tool:      │                                    │  │
│  │   │ get_status   │                                    │  │
│  │   └──────────────┘                                    │  │
│  │                                                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                 │
│   ┌───────────────────────┴───────────────────────┐        │
│   │              Data Layer                        │        │
│   │   - Page Index (SQLite/Memory)                 │        │
│   │   - Config (brain.yaml)                        │        │
│   └───────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 模块设计

### 1. server.py - MCP Server 主入口

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from fastapi import FastAPI

app = FastAPI()
server = Server("cognitive-brain")

# 注册工具
@app.on_event("startup")
async def startup():
    await init_tools()

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, 
            write_stream, 
            server.create_initialization_options()
        )
```

### 2. models/page.py - Page 数据模型

```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import List, Optional

class PageType(str, Enum):
    SKILL = "skill"
    PATTERN = "pattern"
    CASE = "case"
    CONCEPT = "concept"
    FAQ = "faq"

class PageMetadata(BaseModel):
    author: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    difficulty: Optional[str] = None

class PageLinks(BaseModel):
    prerequisites: List[str] = Field(default_factory=list)
    related: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)

class Page(BaseModel):
    id: str
    type: PageType
    title: str
    domain: str
    content: str
    metadata: PageMetadata = Field(default_factory=PageMetadata)
    links: PageLinks = Field(default_factory=PageLinks)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 3. models/requests.py - 请求/响应模型

```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

# Query
class KnowledgeQuery(BaseModel):
    query: str
    domain: str
    context: Optional[Dict[str, Any]] = None
    max_results: int = Field(default=5, ge=1, le=20)

class KnowledgeResult(BaseModel):
    page_id: str
    title: str
    type: str
    relevance_score: float
    snippet: str

class KnowledgeResponse(BaseModel):
    query: str
    domain: str
    results: List[KnowledgeResult]
    total_found: int
    reasoning_path: List[str] = Field(default_factory=list)

# Learning
class MaterialType(str, Enum):
    PDF = "pdf"
    MARKDOWN = "markdown"
    TXT = "txt"
    URL = "url"

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class LearningTask(BaseModel):
    id: str
    material_path: str
    material_type: MaterialType
    domain: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class LearningResult(BaseModel):
    task_id: str
    status: TaskStatus
    pages_created: int = 0
    message: str

# Status
class DomainStatus(BaseModel):
    domain: str
    page_count: int
    last_updated: Optional[datetime]
    index_status: str

class StatusResponse(BaseModel):
    server_status: str
    version: str
    domains: List[DomainStatus]
    uptime_seconds: float
```

### 4. api/tools.py - MCP Tools 实现

```python
from mcp.server import Server
from ..models.requests import (
    KnowledgeQuery, KnowledgeResponse,
    LearningTask, LearningResult,
    StatusResponse
)

async def register_tools(server: Server):
    """注册所有 MCP Tools"""
    
    @server.call_tool()
    async def query_knowledge(
        query: str,
        domain: str,
        context: dict = None
    ) -> KnowledgeResponse:
        """查询领域知识"""
        # 实现查询逻辑
        pass
    
    @server.call_tool()
    async def learn_material(
        material_path: str,
        material_type: str,
        domain: str
    ) -> LearningResult:
        """学习新材料"""
        # 实现学习逻辑
        pass
    
    @server.call_tool()
    async def get_status(
        domain: str = None
    ) -> StatusResponse:
        """获取知识库状态"""
        # 实现状态查询
        pass
```

### 5. config.py - 配置管理

```python
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import List, Dict
import yaml
from pathlib import Path

class DomainConfig(BaseModel):
    name: str
    description: str
    data_path: str
    enabled: bool = True

class BrainConfig(BaseSettings):
    """Cognitive Brain 配置"""
    
    # Server
    server_name: str = "cognitive-brain"
    version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Paths
    data_root: Path = Path("/data/knowledge-brains")
    config_path: Path = Path("brain.yaml")
    
    # Domains
    domains: Dict[str, DomainConfig] = Field(default_factory=dict)
    
    # LLM (预留)
    llm_provider: str = "claude"
    llm_model: str = "claude-3-sonnet"
    
    @classmethod
    def from_yaml(cls, path: str = "brain.yaml") -> "BrainConfig":
        """从 YAML 文件加载配置"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    def to_yaml(self, path: str = None):
        """保存配置到 YAML"""
        path = path or self.config_path
        with open(path, 'w') as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)
```

## 接口定义

### MCP Tool Schema

#### query_knowledge
```json
{
  "name": "query_knowledge",
  "description": "查询领域知识库，获取专业信息",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "用户查询"},
      "domain": {"type": "string", "description": "领域标识"},
      "context": {"type": "object", "description": "可选上下文"}
    },
    "required": ["query", "domain"]
  }
}
```

#### learn_material
```json
{
  "name": "learn_material",
  "description": "学习新材料，提取知识并创建 Page",
  "inputSchema": {
    "type": "object",
    "properties": {
      "material_path": {"type": "string", "description": "材料路径"},
      "material_type": {"type": "string", "enum": ["pdf", "markdown", "txt", "url"]},
      "domain": {"type": "string", "description": "目标领域"}
    },
    "required": ["material_path", "material_type", "domain"]
  }
}
```

#### get_status
```json
{
  "name": "get_status",
  "description": "获取知识库状态信息",
  "inputSchema": {
    "type": "object",
    "properties": {
      "domain": {"type": "string", "description": "领域标识，null 表示所有领域"}
    }
  }
}
```

## 数据结构

### Page Index 存储格式 (内存/JSON)

```json
{
  "version": "1.0",
  "last_updated": "2026-02-14T19:00:00Z",
  "pages": {
    "skill-inference-storage": {
      "id": "skill-inference-storage-a1b2c3",
      "type": "skill",
      "title": "推理存储技术",
      "domain": "storage-architect",
      "metadata": {...},
      "links": {...}
    }
  },
  "by_domain": {
    "storage-architect": ["skill-inference-storage-a1b2c3", ...]
  },
  "by_type": {
    "skill": ["skill-inference-storage-a1b2c3", ...]
  }
}
```

## 错误处理

### 错误码定义

| 错误码 | 描述 | HTTP 状态 |
|--------|------|----------|
| E001 | 领域不存在 | 404 |
| E002 | Page 未找到 | 404 |
| E003 | 材料格式不支持 | 400 |
| E004 | 学习处理失败 | 500 |
| E005 | 配置错误 | 500 |

### 错误响应格式

```json
{
  "error": {
    "code": "E001",
    "message": "Domain 'unknown' not found",
    "details": {}
  }
}
```

## 配置示例 (brain.yaml)

```yaml
server_name: cognitive-brain
version: 0.1.0
host: 0.0.0.0
port: 8000

data_root: /data/knowledge-brains

domains:
  storage-architect:
    name: 存储架构师
    description: 企业存储架构设计知识
    data_path: storage-architect
    enabled: true
  
  network-architect:
    name: 网络架构师
    description: 网络架构设计知识
    data_path: network-architect
    enabled: false

llm_provider: claude
llm_model: claude-3-sonnet-20240229
```
