"""
Alpha - Intelligent Notifier

Smart notification system with user preference learning.
Features:
- Intelligent reminder system
- Proactive issue alerts
- Context-aware suggestions
- Multiple delivery channels
- User preference learning
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications."""
    REMINDER = "reminder"
    ALERT = "alert"
    SUGGESTION = "suggestion"
    ERROR = "error"
    PERFORMANCE = "performance"
    INFO = "info"


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class NotificationChannel(Enum):
    """Delivery channels for notifications."""
    CLI = "cli"
    LOG = "log"
    EMAIL = "email"  # Future
    SMS = "sms"      # Future
    WEBHOOK = "webhook"  # Future


@dataclass
class Notification:
    """Represents a notification."""
    notification_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    channels: List[NotificationChannel] = None
    metadata: Dict[str, Any] = None
    read: bool = False
    actionable: bool = False
    action_url: Optional[str] = None


@dataclass
class NotificationPreference:
    """User notification preferences."""
    notification_type: NotificationType
    enabled: bool
    quiet_hours_start: Optional[int] = None  # Hour 0-23
    quiet_hours_end: Optional[int] = None    # Hour 0-23
    min_priority: NotificationPriority = NotificationPriority.NORMAL
    channels: List[NotificationChannel] = None
    frequency_limit: Optional[int] = None  # Max per day


