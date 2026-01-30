"""
Alpha REST API Server

FastAPI-based HTTP API for Alpha daemon interaction.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import psutil
import time

from .routes import tasks, status, health
from .schemas import ErrorResponse
from ..core.engine import AlphaEngine

logger = logging.getLogger(__name__)

# Global engine instance
_engine: Optional[AlphaEngine] = None
_start_time: float = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global _engine, _start_time

    logger.info("Starting Alpha API Server...")

    # Initialize Alpha engine
    _engine = AlphaEngine()
    await _engine.initialize()
    _start_time = time.time()

    logger.info("Alpha API Server started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Alpha API Server...")
    if _engine:
        await _engine.shutdown()
    logger.info("Alpha API Server shut down")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI app instance
    """
    app = FastAPI(
        title="Alpha REST API",
        description="HTTP API for Alpha AI Assistant",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal Server Error",
                detail=str(exc)
            ).model_dump()
        )

    # Include routers
    app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
    app.include_router(status.router, prefix="/api/v1", tags=["status"])
    app.include_router(health.router, prefix="/api", tags=["health"])

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": "Alpha REST API",
            "version": "1.0.0",
            "status": "operational",
            "docs": "/api/docs"
        }

    return app


def get_engine() -> AlphaEngine:
    """
    Get global Alpha engine instance.

    Returns:
        AlphaEngine instance

    Raises:
        RuntimeError: If engine not initialized
    """
    if _engine is None:
        raise RuntimeError("Alpha engine not initialized")
    return _engine


def get_uptime() -> float:
    """
    Get server uptime in seconds.

    Returns:
        Uptime in seconds
    """
    return time.time() - _start_time


def get_system_stats() -> dict:
    """
    Get system resource statistics.

    Returns:
        Dictionary with CPU and memory stats
    """
    process = psutil.Process()
    return {
        "cpu_percent": process.cpu_percent(),
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "threads": process.num_threads()
    }


async def start_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    reload: bool = False
):
    """
    Start API server.

    Args:
        host: Host to bind to
        port: Port to listen on
        reload: Enable auto-reload (development only)
    """
    logger.info(f"Starting API server on {host}:{port}")

    config = uvicorn.Config(
        app="alpha.api.server:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    # For development testing
    asyncio.run(start_server(reload=True))
