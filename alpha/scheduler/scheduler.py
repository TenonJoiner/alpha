"""
Alpha - Task Scheduler

Main task scheduler implementing cron-based and interval-based scheduling.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

from alpha.scheduler.cron import CronSchedule, CronParseError
from alpha.scheduler.storage import ScheduleStorage


logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Schedule type enumeration."""
    CRON = "cron"           # Cron expression
    INTERVAL = "interval"   # Fixed interval
    ONE_TIME = "one_time"   # Single execution
    DAILY = "daily"         # Daily at specific time
    WEEKLY = "weekly"       # Weekly on specific day/time


@dataclass
class ScheduleConfig:
    """
    Schedule configuration.

    Examples:
        # Cron-based
        ScheduleConfig(type=ScheduleType.CRON, cron="0 9 * * *")

        # Interval-based (every 30 minutes)
        ScheduleConfig(type=ScheduleType.INTERVAL, interval=1800)

        # One-time execution
        ScheduleConfig(type=ScheduleType.ONE_TIME, run_at="2026-01-30T10:00:00")

        # Daily at 9:00 AM
        ScheduleConfig(type=ScheduleType.DAILY, time="09:00")

        # Weekly on Monday at 9:00 AM
        ScheduleConfig(type=ScheduleType.WEEKLY, weekday=1, time="09:00")
    """
    type: ScheduleType
    cron: Optional[str] = None              # For CRON type
    interval: Optional[int] = None          # For INTERVAL type (seconds)
    run_at: Optional[str] = None            # For ONE_TIME type (ISO datetime)
    time: Optional[str] = None              # For DAILY/WEEKLY (HH:MM format)
    weekday: Optional[int] = None           # For WEEKLY (0=Monday, 6=Sunday)
    timezone: str = "UTC"                    # Timezone
    max_runs: Optional[int] = None          # Max number of runs (None = unlimited)


@dataclass
class TaskSpec:
    """
    Task specification for scheduled execution.
    """
    name: str
    description: str
    executor: str  # Function name or identifier to execute
    params: Dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"  # low, normal, high, critical
    timeout: Optional[int] = None  # Execution timeout in seconds


