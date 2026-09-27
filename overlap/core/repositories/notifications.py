"""
Notification Repository for Event Bot.

Handles all database operations for notification preferences
and scheduled notifications.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from overlap.core.database import execute_query, execute_one, execute_write, transaction
from overlap.core.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Notification Types
# =============================================================================

class NotificationType(Enum):
    """Types of notifications the bot can send."""
    EVENT_REMINDER = "event_reminder"       # Reminder before event starts
    EVENT_START = "event_start"             # When event starts
    EVENT_CANCELED = "event_canceled"       # When event is canceled
    EVENT_CHANGED = "event_changed"         # When event details change
    EVENT_CONFIRMED = "event_confirmed"     # When event date is confirmed


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class NotificationPreference:
    """User's notification preferences for an event."""
    user_id: int
    guild_id: int
    event_name: str
    reminder_minutes: int = 60  # Default: 1 hour before
    notify_on_start: bool = True
    notify_on_change: bool = True
    notify_on_cancel: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "guild_id": self.guild_id,
            "event_name": self.event_name,
            "reminder_minutes": self.reminder_minutes,
            "notify_on_start": self.notify_on_start,
            "notify_on_change": self.notify_on_change,
            "notify_on_cancel": self.notify_on_cancel,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "NotificationPreference":
        return NotificationPreference(
            user_id=data["user_id"],
            guild_id=data["guild_id"],
            event_name=data["event_name"],
            reminder_minutes=data.get("reminder_minutes", 60),
            notify_on_start=data.get("notify_on_start", True),
            notify_on_change=data.get("notify_on_change", True),
            notify_on_cancel=data.get("notify_on_cancel", True),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )


@dataclass
class ScheduledNotification:
    """A notification scheduled to be sent at a specific time."""
    id: str
    notification_type: NotificationType
    user_id: int
    guild_id: int
    event_name: str
    scheduled_time: str  # ISO format
    message: str
    sent: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "notification_type": self.notification_type.value,
            "user_id": self.user_id,
            "guild_id": self.guild_id,
            "event_name": self.event_name,
            "scheduled_time": self.scheduled_time,
            "message": self.message,
            "sent": self.sent,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ScheduledNotification":
        return ScheduledNotification(
            id=data["id"],
            notification_type=NotificationType(data["notification_type"]),
            user_id=data["user_id"],
            guild_id=data["guild_id"],
            event_name=data["event_name"],
            scheduled_time=data["scheduled_time"],
            message=data["message"],
            sent=data.get("sent", False),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )


