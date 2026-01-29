"""
Tests for Alpha Task Scheduler
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from alpha.scheduler.cron import CronSchedule, CronParser, CronParseError, CommonCronExpressions
from alpha.scheduler.storage import ScheduleStorage
from alpha.scheduler.scheduler import (
    TaskScheduler,
    ScheduleType,
    ScheduleConfig,
    TaskSpec,
    Schedule
)
from alpha.scheduler.triggers import (
    TriggerManager,
    TimeTrigger,
    IntervalTrigger,
    ConditionTrigger,
    TriggerConfig
)


class TestCronSchedule:
    """Test cron expression parsing and evaluation."""

    def test_parse_all_wildcards(self):
        """Test parsing * * * * *"""
        cron = CronSchedule("* * * * *")
        assert len(cron.parts["minute"]) == 60
        assert len(cron.parts["hour"]) == 24
        assert len(cron.parts["day"]) == 31
        assert len(cron.parts["month"]) == 12
        assert len(cron.parts["weekday"]) == 7

    def test_parse_specific_values(self):
        """Test parsing specific values"""
        cron = CronSchedule("30 9 1 1 1")
        assert cron.parts["minute"] == {30}
        assert cron.parts["hour"] == {9}
        assert cron.parts["day"] == {1}
        assert cron.parts["month"] == {1}
        assert cron.parts["weekday"] == {1}

    def test_parse_step_values(self):
        """Test parsing step values (*/N)"""
        cron = CronSchedule("*/15 * * * *")
        assert cron.parts["minute"] == {0, 15, 30, 45}

    def test_parse_range_values(self):
        """Test parsing range values (N-M)"""
        cron = CronSchedule("0 9-17 * * *")
        assert cron.parts["hour"] == {9, 10, 11, 12, 13, 14, 15, 16, 17}

    def test_parse_list_values(self):
        """Test parsing list values (N,M,O)"""
        cron = CronSchedule("0 9,12,15,18 * * *")
        assert cron.parts["hour"] == {9, 12, 15, 18}

    def test_invalid_expression(self):
        """Test invalid cron expressions"""
        with pytest.raises(CronParseError):
            CronSchedule("* * *")  # Too few parts

        with pytest.raises(CronParseError):
            CronSchedule("60 * * * *")  # Invalid minute

        with pytest.raises(CronParseError):
            CronSchedule("* 25 * * *")  # Invalid hour

    def test_matches(self):
        """Test datetime matching"""
        cron = CronSchedule("30 9 * * *")

        # Should match
        dt = datetime(2026, 1, 29, 9, 30, 0)
        assert cron.matches(dt)

        # Should not match (wrong minute)
        dt = datetime(2026, 1, 29, 9, 31, 0)
        assert not cron.matches(dt)

        # Should not match (wrong hour)
        dt = datetime(2026, 1, 29, 10, 30, 0)
        assert not cron.matches(dt)

    def test_next_run_time(self):
        """Test calculating next run time"""
        cron = CronSchedule("0 9 * * *")  # Daily at 9:00 AM

        # Before 9 AM - should return today at 9 AM
        now = datetime(2026, 1, 29, 8, 0, 0)
        next_run = cron.next_run_time(now)
        assert next_run.hour == 9
        assert next_run.minute == 0
        assert next_run.day == 29

        # After 9 AM - should return tomorrow at 9 AM
        now = datetime(2026, 1, 29, 10, 0, 0)
        next_run = cron.next_run_time(now)
        assert next_run.hour == 9
        assert next_run.minute == 0
        assert next_run.day == 30

    def test_common_expressions(self):
        """Test common cron expressions"""
        # Every minute
        cron = CronSchedule(CommonCronExpressions.EVERY_MINUTE)
        assert len(cron.parts["minute"]) == 60

        # Every hour
        cron = CronSchedule(CommonCronExpressions.EVERY_HOUR)
        assert cron.parts["minute"] == {0}

        # Daily at midnight
        cron = CronSchedule(CommonCronExpressions.DAILY_MIDNIGHT)
        assert cron.parts["hour"] == {0}
        assert cron.parts["minute"] == {0}

    def test_cron_parser(self):
        """Test CronParser utility"""
        # Validate
        assert CronParser.validate("0 9 * * *")
        assert not CronParser.validate("invalid")

        # Describe
        desc = CronParser.describe("0 9 * * *")
        assert "9" in desc


class TestScheduleStorage:
    """Test schedule storage."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def storage(self, temp_db):
        """Create storage instance."""
        storage = ScheduleStorage(temp_db)
        storage.initialize()
        yield storage
        storage.close()

    def test_add_schedule(self, storage):
        """Test adding a schedule."""
        schedule_data = {
            "id": "test-123",
            "task_name": "Test Task",
            "task_description": "Test description",
            "schedule_type": "cron",
            "schedule_config": {"cron": "0 9 * * *"},
            "enabled": True
        }

        schedule_id = storage.add_schedule(schedule_data)
        assert schedule_id == "test-123"

        # Retrieve and verify
        retrieved = storage.get_schedule(schedule_id)
        assert retrieved["task_name"] == "Test Task"
        assert retrieved["schedule_type"] == "cron"

    def test_list_schedules(self, storage):
        """Test listing schedules."""
        # Add multiple schedules
        for i in range(5):
            storage.add_schedule({
                "id": f"test-{i}",
                "task_name": f"Task {i}",
                "schedule_type": "cron",
                "enabled": i % 2 == 0  # Alternate enabled/disabled
            })

        # List all
        all_schedules = storage.list_schedules()
        assert len(all_schedules) == 5

        # List enabled only
        enabled = storage.list_schedules(enabled=True)
        assert len(enabled) == 3

    def test_update_schedule(self, storage):
        """Test updating schedule."""
        schedule_data = {
            "id": "test-123",
            "task_name": "Original Task",
            "schedule_type": "cron"
        }
        storage.add_schedule(schedule_data)

        # Update
        updated = storage.update_schedule("test-123", {
            "task_name": "Updated Task",
            "run_count": 5
        })
        assert updated

        # Verify
        retrieved = storage.get_schedule("test-123")
        assert retrieved["task_name"] == "Updated Task"
        assert retrieved["run_count"] == 5

    def test_delete_schedule(self, storage):
        """Test deleting schedule."""
        storage.add_schedule({
            "id": "test-123",
            "task_name": "Test Task",
            "schedule_type": "cron"
        })

        deleted = storage.delete_schedule("test-123")
        assert deleted

        # Verify deleted
        retrieved = storage.get_schedule("test-123")
        assert retrieved is None

    def test_run_history(self, storage):
        """Test schedule run history."""
        storage.add_schedule({
            "id": "test-123",
            "task_name": "Test Task",
            "schedule_type": "cron"
        })

        # Add run history
        run_data = {
            "id": "run-1",
            "schedule_id": "test-123",
            "started_at": datetime.now().isoformat(),
            "status": "completed",
            "result": {"success": True}
        }
        storage.add_run_history(run_data)

        # Get history
        history = storage.get_run_history("test-123")
        assert len(history) == 1
        assert history[0]["status"] == "completed"

    def test_statistics(self, storage):
        """Test getting statistics."""
        # Add some schedules
        for i in range(3):
            storage.add_schedule({
                "id": f"test-{i}",
                "task_name": f"Task {i}",
                "schedule_type": "cron" if i < 2 else "interval"
            })

        stats = storage.get_statistics()
        assert stats["total_schedules"] == 3
        assert stats["by_type"]["cron"] == 2
        assert stats["by_type"]["interval"] == 1


