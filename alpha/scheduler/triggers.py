"""
Alpha - Trigger System

Event-based and condition-based task triggers.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import uuid


logger = logging.getLogger(__name__)


@dataclass
class TriggerConfig:
    """Trigger configuration."""
    trigger_id: str
    name: str
    description: str
    enabled: bool = True
    metadata: Dict[str, Any] = None


class Trigger(ABC):
    """
    Abstract base class for triggers.

    Triggers monitor conditions and execute tasks when conditions are met.
    """

    def __init__(self, config: TriggerConfig):
        """
        Initialize trigger.

        Args:
            config: Trigger configuration
        """
        self.config = config
        self.enabled = config.enabled

    @abstractmethod
    async def check(self) -> bool:
        """
        Check if trigger condition is met.

        Returns:
            True if trigger should fire
        """
        pass

    @abstractmethod
    async def on_trigger(self):
        """
        Execute when trigger fires.

        Should create and submit tasks.
        """
        pass

    def enable(self):
        """Enable trigger."""
        self.enabled = True

    def disable(self):
        """Disable trigger."""
        self.enabled = False


class TimeTrigger(Trigger):
    """
    Time-based trigger.

    Fires at specific time or after interval.
    """

    def __init__(
        self,
        config: TriggerConfig,
        trigger_time: datetime,
        on_trigger_callback: Callable
    ):
        """
        Initialize time trigger.

        Args:
            config: Trigger configuration
            trigger_time: When to trigger
            on_trigger_callback: Function to call when triggered
        """
        super().__init__(config)
        self.trigger_time = trigger_time
        self.on_trigger_callback = on_trigger_callback
        self.triggered = False

    async def check(self) -> bool:
        """Check if current time passed trigger time."""
        if self.triggered or not self.enabled:
            return False

        return datetime.now() >= self.trigger_time

    async def on_trigger(self):
        """Execute trigger callback."""
        if self.on_trigger_callback:
            await self.on_trigger_callback(self)
        self.triggered = True
        logger.info(f"Time trigger fired: {self.config.name}")


class IntervalTrigger(Trigger):
    """
    Interval-based trigger.

    Fires repeatedly at fixed intervals.
    """

    def __init__(
        self,
        config: TriggerConfig,
        interval: int,
        on_trigger_callback: Callable
    ):
        """
        Initialize interval trigger.

        Args:
            config: Trigger configuration
            interval: Interval in seconds
            on_trigger_callback: Function to call when triggered
        """
        super().__init__(config)
        self.interval = interval
        self.on_trigger_callback = on_trigger_callback
        self.last_trigger: Optional[datetime] = None

    async def check(self) -> bool:
        """Check if interval elapsed since last trigger."""
        if not self.enabled:
            return False

        if self.last_trigger is None:
            return True

        elapsed = (datetime.now() - self.last_trigger).total_seconds()
        return elapsed >= self.interval

    async def on_trigger(self):
        """Execute trigger callback."""
        if self.on_trigger_callback:
            await self.on_trigger_callback(self)
        self.last_trigger = datetime.now()
        logger.info(f"Interval trigger fired: {self.config.name}")


class ConditionTrigger(Trigger):
    """
    Condition-based trigger.

    Fires when a custom condition evaluates to True.
    """

    def __init__(
        self,
        config: TriggerConfig,
        condition_func: Callable[[], bool],
        on_trigger_callback: Callable
    ):
        """
        Initialize condition trigger.

        Args:
            config: Trigger configuration
            condition_func: Function that returns True when condition met
            on_trigger_callback: Function to call when triggered
        """
        super().__init__(config)
        self.condition_func = condition_func
        self.on_trigger_callback = on_trigger_callback
        self.last_state = False

    async def check(self) -> bool:
        """Check if condition is met."""
        if not self.enabled:
            return False

        try:
            # Call condition function
            if asyncio.iscoroutinefunction(self.condition_func):
                current_state = await self.condition_func()
            else:
                current_state = self.condition_func()

            # Only trigger on state change from False to True
            should_trigger = current_state and not self.last_state
            self.last_state = current_state

            return should_trigger

        except Exception as e:
            logger.error(f"Error checking condition for {self.config.name}: {e}")
            return False

    async def on_trigger(self):
        """Execute trigger callback."""
        if self.on_trigger_callback:
            await self.on_trigger_callback(self)
        logger.info(f"Condition trigger fired: {self.config.name}")


class FileTrigger(Trigger):
    """
    File system trigger.

    Fires when file is created, modified, or deleted.
    This is a placeholder - full implementation would use watchdog library.
    """

    def __init__(
        self,
        config: TriggerConfig,
        path: str,
        event_type: str,
        on_trigger_callback: Callable
    ):
        """
        Initialize file trigger.

        Args:
            config: Trigger configuration
            path: File path to watch
            event_type: Event type (created, modified, deleted)
            on_trigger_callback: Function to call when triggered
        """
        super().__init__(config)
        self.path = path
        self.event_type = event_type
        self.on_trigger_callback = on_trigger_callback

    async def check(self) -> bool:
        """Check for file events."""
        # Placeholder - would use watchdog in full implementation
        return False

    async def on_trigger(self):
        """Execute trigger callback."""
        if self.on_trigger_callback:
            await self.on_trigger_callback(self)
        logger.info(f"File trigger fired: {self.config.name} ({self.path})")


class TriggerManager:
    """
    Manages and monitors triggers.

    Features:
    - Register multiple triggers
    - Continuous monitoring
    - Automatic trigger execution
    """

    def __init__(self, check_interval: int = 10):
        """
        Initialize trigger manager.

        Args:
            check_interval: How often to check triggers (seconds)
        """
        self.triggers: Dict[str, Trigger] = {}
        self.check_interval = check_interval
        self.running = False

    def register_trigger(self, trigger: Trigger) -> str:
        """
        Register a trigger.

        Args:
            trigger: Trigger instance

        Returns:
            Trigger ID
        """
        trigger_id = trigger.config.trigger_id
        self.triggers[trigger_id] = trigger
        logger.info(f"Registered trigger: {trigger_id} - {trigger.config.name}")
        return trigger_id

    def unregister_trigger(self, trigger_id: str) -> bool:
        """
        Unregister a trigger.

        Args:
            trigger_id: Trigger ID

        Returns:
            True if unregistered, False if not found
        """
        if trigger_id in self.triggers:
            del self.triggers[trigger_id]
            logger.info(f"Unregistered trigger: {trigger_id}")
            return True
        return False

    def get_trigger(self, trigger_id: str) -> Optional[Trigger]:
        """Get trigger by ID."""
        return self.triggers.get(trigger_id)

    def list_triggers(self, enabled: Optional[bool] = None) -> List[Trigger]:
        """
        List triggers with optional filtering.

        Args:
            enabled: Filter by enabled status

        Returns:
            List of triggers
        """
        triggers = list(self.triggers.values())

        if enabled is not None:
            triggers = [t for t in triggers if t.enabled == enabled]

        return triggers

    def enable_trigger(self, trigger_id: str) -> bool:
        """Enable a trigger."""
        trigger = self.triggers.get(trigger_id)
        if trigger:
            trigger.enable()
            logger.info(f"Enabled trigger: {trigger_id}")
            return True
        return False

    def disable_trigger(self, trigger_id: str) -> bool:
        """Disable a trigger."""
        trigger = self.triggers.get(trigger_id)
        if trigger:
            trigger.disable()
            logger.info(f"Disabled trigger: {trigger_id}")
            return True
        return False

    async def check_triggers(self) -> List[str]:
        """
        Check all triggers and execute those that fire.

        Returns:
            List of trigger IDs that fired
        """
        fired_triggers = []

        for trigger_id, trigger in list(self.triggers.items()):
            try:
                if await trigger.check():
                    await trigger.on_trigger()
                    fired_triggers.append(trigger_id)

            except Exception as e:
                logger.error(
                    f"Error checking/executing trigger {trigger_id}: {e}",
                    exc_info=True
                )

        return fired_triggers

    async def start(self):
        """Start trigger monitoring loop."""
        self.running = True
        logger.info("Trigger manager started")

        while self.running:
            try:
                await self.check_triggers()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in trigger loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)

    async def stop(self):
        """Stop trigger monitoring."""
        self.running = False
        logger.info("Trigger manager stopped")

    def get_statistics(self) -> Dict[str, Any]:
        """Get trigger statistics."""
        total = len(self.triggers)
        enabled = len([t for t in self.triggers.values() if t.enabled])

        by_type = {}
        for trigger in self.triggers.values():
            trigger_type = type(trigger).__name__
            by_type[trigger_type] = by_type.get(trigger_type, 0) + 1

        return {
            "total_triggers": total,
            "enabled_triggers": enabled,
            "by_type": by_type
        }
