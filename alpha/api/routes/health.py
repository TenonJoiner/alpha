"""
Health Check API Routes
"""

import logging
from fastapi import APIRouter
from datetime import datetime

from ..schemas import HealthResponse
from ..server import get_engine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring.

    Returns:
        Health status
    """
    checks = {
        "api": True,
        "engine": False,
        "database": False,
        "llm": False
    }

    try:
        engine = get_engine()
        checks["engine"] = True

        # Check database
        try:
            await engine.memory_manager.ping()
            checks["database"] = True
        except:
            pass

        # Check LLM
        try:
            await engine.llm_service.ping()
            checks["llm"] = True
        except:
            pass

    except:
        pass

    healthy = all(checks.values())

    return HealthResponse(
        healthy=healthy,
        timestamp=datetime.now(),
        checks=checks
    )
