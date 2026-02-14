# cb-mcp-core Tasks

## 任务清单

### T1: 项目初始化
- [x] T1.1 创建目录结构
- [x] T1.2 创建 pyproject.toml
- [x] T1.3 创建 README.md

### T2: 数据模型实现
- [x] T2.1 Page 数据模型 (page.py)
  - PageType 枚举
  - PageMetadata 模型
  - PageLinks 模型
  - Page 主模型
- [x] T2.2 请求/响应模型 (requests.py)
  - KnowledgeQuery / KnowledgeResponse
  - LearningTask / LearningResult
  - StatusResponse

### T3: MCP Server 框架
- [x] T3.1 server.py 主入口
  - FastAPI 应用初始化
  - MCP Server 初始化
  - 生命周期管理
- [x] T3.2 tools.py 工具实现
  - query_knowledge 工具
  - learn_material 工具
  - get_status 工具

### T4: 配置管理
- [x] T4.1 config.py 配置模块
  - BrainConfig 模型
  - DomainConfig 模型
  - YAML 加载/保存
- [x] T4.2 brain.yaml 配置文件
  - 服务器配置
  - 领域配置

### T5: 测试
- [x] T5.1 单元测试
  - test_models.py
  - test_server.py

### T6: 文档
- [x] T6.1 API 文档
- [x] T6.2 使用说明

## 任务依赖图

```
T1 (初始化)
  │
  ├──→ T2 (数据模型)
  │      │
  │      └──→ T3 (MCP Server)
  │             │
  │             ├──→ T4 (配置)
  │             │
  │             └──→ T5 (测试)
  │
  └──→ T6 (文档)
```

## 进度追踪

| 任务 | 状态 | 完成时间 |
|------|------|----------|
| T1 | ✅ Done | 2026-02-14 |
| T2 | ✅ Done | 2026-02-14 |
| T3 | ✅ Done | 2026-02-14 |
| T4 | ✅ Done | 2026-02-14 |
| T5 | ✅ Done | 2026-02-14 |
| T6 | ✅ Done | 2026-02-14 |

## 时间预估

| 模块 | 预估时间 | 实际时间 |
|------|----------|----------|
| 目录结构 & 配置 | 15 min | - |
| 数据模型 | 30 min | - |
| MCP Server 框架 | 45 min | - |
| 配置管理 | 20 min | - |
| 测试 | 30 min | - |
| 文档 | 20 min | - |
| **总计** | **~3 hours** | - |