@pytest.mark.asyncio
class TestTaskScheduler:
    """Test task scheduler."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest_asyncio.fixture
    async def scheduler(self, temp_db):
        """Create scheduler instance."""
        storage = ScheduleStorage(temp_db)
        scheduler = TaskScheduler(storage, check_interval=1)
        await scheduler.initialize()
        yield scheduler
        storage.close()

    async def test_schedule_cron_task(self, scheduler):
        """Test scheduling a cron-based task."""
        task_spec = TaskSpec(
            name="Daily Report",
            description="Generate daily report",
            executor="generate_report"
        )

        schedule_config = ScheduleConfig(
            type=ScheduleType.CRON,
            cron="0 9 * * *"
        )

        schedule_id = await scheduler.schedule_task(task_spec, schedule_config)
        assert schedule_id

        # Verify schedule was created
        schedule = scheduler.get_schedule(schedule_id)
        assert schedule is not None
        assert schedule.task_spec.name == "Daily Report"
        assert schedule.next_run is not None

    async def test_schedule_interval_task(self, scheduler):
        """Test scheduling an interval-based task."""
        task_spec = TaskSpec(
            name="Health Check",
            description="Check system health",
            executor="health_check"
        )

        schedule_config = ScheduleConfig(
            type=ScheduleType.INTERVAL,
            interval=300  # 5 minutes
        )

        schedule_id = await scheduler.schedule_task(task_spec, schedule_config)
        schedule = scheduler.get_schedule(schedule_id)

        assert schedule.next_run is not None
        # Next run should be ~5 minutes from now
        delta = (schedule.next_run - datetime.now()).total_seconds()
        assert 290 < delta < 310

    async def test_schedule_one_time_task(self, scheduler):
        """Test scheduling a one-time task."""
        future_time = datetime.now() + timedelta(hours=1)

        task_spec = TaskSpec(
            name="One Time Task",
            description="Runs once",
            executor="one_time_job"
        )

        schedule_config = ScheduleConfig(
            type=ScheduleType.ONE_TIME,
            run_at=future_time.isoformat()
        )

        schedule_id = await scheduler.schedule_task(task_spec, schedule_config)
        schedule = scheduler.get_schedule(schedule_id)

        assert schedule.next_run == future_time

    async def test_execute_due_task(self, scheduler):
        """Test executing a due task."""
        executed = []

        async def test_executor(task_spec):
            executed.append(task_spec.name)
            return {"success": True}

        scheduler.register_executor("test_executor", test_executor)

        # Schedule task that's due now
        past_time = datetime.now() - timedelta(minutes=1)

        task_spec = TaskSpec(
            name="Test Task",
            description="Test",
            executor="test_executor"
        )

        schedule_config = ScheduleConfig(
            type=ScheduleType.ONE_TIME,
            run_at=past_time.isoformat()
        )

        schedule_id = await scheduler.schedule_task(task_spec, schedule_config)

        # Check for due tasks
        await scheduler.check_due_tasks()

        # Verify task was executed
        assert "Test Task" in executed

        # Verify schedule was updated
        schedule = scheduler.get_schedule(schedule_id)
        assert schedule.run_count == 1
        assert schedule.last_run is not None

    async def test_cancel_schedule(self, scheduler):
        """Test canceling a schedule."""
        task_spec = TaskSpec(
            name="Cancellable Task",
            description="Can be cancelled",
            executor="test"
        )

        schedule_config = ScheduleConfig(
            type=ScheduleType.CRON,
            cron="0 9 * * *"
        )

        schedule_id = await scheduler.schedule_task(task_spec, schedule_config)

        # Cancel schedule
        cancelled = await scheduler.cancel_schedule(schedule_id)
        assert cancelled

        # Verify it's disabled
        schedule = scheduler.get_schedule(schedule_id)
        assert not schedule.enabled

    async def test_list_schedules(self, scheduler):
        """Test listing schedules."""
        # Create multiple schedules
        for i in range(3):
            task_spec = TaskSpec(
                name=f"Task {i}",
                description=f"Description {i}",
                executor="test"
            )

            schedule_config = ScheduleConfig(
                type=ScheduleType.CRON,
                cron="0 9 * * *"
            )

            await scheduler.schedule_task(task_spec, schedule_config)

        # List all
        schedules = scheduler.list_schedules()
        assert len(schedules) == 3

        # Cancel one
        await scheduler.cancel_schedule(schedules[0].id)

        # List enabled only
        enabled = scheduler.list_schedules(enabled=True)
        assert len(enabled) == 2


@pytest.mark.asyncio
class TestTriggers:
    """Test trigger system."""

    async def test_time_trigger(self):
        """Test time-based trigger."""
        triggered = []

        async def on_trigger(trigger):
            triggered.append(trigger.config.name)

        config = TriggerConfig(
            trigger_id="test-1",
            name="Test Time Trigger",
            description="Test"
        )

        # Trigger time in the past
        trigger_time = datetime.now() - timedelta(seconds=1)

        trigger = TimeTrigger(config, trigger_time, on_trigger)

        # Should fire
        should_fire = await trigger.check()
        assert should_fire

        await trigger.on_trigger()
        assert "Test Time Trigger" in triggered

        # Should not fire again
        should_fire = await trigger.check()
        assert not should_fire

    async def test_interval_trigger(self):
        """Test interval-based trigger."""
        triggered = []

        async def on_trigger(trigger):
            triggered.append(datetime.now())

        config = TriggerConfig(
            trigger_id="test-2",
            name="Test Interval Trigger",
            description="Test"
        )

        # 1 second interval
        trigger = IntervalTrigger(config, interval=1, on_trigger_callback=on_trigger)

        # First check should fire
        should_fire = await trigger.check()
        assert should_fire

        await trigger.on_trigger()
        assert len(triggered) == 1

        # Immediate check should not fire
        should_fire = await trigger.check()
        assert not should_fire

        # After 1 second should fire again
        await asyncio.sleep(1.1)
        should_fire = await trigger.check()
        assert should_fire

    async def test_condition_trigger(self):
        """Test condition-based trigger."""
        triggered = []
        condition_state = False

        def condition_func():
            return condition_state

        async def on_trigger(trigger):
            triggered.append(trigger.config.name)

        config = TriggerConfig(
            trigger_id="test-3",
            name="Test Condition Trigger",
            description="Test"
        )

        trigger = ConditionTrigger(config, condition_func, on_trigger)

        # Condition False - should not fire
        should_fire = await trigger.check()
        assert not should_fire

        # Change condition to True - should fire
        condition_state = True
        should_fire = await trigger.check()
        assert should_fire

        await trigger.on_trigger()
        assert len(triggered) == 1

        # Condition still True - should not fire again (edge trigger)
        should_fire = await trigger.check()
        assert not should_fire

    async def test_trigger_manager(self):
        """Test trigger manager."""
        manager = TriggerManager(check_interval=1)

        triggered = []

        async def on_trigger(trigger):
            triggered.append(trigger.config.name)

        # Register trigger
        config = TriggerConfig(
            trigger_id="test-1",
            name="Test Trigger",
            description="Test"
        )

        trigger_time = datetime.now() - timedelta(seconds=1)
        trigger = TimeTrigger(config, trigger_time, on_trigger)

        trigger_id = manager.register_trigger(trigger)
        assert trigger_id == "test-1"

        # Check triggers
        fired = await manager.check_triggers()
        assert "test-1" in fired
        assert len(triggered) == 1

        # List triggers
        triggers = manager.list_triggers()
        assert len(triggers) == 1

        # Disable trigger
        manager.disable_trigger(trigger_id)
        trigger = manager.get_trigger(trigger_id)
        assert not trigger.enabled

        # Unregister trigger
        unregistered = manager.unregister_trigger(trigger_id)
        assert unregistered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
