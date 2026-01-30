"""
Task Management API Routes
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from ..schemas import (
    TaskRequest,
    TaskResponse,
    TaskListResponse,
    TaskStatus,
    ErrorResponse
)
from ..server import get_engine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task_request: TaskRequest):
    """
    Create and submit a new task.

    Args:
        task_request: Task creation request

    Returns:
        Created task response
    """
    try:
        engine = get_engine()

        # Create task
        task_id = await engine.task_manager.create_task(
            prompt=task_request.prompt,
            priority=task_request.priority,
            context=task_request.context or {}
        )

        # Execute task asynchronously
        asyncio.create_task(engine.execute_task(task_id))

        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            metadata={"priority": task_request.priority}
        )

    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """
    Get task status and result.

    Args:
        task_id: Task ID

    Returns:
        Task response
    """
    try:
        engine = get_engine()
        task = await engine.task_manager.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return TaskResponse(
            task_id=task.id,
            status=TaskStatus(task.status),
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            result=task.result,
            error=str(task.error) if task.error else None,
            metadata=task.metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    limit: int = Query(default=50, le=100, description="Max results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination")
):
    """
    List all tasks with optional filtering.

    Args:
        status: Filter by task status
        limit: Maximum number of results
        offset: Pagination offset

    Returns:
        List of tasks
    """
    try:
        engine = get_engine()
        tasks = await engine.task_manager.list_tasks(
            status=status.value if status else None,
            limit=limit,
            offset=offset
        )

        task_responses = [
            TaskResponse(
                task_id=task.id,
                status=TaskStatus(task.status),
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                result=task.result,
                error=str(task.error) if task.error else None
            )
            for task in tasks
        ]

        return TaskListResponse(
            tasks=task_responses,
            total=len(task_responses),
            page=offset // limit,
            page_size=limit
        )

    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}", status_code=204)
async def cancel_task(task_id: str):
    """
    Cancel a running task.

    Args:
        task_id: Task ID
    """
    try:
        engine = get_engine()
        success = await engine.task_manager.cancel_task(task_id)

        if not success:
            raise HTTPException(status_code=404, detail="Task not found or already completed")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


import asyncio
