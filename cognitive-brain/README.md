# Cognitive Brain

Cognitive Brain 是一个面向数字员工的外置知识库平台，通过 MCP 协议为 OpenClaw 提供外挂知识能力。

## 项目概述

- **领域专业化**: 让 OpenClaw 具备特定领域专业技能
- **知识外挂**: 通过外置知识库扩展能力，不修改核心代码
- **增量学习**: 持续从新材料中学习，知识库自动进化
- **多领域支持**: 存储架构师、网络架构师等多个专业领域

## 技术栈

- Python 3.11+
- MCP SDK
- FastAPI
- Pydantic

## 项目结构

```
cognitive-brain/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── server.py          # MCP Server 主入口
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── page.py        # Page 数据模型
│   │   └── requests.py    # 请求/响应模型
│   ├── api/               # API 实现
│   │   ├── __init__.py
│   │   ├── tools.py       # MCP Tools
│   │   └── handlers.py    # 请求处理器
│   └── config.py          # 配置管理
├── tests/                 # 测试
├── openspec/              # openspec 文档
├── pyproject.toml         # 项目配置
├── brain.yaml            # 运行时配置
└── README.md             # 本文档
```

## 快速开始

### 安装依赖

```bash
pip install -e ".[dev]"
```

### 配置

编辑 `brain.yaml`:

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
```

### 运行

```bash
# 开发模式
uvicorn src.server:app --reload

# 生产模式
python -m src.server
```

## MCP Tools

### query_knowledge

查询领域知识库。

```python
{
    "query": "什么是推理存储？",
    "domain": "storage-architect",
    "context": {"user_level": "expert"}
}
```

### learn_material

学习新材料。

```python
{
    "material_path": "/path/to/document.pdf",
    "material_type": "pdf",
    "domain": "storage-architect"
}
```

### get_status

获取知识库状态。

```python
{
    "domain": "storage-architect"  # null 表示所有领域
}
```

## 开发

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black src tests
ruff check src tests
```

## 许可证

MIT License
