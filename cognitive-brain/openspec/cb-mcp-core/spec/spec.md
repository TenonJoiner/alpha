# cb-mcp-core Specification

## 基本信息

- **Proposal**: cb-mcp-core
- **目标**: 搭建 MCP Server 核心框架，实现基础接口
- **阶段**: Phase 1
- **状态**: spec → design → impl → archive

## 功能范围

### 1. MCP Server 基础框架
- FastAPI + MCP SDK 集成
- 支持 stdio 和 sse 传输方式
- 基础日志和错误处理

### 2. 核心接口 (3个)

#### 2.1 query_knowledge
```python
async def query_knowledge(
    query: str,           # 用户查询
    domain: str,          # 领域标识 (e.g., "storage-architect")
    context: dict | None  # 可选上下文
) -> KnowledgeResponse
```

#### 2.2 learn_material
```python
async def learn_material(
    material_path: str,   # 材料路径
    material_type: str,   # 类型: pdf, markdown, txt, url
    domain: str           # 目标领域
) -> LearningResult
```

#### 2.3 get_status
```python
async def get_status(
    domain: str | None    # 领域标识，None 表示所有领域
) -> StatusResponse
```

### 3. 数据模型

#### Page (知识页面)
```python
class Page:
    id: str                    # 唯一标识
    type: PageType             # skill/pattern/case/concept/faq
    title: str                 # 标题
    domain: str                # 所属领域
    content: str               # Markdown 内容
    metadata: PageMetadata     # 元数据
    links: PageLinks           # 知识链接
    created_at: datetime
    updated_at: datetime
```

#### KnowledgeQuery (知识查询请求)
```python
class KnowledgeQuery:
    query: str
    domain: str
    context: dict | None
    max_results: int = 5
```

#### LearningTask (学习任务)
```python
class LearningTask:
    id: str
    material_path: str
    material_type: str
    domain: str
    status: TaskStatus        # pending/processing/completed/failed
    result: dict | None
    created_at: datetime
    completed_at: datetime | None
```

## 技术约束

- Python 3.11+
- mcp SDK ^1.0.0
- FastAPI ^0.100.0
- Pydantic ^2.0.0

## 目录结构

```
cognitive-brain/
├── src/
│   ├── __init__.py
│   ├── server.py          # MCP Server 主入口
│   ├── models/
│   │   ├── __init__.py
│   │   ├── page.py        # Page 数据模型
│   │   └── requests.py    # 请求/响应模型
│   ├── api/
│   │   ├── __init__.py
│   │   ├── tools.py       # MCP Tools 实现
│   │   └── handlers.py    # 请求处理器
│   └── config.py          # 配置管理
├── tests/
│   ├── __init__.py
│   ├── test_server.py
│   └── test_models.py
├── pyproject.toml
├── README.md
└── brain.yaml             # 配置文件
```

## 验收标准

- [ ] MCP Server 可正常启动
- [ ] 3个核心接口可通过 MCP Client 调用
- [ ] 数据模型验证通过
- [ ] 基础测试用例通过
- [ ] 配置管理正常工作

## 依赖

- Phase 0: 项目初始化 (已完成)
- 后续: Phase 2 (推理引擎)