class NotificationRepository:
    """Repository for notification data operations."""

    # =========================================================================
    # Notification Preferences
    # =========================================================================

    @staticmethod
    def get_preference(user_id: int, guild_id: int, event_name: str) -> Optional[NotificationPreference]:
        """Get a user's notification preference for an event."""
        row = execute_one(
            "SELECT * FROM notification_preferences WHERE user_id = ? AND guild_id = ? AND event_name = ?",
            (str(user_id), str(guild_id), event_name),
        )
        return NotificationRepository._row_to_preference(dict(row)) if row else None

    @staticmethod
    def get_user_preferences(user_id: int, guild_id: int) -> Dict[str, NotificationPreference]:
        """Get all notification preferences for a user in a guild."""
        rows = execute_query(
            "SELECT * FROM notification_preferences WHERE user_id = ? AND guild_id = ?",
            (str(user_id), str(guild_id)),
        )
        return {row["event_name"]: NotificationRepository._row_to_preference(dict(row)) for row in rows}

    @staticmethod
    def get_event_subscribers(guild_id: int, event_name: str) -> List[NotificationPreference]:
        """Get all users who want notifications for an event."""
        rows = execute_query(
            "SELECT * FROM notification_preferences WHERE guild_id = ? AND event_name = ?",
            (str(guild_id), event_name),
        )
        return [NotificationRepository._row_to_preference(dict(row)) for row in rows]

    @staticmethod
    def set_preference(preference: NotificationPreference) -> None:
        """Set or update a notification preference."""
        with transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO notification_preferences
                    (user_id, guild_id, event_name, reminder_minutes,
                     notify_on_start, notify_on_change, notify_on_cancel)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, guild_id, event_name) DO UPDATE SET
                    reminder_minutes = excluded.reminder_minutes,
                    notify_on_start  = excluded.notify_on_start,
                    notify_on_change = excluded.notify_on_change,
                    notify_on_cancel = excluded.notify_on_cancel,
                    updated_at       = datetime('now')
                """,
                (
                    str(preference.user_id),
                    str(preference.guild_id),
                    preference.event_name,
                    preference.reminder_minutes,
                    int(preference.notify_on_start),
                    int(preference.notify_on_change),
                    int(preference.notify_on_cancel),
                ),
            )

    @staticmethod
    def remove_preference(user_id: int, guild_id: int, event_name: str) -> bool:
        """Remove a notification preference."""
        with transaction() as cursor:
            cursor.execute(
                "DELETE FROM notification_preferences WHERE user_id = ? AND guild_id = ? AND event_name = ?",
                (str(user_id), str(guild_id), event_name),
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_users_to_notify(guild_id: int, event_name: str) -> List[NotificationPreference]:
        """Get all users who want notifications for an event (alias of get_event_subscribers)."""
        return NotificationRepository.get_event_subscribers(guild_id, event_name)

    @staticmethod
    def remove_event_preferences(guild_id: int, event_name: str) -> int:
        """Remove all notification preferences for an event."""
        try:
            return execute_write(
                "DELETE FROM notification_preferences WHERE guild_id = ? AND event_name = ?",
                (str(guild_id), event_name),
            )
        except Exception as e:
            logger.error(f"Failed to remove event preferences: {e}")
            return 0

    @staticmethod
    def migrate_preferences(guild_id: int, old_event_name: str, new_event_name: str) -> int:
        """Repoint notification preferences from one event name to another (event renamed)."""
        with transaction() as cursor:
            cursor.execute(
                """
                UPDATE notification_preferences
                SET event_name = ?, updated_at = datetime('now')
                WHERE guild_id = ? AND event_name = ?
                """,
                (new_event_name, str(guild_id), old_event_name),
            )
            return cursor.rowcount

    # =========================================================================
    # Scheduled Notifications
    # =========================================================================

    @staticmethod
    def schedule_notification(
        notification_type: NotificationType,
        user_id: int,
        guild_id: int,
        event_name: str,
        scheduled_time: datetime,
        message: str
    ) -> Optional[str]:
        """Schedule a notification to be sent at a specific time."""
        try:
            notification_id = str(uuid.uuid4())
            execute_write(
                """
                INSERT INTO scheduled_notifications (
                    id, notification_type, user_id, guild_id, event_name,
                    scheduled_time, message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    notification_id,
                    notification_type.value,
                    str(user_id),
                    str(guild_id),
                    event_name,
                    scheduled_time.isoformat(),
                    message
                )
            )
            return notification_id

        except Exception as e:
            logger.error(f"Failed to schedule notification: {e}")
            return None

    @staticmethod
    def get_pending_notifications(before: Optional[datetime] = None) -> List[ScheduledNotification]:
        """Get all pending (unsent) notifications."""
        if before is None:
            before = datetime.utcnow()

        rows = execute_query(
            """
            SELECT * FROM scheduled_notifications
            WHERE sent = 0 AND scheduled_time <= ?
            ORDER BY scheduled_time ASC
            """,
            (before.isoformat(),)
        )
        return [NotificationRepository._row_to_scheduled(dict(row)) for row in rows]

    @staticmethod
    def mark_notification_sent(notification_id: str) -> bool:
        """Mark a notification as sent."""
        try:
            execute_write("UPDATE scheduled_notifications SET sent = 1 WHERE id = ?", (notification_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to mark notification sent: {e}")
            return False

    @staticmethod
    def delete_notification(notification_id: str) -> bool:
        """Delete a scheduled notification."""
        try:
            execute_write("DELETE FROM scheduled_notifications WHERE id = ?", (notification_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to delete notification: {e}")
            return False

    @staticmethod
    def delete_event_notifications(guild_id: int, event_name: str) -> int:
        """Delete all scheduled notifications for an event."""
        try:
            return execute_write(
                "DELETE FROM scheduled_notifications WHERE guild_id = ? AND event_name = ?",
                (str(guild_id), event_name),
            )
        except Exception as e:
            logger.error(f"Failed to delete event notifications: {e}")
            return 0

    @staticmethod
    def cleanup_sent_notifications(older_than_days: int = 7) -> int:
        """Clean up old sent notifications."""
        try:
            return execute_write(
                """
                DELETE FROM scheduled_notifications
                WHERE sent = 1
                AND created_at < datetime('now', '-' || ? || ' days')
                """,
                (older_than_days,)
            )
        except Exception as e:
            logger.error(f"Failed to cleanup notifications: {e}")
            return 0

    # =========================================================================
    # Helper Methods
    # =========================================================================

    @staticmethod
    def _row_to_preference(row: dict) -> NotificationPreference:
        """Convert a database row to a NotificationPreference object."""
        return NotificationPreference(
            user_id=int(row["user_id"]),
            guild_id=int(row["guild_id"]),
            event_name=row["event_name"],
            reminder_minutes=row.get("reminder_minutes", 60),
            notify_on_start=bool(row.get("notify_on_start", 1)),
            notify_on_change=bool(row.get("notify_on_change", 1)),
            notify_on_cancel=bool(row.get("notify_on_cancel", 1)),
            created_at=row.get("created_at", datetime.utcnow().isoformat())
        )

    @staticmethod
    def _row_to_scheduled(row: dict) -> ScheduledNotification:
        """Convert a database row to a ScheduledNotification object."""
        return ScheduledNotification(
            id=row["id"],
            notification_type=NotificationType(row["notification_type"]),
            user_id=int(row["user_id"]),
            guild_id=int(row["guild_id"]),
            event_name=row["event_name"],
            scheduled_time=row["scheduled_time"],
            message=row["message"],
            sent=bool(row.get("sent", 0)),
            created_at=row.get("created_at", datetime.utcnow().isoformat())
        )