@dataclass
class Schedule:
    """
    Schedule representation.
    """
    id: str
    task_spec: TaskSpec
    schedule_config: ScheduleConfig
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskScheduler:
    """
    Main task scheduler.

    Features:
    - Cron-based scheduling
    - Interval-based scheduling
    - One-time scheduled tasks
    - Task persistence
    - Execution history tracking
    """

    def __init__(
        self,
        storage: ScheduleStorage,
        check_interval: int = 60
    ):
        """
        Initialize task scheduler.

        Args:
            storage: Schedule storage instance
            check_interval: How often to check for due tasks (seconds)
        """
        self.storage = storage
        self.check_interval = check_interval
        self.schedules: Dict[str, Schedule] = {}
        self.running = False
        self.executor_registry: Dict[str, Callable] = {}

    async def initialize(self):
        """Initialize scheduler and load persisted schedules."""
        self.storage.initialize()

        # Load schedules from storage
        stored_schedules = self.storage.list_schedules()
        for schedule_data in stored_schedules:
            try:
                schedule = self._schedule_from_dict(schedule_data)
                self.schedules[schedule.id] = schedule
                logger.info(f"Loaded schedule: {schedule.id} - {schedule.task_spec.name}")
            except Exception as e:
                logger.error(f"Failed to load schedule {schedule_data['id']}: {e}")

        logger.info(f"Task scheduler initialized with {len(self.schedules)} schedules")

    def register_executor(self, name: str, func: Callable):
        """
        Register task executor function.

        Args:
            name: Executor name
            func: Async function to execute tasks
        """
        self.executor_registry[name] = func
        logger.info(f"Registered executor: {name}")

    async def schedule_task(
        self,
        task_spec: TaskSpec,
        schedule_config: ScheduleConfig
    ) -> str:
        """
        Schedule a new task.

        Args:
            task_spec: Task specification
            schedule_config: Schedule configuration

        Returns:
            Schedule ID

        Raises:
            ValueError: If schedule configuration is invalid
        """
        # Validate schedule config
        self._validate_schedule_config(schedule_config)

        # Create schedule
        schedule = Schedule(
            id=str(uuid.uuid4()),
            task_spec=task_spec,
            schedule_config=schedule_config,
            next_run=self._calculate_next_run(schedule_config, None)
        )

        # Store schedule
        self.schedules[schedule.id] = schedule
        self.storage.add_schedule(self._schedule_to_dict(schedule))

        logger.info(
            f"Scheduled task: {schedule.id} - {task_spec.name}, "
            f"next run: {schedule.next_run}"
        )

        return schedule.id

    def _validate_schedule_config(self, config: ScheduleConfig):
        """Validate schedule configuration."""
        if config.type == ScheduleType.CRON:
            if not config.cron:
                raise ValueError("Cron expression required for CRON type")
            try:
                CronSchedule(config.cron)
            except CronParseError as e:
                raise ValueError(f"Invalid cron expression: {e}")

        elif config.type == ScheduleType.INTERVAL:
            if not config.interval or config.interval <= 0:
                raise ValueError("Positive interval required for INTERVAL type")

        elif config.type == ScheduleType.ONE_TIME:
            if not config.run_at:
                raise ValueError("run_at required for ONE_TIME type")
            try:
                datetime.fromisoformat(config.run_at)
            except ValueError:
                raise ValueError("run_at must be ISO format datetime")

        elif config.type in [ScheduleType.DAILY, ScheduleType.WEEKLY]:
            if not config.time:
                raise ValueError("time required for DAILY/WEEKLY type")
            if config.type == ScheduleType.WEEKLY and config.weekday is None:
                raise ValueError("weekday required for WEEKLY type")

    def _calculate_next_run(
        self,
        config: ScheduleConfig,
        after: Optional[datetime]
    ) -> datetime:
        """Calculate next run time based on schedule config."""
        if after is None:
            after = datetime.now()

        if config.type == ScheduleType.CRON:
            cron = CronSchedule(config.cron)
            return cron.next_run_time(after)

        elif config.type == ScheduleType.INTERVAL:
            return after + timedelta(seconds=config.interval)

        elif config.type == ScheduleType.ONE_TIME:
            return datetime.fromisoformat(config.run_at)

        elif config.type == ScheduleType.DAILY:
            # Parse time
            hour, minute = map(int, config.time.split(":"))
            next_run = after.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # If time already passed today, schedule for tomorrow
            if next_run <= after:
                next_run += timedelta(days=1)

            return next_run

        elif config.type == ScheduleType.WEEKLY:
            # Parse time
            hour, minute = map(int, config.time.split(":"))

            # Calculate days until target weekday
            days_ahead = config.weekday - after.weekday()
            if days_ahead <= 0:
                days_ahead += 7

            next_run = after + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)

            return next_run

        raise ValueError(f"Unknown schedule type: {config.type}")

    async def check_due_tasks(self) -> List[str]:
        """
        Check for tasks that are due to run and execute them.

        Returns:
            List of task IDs that were executed
        """
        now = datetime.now()
        executed_task_ids = []

        for schedule in list(self.schedules.values()):
            if not schedule.enabled:
                continue

            if schedule.next_run and schedule.next_run <= now:
                try:
                    # Execute task
                    await self._execute_scheduled_task(schedule)
                    executed_task_ids.append(schedule.id)

                    # Update schedule
                    schedule.last_run = now
                    schedule.run_count += 1

                    # Check if max runs reached
                    if (schedule.schedule_config.max_runs and
                        schedule.run_count >= schedule.schedule_config.max_runs):
                        schedule.enabled = False
                        schedule.next_run = None
                        logger.info(f"Schedule {schedule.id} reached max runs, disabled")
                    else:
                        # Calculate next run
                        if schedule.schedule_config.type == ScheduleType.ONE_TIME:
                            schedule.enabled = False
                            schedule.next_run = None
                        else:
                            schedule.next_run = self._calculate_next_run(
                                schedule.schedule_config,
                                now
                            )

                    # Persist updates
                    self.storage.update_schedule(schedule.id, {
                        "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
                        "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
                        "run_count": schedule.run_count,
                        "enabled": schedule.enabled
                    })

                except Exception as e:
                    logger.error(f"Failed to execute schedule {schedule.id}: {e}", exc_info=True)

        return executed_task_ids

    async def _execute_scheduled_task(self, schedule: Schedule):
        """Execute a scheduled task."""
        task_spec = schedule.task_spec
        run_id = str(uuid.uuid4())

        logger.info(f"Executing scheduled task: {task_spec.name} (schedule: {schedule.id})")

        started_at = datetime.now()
        run_data = {
            "id": run_id,
            "schedule_id": schedule.id,
            "started_at": started_at.isoformat(),
            "status": "running"
        }

        try:
            # Get executor function
            executor = self.executor_registry.get(task_spec.executor)
            if not executor:
                raise ValueError(f"Executor not found: {task_spec.executor}")

            # Execute with timeout if specified
            if task_spec.timeout:
                result = await asyncio.wait_for(
                    executor(task_spec),
                    timeout=task_spec.timeout
                )
            else:
                result = await executor(task_spec)

            # Record success
            run_data.update({
                "completed_at": datetime.now().isoformat(),
                "status": "completed",
                "result": result
            })

            logger.info(f"Scheduled task completed: {task_spec.name}")

        except asyncio.TimeoutError:
            run_data.update({
                "completed_at": datetime.now().isoformat(),
                "status": "failed",
                "error": f"Task timeout after {task_spec.timeout}s"
            })
            logger.error(f"Scheduled task timed out: {task_spec.name}")

        except Exception as e:
            run_data.update({
                "completed_at": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e)
            })
            logger.error(f"Scheduled task failed: {task_spec.name} - {e}", exc_info=True)

        # Store run history
        self.storage.add_run_history(run_data)

    async def start(self):
        """Start scheduler main loop."""
        self.running = True
        logger.info("Task scheduler started")

        while self.running:
            try:
                await self.check_due_tasks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)

    async def stop(self):
        """Stop scheduler."""
        self.running = False
        logger.info("Task scheduler stopped")

    def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get schedule by ID."""
        return self.schedules.get(schedule_id)

    def list_schedules(
        self,
        enabled: Optional[bool] = None
    ) -> List[Schedule]:
        """List schedules with optional filtering."""
        schedules = list(self.schedules.values())

        if enabled is not None:
            schedules = [s for s in schedules if s.enabled == enabled]

        schedules.sort(key=lambda s: s.created_at, reverse=True)
        return schedules

    async def cancel_schedule(self, schedule_id: str) -> bool:
        """
        Cancel (disable) a schedule.

        Args:
            schedule_id: Schedule ID

        Returns:
            True if cancelled, False if not found
        """
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return False

        schedule.enabled = False
        self.storage.update_schedule(schedule_id, {"enabled": False})
        logger.info(f"Cancelled schedule: {schedule_id}")
        return True

    async def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete a schedule.

        Args:
            schedule_id: Schedule ID

        Returns:
            True if deleted, False if not found
        """
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            self.storage.delete_schedule(schedule_id)
            logger.info(f"Deleted schedule: {schedule_id}")
            return True
        return False

    def get_run_history(
        self,
        schedule_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get execution history for a schedule."""
        return self.storage.get_run_history(schedule_id, limit)

    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return self.storage.get_statistics()

    def _schedule_to_dict(self, schedule: Schedule) -> Dict[str, Any]:
        """Convert Schedule to dictionary for storage."""
        # Convert ScheduleConfig to dict with enum values
        schedule_config_dict = asdict(schedule.schedule_config)
        # Convert ScheduleType enum to string value
        schedule_config_dict['type'] = schedule.schedule_config.type.value

        return {
            "id": schedule.id,
            "task_name": schedule.task_spec.name,
            "task_description": schedule.task_spec.description,
            "task_params": {
                "executor": schedule.task_spec.executor,
                "params": schedule.task_spec.params,
                "priority": schedule.task_spec.priority,
                "timeout": schedule.task_spec.timeout
            },
            "schedule_type": schedule.schedule_config.type.value,
            "schedule_config": schedule_config_dict,
            "enabled": schedule.enabled,
            "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
            "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
            "run_count": schedule.run_count,
            "metadata": schedule.metadata
        }

    def _schedule_from_dict(self, data: Dict[str, Any]) -> Schedule:
        """Convert dictionary from storage to Schedule."""
        task_params = data.get("task_params", {})

        task_spec = TaskSpec(
            name=data["task_name"],
            description=data.get("task_description", ""),
            executor=task_params.get("executor", ""),
            params=task_params.get("params", {}),
            priority=task_params.get("priority", "normal"),
            timeout=task_params.get("timeout")
        )

        schedule_config_data = data.get("schedule_config", {})
        schedule_config = ScheduleConfig(
            type=ScheduleType(schedule_config_data.get("type", data["schedule_type"])),
            cron=schedule_config_data.get("cron"),
            interval=schedule_config_data.get("interval"),
            run_at=schedule_config_data.get("run_at"),
            time=schedule_config_data.get("time"),
            weekday=schedule_config_data.get("weekday"),
            timezone=schedule_config_data.get("timezone", "UTC"),
            max_runs=schedule_config_data.get("max_runs")
        )

        return Schedule(
            id=data["id"],
            task_spec=task_spec,
            schedule_config=schedule_config,
            enabled=data.get("enabled", True),
            last_run=datetime.fromisoformat(data["last_run"]) if data.get("last_run") else None,
            next_run=datetime.fromisoformat(data["next_run"]) if data.get("next_run") else None,
            run_count=data.get("run_count", 0),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            metadata=data.get("metadata", {})
        )
