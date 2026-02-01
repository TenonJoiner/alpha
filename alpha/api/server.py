"""
Alpha REST API Server

FastAPI-based HTTP API for Alpha daemon interaction.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .routes import tasks, status, health, websocket
from .schemas import ErrorResponse
from .dependencies import set_engine, set_chat_handler
from .chat_handler import ChatHandler
from ..core.engine import AlphaEngine
from ..utils.config import load_config
from ..llm.service import LLMService
from ..tools.registry import create_default_registry
from ..skills.registry import SkillRegistry
from ..skills.marketplace import SkillMarketplace
from ..skills.installer import SkillInstaller
from ..skills.executor import SkillExecutor
from ..skills.auto_manager import AutoSkillManager
from ..skills import preinstall_builtin_skills

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""

    logger.info("Starting Alpha API Server...")

    # Load configuration from project root
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.yaml"
    config = load_config(str(config_path))

    # Initialize Alpha engine
    engine = AlphaEngine(config)
    await engine.startup()
    set_engine(engine)

    # Create LLM service
    llm_service = LLMService.from_config(config.llm)

    # Create tool registry
    tool_registry = create_default_registry(llm_service, config)

    # Create skill system
    skill_config = config.dict().get('skills', {}) if hasattr(config, 'dict') else {}
    skill_registry = SkillRegistry()
    skill_marketplace = SkillMarketplace(config=skill_config)
    skill_installer = SkillInstaller()

    # Preinstall builtin skills
    logger.info("Loading builtin skills...")
    installed_count = await preinstall_builtin_skills(skill_registry, skill_installer)
    if installed_count > 0:
        logger.info(f"Loaded {installed_count} builtin skills")

    skill_executor = SkillExecutor(
        registry=skill_registry,
        marketplace=skill_marketplace,
        installer=skill_installer,
        auto_install=skill_config.get('auto_install', True)
    )

    # Create auto-skill manager
    auto_skill_config = skill_config.get('auto_skill', {})
    auto_skill_enabled = auto_skill_config.get('enabled', True)

    auto_skill_manager = None
    if auto_skill_enabled:
        logger.info("Initializing auto-skill system (local-only mode)...")
        auto_skill_manager = AutoSkillManager(
            auto_install=False,
            auto_load=auto_skill_config.get('auto_load', True)
        )
        await auto_skill_manager.initialize()
        skill_count = len(auto_skill_manager.matcher.skills_cache)
        logger.info(f"Auto-skill system ready ({skill_count} local skills)")

    # Create chat handler
    chat_handler = ChatHandler(
        engine=engine,
        llm_service=llm_service,
        tool_registry=tool_registry,
        skill_executor=skill_executor,
        auto_skill_manager=auto_skill_manager
    )
    set_chat_handler(chat_handler)

    # Start engine in background
    engine_task = asyncio.create_task(engine.run())

    logger.info("Alpha API Server started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Alpha API Server...")
    await engine.shutdown()
    try:
        await asyncio.wait_for(engine_task, timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("Engine task did not complete in time")
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
    app.include_router(websocket.router, prefix="/api/v1", tags=["chat"])
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
