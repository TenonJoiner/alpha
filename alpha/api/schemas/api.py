"""
API Schemas - Request and Response Models
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskRequest(BaseModel):
    """Request to create a new task"""
    prompt: str = Field(..., description="Task prompt/instruction", min_length=1)
    priority: int = Field(default=5, description="Task priority (1-10)", ge=1, le=10)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    timeout: Optional[int] = Field(default=None, description="Max execution time in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Search for latest AI news and summarize",
                "priority": 7,
                "context": {"sources": ["TechCrunch", "VentureBeat"]},
                "timeout": 300
            }
        }


class TaskResponse(BaseModel):
    """Response for task operations"""
    task_id: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskListResponse(BaseModel):
    """List of tasks"""
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int


class StatusResponse(BaseModel):
    """System status response"""
    status: str
    uptime: float
    version: str
    tasks_total: int
    tasks_running: int
    tasks_completed: int
    tasks_failed: int
    memory_usage_mb: float
    cpu_percent: float


class ConfigUpdateRequest(BaseModel):
    """Request to update configuration"""
    config: Dict[str, Any]


class ConfigResponse(BaseModel):
    """Configuration response"""
    config: Dict[str, Any]
    updated_at: datetime


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    healthy: bool
    timestamp: datetime
    checks: Dict[str, bool]
