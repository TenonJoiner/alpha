"""
System Status API Routes
"""

import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime

from ..schemas import StatusResponse
from ..server import get_engine, get_uptime, get_system_stats

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get system status and statistics.

    Returns:
        Status response with system metrics
    """
    try:
        engine = get_engine()
        stats = get_system_stats()

        # Get task statistics
        task_stats = await engine.task_manager.get_statistics()

        return StatusResponse(
            status="operational",
            uptime=get_uptime(),
            version="1.0.0",
            tasks_total=task_stats.get("total", 0),
            tasks_running=task_stats.get("running", 0),
            tasks_completed=task_stats.get("completed", 0),
            tasks_failed=task_stats.get("failed", 0),
            memory_usage_mb=stats["memory_mb"],
            cpu_percent=stats["cpu_percent"]
        )

    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
