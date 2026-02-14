"""
Cognitive Brain MCP Server

主入口文件，初始化并运行 MCP Server
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from anyio.lowlevel import checkpoint
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from mcp.server import Server
from mcp.server.sse import SseServerTransport

from .api import ToolRegistry
from .config import BrainConfig, create_default_config, get_config, set_config
from .models import Page, PageMetadata, PageLinks, PageType, generate_page_id

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cognitive-brain")


# 全局组件
_config: BrainConfig | None = None
_registry: ToolRegistry | None = None


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[dict]:
    """FastAPI 生命周期管理"""
    # 启动
    logger.info("Cognitive Brain MCP Server starting...")
    
    # 加载配置
    global _config, _registry
    try:
        _config = get_config()
        logger.info(f"Config loaded: {_config.server.name} v{_config.server.version}")
    except Exception as e:
        logger.warning(f"Failed to load config: {e}, using default")
        _config = create_default_config()
        set_config(_config)
    
    # 初始化工具注册器
    _registry = ToolRegistry()
    
    # 添加一些示例数据 (用于演示)
    _add_sample_data()
    
    logger.info(f"Server ready. Enabled domains: {_config.list_enabled_domains()}")
    
    yield {"config": _config, "registry": _registry}
    
    # 关闭
    logger.info("Cognitive Brain MCP Server shutting down...")


def _add_sample_data():
    """添加示例数据"""
    global _registry
    if _registry is None:
        return
    
    # 添加示例 Page
    sample_pages = [
        Page(
            id=generate_page_id(PageType.CONCEPT, "推理存储基础"),
            type=PageType.CONCEPT,
            title="推理存储基础",
            domain="storage-architect",
            content="""# 推理存储基础

推理存储(Inference Storage)是一种面向 AI 工作负载优化的存储架构。

## 核心特点

1. **高吞吐顺序读取**: 支持大模型参数加载
2. **低延迟随机访问**: 支持 KV Cache 随机读取
3. **弹性扩展**: 随 GPU 规模线性扩展

## 典型场景

- 大语言模型推理
- 多模态模型服务
- 实时推荐系统
""",
            metadata=PageMetadata(
                author="System",
                tags=["storage", "inference", "AI", "基础概念"],
                difficulty="beginner"
            ),
            links=PageLinks(
                related=[],
                next_steps=[]
            )
        ),
        Page(
            id=generate_page_id(PageType.SKILL, "推理存储选型"),
            type=PageType.SKILL,
            title="推理存储选型方法论",
            domain="storage-architect",
            content="""# 推理存储选型方法论

## 选型框架

### 1. 工作负载分析
- 模型规模 (参数数量)
- 并发请求量
- 延迟要求 (P99)

### 2. 存储类型选择
| 场景 | 推荐存储 | 理由 |
|------|----------|------|
| 大模型加载 | 本地 NVMe | 最低延迟 |
| KV Cache | 分布式 KV | 弹性扩展 |
| 检查点 | 对象存储 | 成本最优 |

### 3. 容量规划
- 模型参数: 2 bytes/param (FP16)
- KV Cache: batch_size × seq_len × hidden_dim × 2
- 预留 30% 余量
""",
            metadata=PageMetadata(
                author="System",
                tags=["storage", "inference", "选型", "方法论"],
                difficulty="intermediate"
            ),
            links=PageLinks(
                prerequisites=[],
                related=[]
            )
        ),
    ]
    
    for page in sample_pages:
        _registry.add_page(page)
    
    logger.info(f"Added {len(sample_pages)} sample pages")


# 创建 FastAPI 应用
app = FastAPI(
    title="Cognitive Brain MCP Server",
    description="面向数字员工的外置知识库 MCP Server",
    version="0.1.0",
    lifespan=app_lifespan
)


@app.get("/")
async def root():
    """根路径 - 服务状态"""
    config = get_config()
    return {
        "name": config.server.name,
        "version": config.server.version,
        "status": "healthy",
        "domains": config.list_enabled_domains()
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


@app.get("/api/v1/domains")
async def list_domains():
    """列出所有领域"""
    config = get_config()
    return {
        "domains": [
            {
                "id": k,
                "name": v.name,
                "description": v.description,
                "enabled": v.enabled
            }
            for k, v in config.domains.items()
        ]
    }


# SSE 端点 (MCP 传输)
sse_transport = SseServerTransport("/messages/")


@app.get("/sse")
async def sse_endpoint():
    """SSE 连接端点"""
    from starlette.responses import StreamingResponse
    
    async with sse_transport.connect_sse(
        scope={},  # type: ignore
        receive=None,  # type: ignore
        send=None  # type: ignore
    ) as (read_stream, write_stream):
        server = Server("cognitive-brain")
        
        if _registry:
            await _registry.register(server)
        
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )
    
    return StreamingResponse(
        sse_transport.get_stream(),
        media_type="text/event-stream"
    )


async def run_stdio_server():
    """运行 stdio 模式的 MCP Server"""
    from mcp.server.stdio import stdio_server
    
    logger.info("Starting stdio MCP server...")
    
    # 加载配置
    global _config, _registry
    try:
        _config = get_config()
    except Exception as e:
        logger.warning(f"Failed to load config: {e}, using default")
        _config = create_default_config()
        set_config(_config)
    
    _registry = ToolRegistry()
    _add_sample_data()
    
    # 创建 MCP Server
    server = Server("cognitive-brain")
    await _registry.register(server)
    
    # 使用 stdio 传输运行
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """主入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cognitive Brain MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="传输方式 (默认: stdio)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="SSE 模式下的监听地址"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="SSE 模式下的监听端口"
    )
    parser.add_argument(
        "--config",
        default="brain.yaml",
        help="配置文件路径"
    )
    
    args = parser.parse_args()
    
    # 加载指定配置
    if args.config:
        try:
            config = BrainConfig.from_yaml(args.config)
            set_config(config)
            logger.info(f"Loaded config from {args.config}")
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
    
    if args.transport == "stdio":
        # stdio 模式
        asyncio.run(run_stdio_server())
    else:
        # SSE 模式 (FastAPI)
        logger.info(f"Starting SSE server on {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