class Notifier:
    """
    Intelligent notification system.

    Features:
    - Smart notification delivery
    - User preference learning
    - Quiet hours support
    - Multiple delivery channels
    - Frequency limiting
    - Priority-based filtering
    """

    def __init__(
        self,
        default_channel: NotificationChannel = NotificationChannel.CLI
    ):
        """
        Initialize notifier.

        Args:
            default_channel: Default notification channel
        """
        self.default_channel = default_channel
        self.notifications: List[Notification] = []
        self.preferences: Dict[NotificationType, NotificationPreference] = {}
        self.delivery_handlers: Dict[NotificationChannel, Callable] = {}
        self.notification_count_today: Dict[NotificationType, int] = {}
        self.last_notification_date = datetime.now().date()

        # Initialize default preferences
        self._initialize_default_preferences()

    def _initialize_default_preferences(self):
        """Initialize default notification preferences."""
        # Conservative defaults - user must opt-in to notifications
        for notif_type in NotificationType:
            self.preferences[notif_type] = NotificationPreference(
                notification_type=notif_type,
                enabled=False,  # Disabled by default
                quiet_hours_start=22,  # 10 PM
                quiet_hours_end=8,     # 8 AM
                min_priority=NotificationPriority.NORMAL,
                channels=[self.default_channel],
                frequency_limit=5  # Max 5 per day per type
            )

        # Enable only critical notifications by default
        self.preferences[NotificationType.ERROR].enabled = True
        self.preferences[NotificationType.ERROR].min_priority = NotificationPriority.NORMAL

    async def notify(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
        actionable: bool = False,
        action_url: Optional[str] = None,
        channels: Optional[List[NotificationChannel]] = None
    ) -> Optional[str]:
        """
        Send a notification.

        Args:
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Priority level
            metadata: Additional metadata
            actionable: Whether notification requires action
            action_url: URL for action (if actionable)
            channels: Override default channels

        Returns:
            Notification ID if sent, None if filtered
        """
        # Check if we should send this notification
        if not await self._should_send(notification_type, priority):
            logger.debug(
                f"Notification filtered: {notification_type.value} - {title}"
            )
            return None

        # Create notification
        import uuid
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            created_at=datetime.now(),
            channels=channels or self.preferences[notification_type].channels,
            metadata=metadata or {},
            actionable=actionable,
            action_url=action_url
        )

        # Store notification
        self.notifications.append(notification)

        # Deliver notification
        await self._deliver(notification)

        # Update count
        self._update_notification_count(notification_type)

        logger.info(f"Notification sent: {notification.notification_id} - {title}")
        return notification.notification_id

    async def _should_send(
        self,
        notification_type: NotificationType,
        priority: NotificationPriority
    ) -> bool:
        """Check if notification should be sent based on preferences."""
        # Reset daily count if needed
        self._check_reset_daily_count()

        # Get preferences
        pref = self.preferences.get(notification_type)
        if not pref:
            return False

        # Check if enabled
        if not pref.enabled:
            # Allow urgent notifications even if disabled
            if priority != NotificationPriority.URGENT:
                return False

        # Check priority threshold
        if priority.value < pref.min_priority.value:
            return False

        # Check frequency limit
        if pref.frequency_limit:
            count = self.notification_count_today.get(notification_type, 0)
            if count >= pref.frequency_limit:
                # Allow urgent notifications to bypass limit
                if priority != NotificationPriority.URGENT:
                    return False

        # Check quiet hours
        if not await self._is_quiet_hours_allowed(pref, priority):
            return False

        return True

    async def _is_quiet_hours_allowed(
        self,
        pref: NotificationPreference,
        priority: NotificationPriority
    ) -> bool:
        """Check if notification is allowed during quiet hours."""
        if pref.quiet_hours_start is None or pref.quiet_hours_end is None:
            return True

        current_hour = datetime.now().hour

        # Check if we're in quiet hours
        in_quiet_hours = False
        if pref.quiet_hours_start < pref.quiet_hours_end:
            in_quiet_hours = pref.quiet_hours_start <= current_hour < pref.quiet_hours_end
        else:
            # Quiet hours span midnight
            in_quiet_hours = current_hour >= pref.quiet_hours_start or current_hour < pref.quiet_hours_end

        if in_quiet_hours:
            # Allow urgent and high priority during quiet hours
            return priority.value >= NotificationPriority.HIGH.value

        return True

    async def _deliver(self, notification: Notification):
        """Deliver notification through configured channels."""
        for channel in notification.channels:
            handler = self.delivery_handlers.get(channel)
            if handler:
                try:
                    await handler(notification)
                except Exception as e:
                    logger.error(f"Failed to deliver notification via {channel.value}: {e}")
            else:
                # Default delivery to log
                await self._default_delivery(notification, channel)

        notification.delivered_at = datetime.now()

    async def _default_delivery(
        self,
        notification: Notification,
        channel: NotificationChannel
    ):
        """Default notification delivery."""
        if channel == NotificationChannel.CLI:
            # Print to console with formatting
            priority_symbols = {
                NotificationPriority.LOW: "ℹ️",
                NotificationPriority.NORMAL: "📌",
                NotificationPriority.HIGH: "⚠️",
                NotificationPriority.URGENT: "🚨"
            }
            symbol = priority_symbols.get(notification.priority, "📌")
            print(f"\n{symbol} [{notification.notification_type.value.upper()}] {notification.title}")
            print(f"   {notification.message}")
            if notification.actionable and notification.action_url:
                print(f"   Action: {notification.action_url}")
            print()

        elif channel == NotificationChannel.LOG:
            # Log notification
            log_level = {
                NotificationPriority.LOW: logging.INFO,
                NotificationPriority.NORMAL: logging.INFO,
                NotificationPriority.HIGH: logging.WARNING,
                NotificationPriority.URGENT: logging.ERROR
            }
            level = log_level.get(notification.priority, logging.INFO)
            logger.log(
                level,
                f"[{notification.notification_type.value}] {notification.title}: {notification.message}"
            )

    def _check_reset_daily_count(self):
        """Reset daily notification count if needed."""
        today = datetime.now().date()
        if today != self.last_notification_date:
            self.notification_count_today.clear()
            self.last_notification_date = today

    def _update_notification_count(self, notification_type: NotificationType):
        """Update notification count for today."""
        self.notification_count_today[notification_type] = \
            self.notification_count_today.get(notification_type, 0) + 1

    def register_handler(
        self,
        channel: NotificationChannel,
        handler: Callable
    ):
        """
        Register a custom notification handler.

        Args:
            channel: Notification channel
            handler: Async handler function
        """
        self.delivery_handlers[channel] = handler
        logger.info(f"Registered handler for channel: {channel.value}")

    async def update_preference(
        self,
        notification_type: NotificationType,
        **kwargs
    ):
        """
        Update notification preferences.

        Args:
            notification_type: Type to update
            **kwargs: Preference fields to update
        """
        if notification_type not in self.preferences:
            self.preferences[notification_type] = NotificationPreference(
                notification_type=notification_type,
                enabled=True,
                channels=[self.default_channel]
            )

        pref = self.preferences[notification_type]

        # Update fields
        for key, value in kwargs.items():
            if hasattr(pref, key):
                setattr(pref, key, value)

        logger.info(f"Updated preferences for {notification_type.value}")

    async def schedule_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        scheduled_for: datetime,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> str:
        """
        Schedule a notification for future delivery.

        Args:
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            scheduled_for: When to deliver
            priority: Priority level
            **kwargs: Additional notification parameters

        Returns:
            Notification ID
        """
        import uuid
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            created_at=datetime.now(),
            scheduled_for=scheduled_for,
            channels=kwargs.get('channels', self.preferences[notification_type].channels),
            metadata=kwargs.get('metadata', {}),
            actionable=kwargs.get('actionable', False),
            action_url=kwargs.get('action_url')
        )

        self.notifications.append(notification)
        logger.info(f"Scheduled notification: {notification.notification_id} for {scheduled_for}")

        return notification.notification_id

    async def deliver_scheduled(self):
        """Deliver scheduled notifications that are due."""
        now = datetime.now()
        delivered_count = 0

        for notification in self.notifications:
            if (notification.scheduled_for and
                notification.scheduled_for <= now and
                not notification.delivered_at):

                # Check if should send
                if await self._should_send(
                    notification.notification_type,
                    notification.priority
                ):
                    await self._deliver(notification)
                    self._update_notification_count(notification.notification_type)
                    delivered_count += 1

        if delivered_count > 0:
            logger.info(f"Delivered {delivered_count} scheduled notifications")

    async def get_notifications(
        self,
        notification_type: Optional[NotificationType] = None,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """
        Get notifications.

        Args:
            notification_type: Filter by type
            unread_only: Only unread notifications
            limit: Maximum to return

        Returns:
            List of notifications
        """
        notifications = self.notifications

        if notification_type:
            notifications = [n for n in notifications if n.notification_type == notification_type]

        if unread_only:
            notifications = [n for n in notifications if not n.read]

        # Sort by created_at descending
        notifications.sort(key=lambda n: n.created_at, reverse=True)

        return notifications[:limit]

    async def mark_read(self, notification_id: str):
        """Mark a notification as read."""
        for notification in self.notifications:
            if notification.notification_id == notification_id:
                notification.read = True
                logger.debug(f"Marked notification as read: {notification_id}")
                return

    async def get_statistics(self) -> Dict[str, Any]:
        """Get notification statistics."""
        total = len(self.notifications)
        if total == 0:
            return {
                "total_notifications": 0,
                "unread_count": 0,
                "by_type": {},
                "by_priority": {}
            }

        unread = sum(1 for n in self.notifications if not n.read)

        # Count by type
        by_type = {}
        for notification in self.notifications:
            type_name = notification.notification_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        # Count by priority
        by_priority = {}
        for notification in self.notifications:
            priority_name = notification.priority.name
            by_priority[priority_name] = by_priority.get(priority_name, 0) + 1

        return {
            "total_notifications": total,
            "unread_count": unread,
            "by_type": by_type,
            "by_priority": by_priority,
            "today_count": sum(self.notification_count_today.values())
        }
