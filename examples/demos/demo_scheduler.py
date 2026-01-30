#!/usr/bin/env python3
"""
Alpha Task Scheduler Demo

Demonstrates the task scheduling capabilities.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from alpha.scheduler import (
    TaskScheduler,
    ScheduleType,
    ScheduleConfig,
    TaskSpec,
    ScheduleStorage,
)


async def sample_task(task_spec: TaskSpec):
    """Sample task executor."""
    print(f"  ⚡ Executing: {task_spec.name}")
    print(f"     Description: {task_spec.description}")
    print(f"     Parameters: {task_spec.params}")

    # Simulate some work
    await asyncio.sleep(1)

    result = {
        "status": "success",
        "message": f"Task '{task_spec.name}' completed",
        "timestamp": datetime.now().isoformat()
    }

    print(f"  ✅ Completed: {task_spec.name}")
    return result


async def demo_cron_schedule(scheduler: TaskScheduler):
    """Demo: Cron-based scheduling."""
    print("\n" + "="*70)
    print("📅 Demo 1: Cron-based Scheduling")
    print("="*70)

    # Schedule a task to run every minute
    task_spec = TaskSpec(
        name="Minute Report",
        description="Runs every minute",
        executor="sample_task",
        params={"report_type": "minute"}
    )

    schedule_config = ScheduleConfig(
        type=ScheduleType.CRON,
        cron="* * * * *",  # Every minute
        max_runs=3  # Run only 3 times for demo
    )

    schedule_id = await scheduler.schedule_task(task_spec, schedule_config)
    schedule = scheduler.get_schedule(schedule_id)

    print(f"✅ Scheduled: {task_spec.name}")
    print(f"   Schedule ID: {schedule_id}")
    print(f"   Cron: {schedule_config.cron}")
    print(f"   Next run: {schedule.next_run}")
    print(f"   Max runs: {schedule_config.max_runs}")

    return schedule_id


async def demo_interval_schedule(scheduler: TaskScheduler):
    """Demo: Interval-based scheduling."""
    print("\n" + "="*70)
    print("⏱️  Demo 2: Interval-based Scheduling")
    print("="*70)

    # Schedule a task to run every 30 seconds
    task_spec = TaskSpec(
        name="Health Check",
        description="Periodic system health check",
        executor="sample_task",
        params={"check_type": "health"}
    )

    schedule_config = ScheduleConfig(
        type=ScheduleType.INTERVAL,
        interval=30,  # 30 seconds
        max_runs=2
    )

    schedule_id = await scheduler.schedule_task(task_spec, schedule_config)
    schedule = scheduler.get_schedule(schedule_id)

    print(f"✅ Scheduled: {task_spec.name}")
    print(f"   Schedule ID: {schedule_id}")
    print(f"   Interval: {schedule_config.interval} seconds")
    print(f"   Next run: {schedule.next_run}")

    return schedule_id


async def demo_one_time_schedule(scheduler: TaskScheduler):
    """Demo: One-time scheduled task."""
    print("\n" + "="*70)
    print("🎯 Demo 3: One-time Scheduled Task")
    print("="*70)

    # Schedule a task to run 5 seconds from now
    run_time = datetime.now() + timedelta(seconds=5)

    task_spec = TaskSpec(
        name="Backup Task",
        description="One-time backup operation",
        executor="sample_task",
        params={"backup_type": "full"}
    )

    schedule_config = ScheduleConfig(
        type=ScheduleType.ONE_TIME,
        run_at=run_time.isoformat()
    )

    schedule_id = await scheduler.schedule_task(task_spec, schedule_config)
    schedule = scheduler.get_schedule(schedule_id)

    print(f"✅ Scheduled: {task_spec.name}")
    print(f"   Schedule ID: {schedule_id}")
    print(f"   Run at: {schedule.next_run}")
    print(f"   Countdown: 5 seconds")

    return schedule_id


async def demo_daily_schedule(scheduler: TaskScheduler):
    """Demo: Daily scheduled task."""
    print("\n" + "="*70)
    print("📆 Demo 4: Daily Scheduled Task")
    print("="*70)

    task_spec = TaskSpec(
        name="Daily Summary",
        description="Generate daily summary report",
        executor="sample_task",
        params={"report_type": "daily"}
    )

    schedule_config = ScheduleConfig(
        type=ScheduleType.DAILY,
        time="09:00"  # 9:00 AM every day
    )

    schedule_id = await scheduler.schedule_task(task_spec, schedule_config)
    schedule = scheduler.get_schedule(schedule_id)

    print(f"✅ Scheduled: {task_spec.name}")
    print(f"   Schedule ID: {schedule_id}")
    print(f"   Time: {schedule_config.time} daily")
    print(f"   Next run: {schedule.next_run}")

    return schedule_id


async def monitor_execution(scheduler: TaskScheduler, duration: int):
    """Monitor task execution."""
    print("\n" + "="*70)
    print("🔍 Monitoring Task Execution")
    print("="*70)
    print(f"Running for {duration} seconds...\n")

    start_time = datetime.now()
    check_count = 0

    while (datetime.now() - start_time).total_seconds() < duration:
        # Check for due tasks
        executed = await scheduler.check_due_tasks()

        if executed:
            check_count += 1
            print(f"\n[Check #{check_count}] {datetime.now().strftime('%H:%M:%S')}")
            print(f"  Executed {len(executed)} task(s)")

            # Show statistics
            stats = scheduler.get_statistics()
            print(f"  Total runs: {stats['total_runs']}")
            print(f"  Success rate: {stats['success_rate']:.1%}")

        await asyncio.sleep(1)

    print(f"\n⏹️  Monitoring stopped after {duration} seconds")


async def show_final_statistics(scheduler: TaskScheduler):
    """Show final statistics."""
    print("\n" + "="*70)
    print("📊 Final Statistics")
    print("="*70)

    stats = scheduler.get_statistics()

    print(f"\nSchedules:")
    print(f"  Total: {stats['total_schedules']}")
    print(f"  Enabled: {stats['enabled_schedules']}")
    print(f"  By type:")
    for stype, count in stats['by_type'].items():
        print(f"    - {stype}: {count}")

    print(f"\nExecution:")
    print(f"  Total runs: {stats['total_runs']}")
    print(f"  Successful: {stats['successful_runs']}")
    print(f"  Success rate: {stats['success_rate']:.1%}")

    # List all schedules
    print(f"\n📋 All Schedules:")
    schedules = scheduler.list_schedules()
    for schedule in schedules:
        status = "🟢" if schedule.enabled else "🔴"
        print(f"\n  {status} {schedule.task_spec.name}")
        print(f"     ID: {schedule.id}")
        print(f"     Type: {schedule.schedule_config.type.value}")
        print(f"     Run count: {schedule.run_count}")
        print(f"     Last run: {schedule.last_run or 'Never'}")
        print(f"     Next run: {schedule.next_run or 'N/A'}")


async def main():
    """Main demo function."""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "        Alpha Task Scheduler - Interactive Demo".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")

    # Initialize scheduler
    print("\n🚀 Initializing scheduler...")
    storage = ScheduleStorage("data/demo_scheduler.db")
    scheduler = TaskScheduler(storage, check_interval=1)
    await scheduler.initialize()

    # Register task executor
    scheduler.register_executor("sample_task", sample_task)
    print("✅ Scheduler initialized\n")

    try:
        # Run demos
        await demo_cron_schedule(scheduler)
        await demo_interval_schedule(scheduler)
        await demo_one_time_schedule(scheduler)
        await demo_daily_schedule(scheduler)

        # Monitor execution for 70 seconds
        # This will catch:
        # - One-time task after 5 seconds
        # - Interval task after 30 seconds and 60 seconds
        # - Cron task at next minute boundary (up to 3 times)
        await monitor_execution(scheduler, duration=70)

        # Show final statistics
        await show_final_statistics(scheduler)

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")

    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await scheduler.stop()
        storage.close()
        print("✅ Cleanup complete")

    print("\n" + "="*70)
    print("✨ Demo completed!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
