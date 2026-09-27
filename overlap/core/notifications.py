"""
Notification system for Event Bot.

Handles scheduling and sending notifications for:
- Event reminders (configurable time before event)
- Event start notifications
- Event canceled/changed notifications
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Union
import discord

from overlap.core.logging import get_logger, log_user_action
from overlap.core.repositories.notifications import (
    NotificationPreference,
    NotificationRepository,
    NotificationType,
    ScheduledNotification,
)

logger = get_logger(__name__)

__all__ = [
    "NotificationType", "NotificationPreference", "ScheduledNotification",
    "get_user_preferences", "get_event_preference", "set_notification_preference",
    "remove_notification_preference", "get_users_to_notify",
    "migrate_event_notification_preferences",
]


# =============================================================================
# Preference Management
# =============================================================================
# NotificationPreference, ScheduledNotification and NotificationType are
# defined in core/repositories/notifications.py, alongside the SQL that reads
# and writes them, and re-exported here for callers that do
# `from overlap.core import notifications` and expect notifications.<name>.

def get_user_preferences(user_id: int, guild_id: int) -> Dict[str, NotificationPreference]:
    """Get all notification preferences for a user in a guild."""
    return NotificationRepository.get_user_preferences(user_id, guild_id)


def get_event_preference(user_id: int, guild_id: int, event_name: str) -> Optional[NotificationPreference]:
    """Get a user's notification preference for a specific event."""
    return NotificationRepository.get_preference(user_id, guild_id, event_name)


def set_notification_preference(preference: NotificationPreference) -> None:
    """Set or update a user's notification preference for an event."""
    NotificationRepository.set_preference(preference)
    log_user_action(
        "set_notification",
        preference.user_id,
        preference.guild_id,
        event_name=preference.event_name,
        reminder_minutes=preference.reminder_minutes,
    )


def remove_notification_preference(user_id: int, guild_id: int, event_name: str) -> bool:
    """Remove a user's notification preference for an event."""
    return NotificationRepository.remove_preference(user_id, guild_id, event_name)


def get_users_to_notify(guild_id: int, event_name: str) -> List[NotificationPreference]:
    """Get all users who want notifications for an event."""
    return NotificationRepository.get_event_subscribers(guild_id, event_name)


def migrate_event_notification_preferences(
    guild_id: int,
    old_event_name: str,
    new_event_name: str,
) -> int:
    """Migrate notification preferences when an event is renamed."""
    count = NotificationRepository.migrate_preferences(guild_id, old_event_name, new_event_name)
    if count:
        logger.info(
            f"Migrated {count} notification preferences: "
            f"'{old_event_name}' → '{new_event_name}' in guild {guild_id}"
        )
    return count


# =============================================================================
# Notification Sending
# =============================================================================

async def send_dm_notification(
    client: discord.Client,
    user_id: int,
    message: str,
    embed: Optional[discord.Embed] = None,
    guild_id: Optional[int] = None,
) -> bool:
    """
    Send a DM notification to a user.

    If the DM fails (user has DMs disabled) and guild_id is provided,
    falls back to the guild's configured notification_channel as a mention.

    Returns:
        True if delivered (DM or channel fallback), False if all attempts failed.
    """
    try:
        user = await client.fetch_user(user_id)
        if user:
            await user.send(content=message, embed=embed)
            logger.info(f"Sent DM notification to user {user_id}")
            return True
    except discord.Forbidden:
        logger.warning(f"Cannot send DM to user {user_id} — DMs disabled; trying channel fallback")
    except discord.HTTPException as e:
        logger.error(f"Failed to send DM to user {user_id}: {e}; trying channel fallback")

    # Channel fallback — only if we know which guild to post in
    if guild_id:
        try:
            from overlap.core.conf import get_config
            guild_config = get_config(guild_id)
            channel_id = guild_config.notification_channel
            if channel_id:
                channel = client.get_channel(int(channel_id))
                if channel:
                    fallback_msg = f"<@{user_id}> {message}"
                    await channel.send(content=fallback_msg, embed=embed)
                    logger.info(f"Delivered notification for user {user_id} via channel {channel_id}")
                    return True
        except Exception as e:
            logger.error(f"Channel fallback failed for user {user_id} in guild {guild_id}: {e}")

    return False


async def notify_event_reminder(
    client: discord.Client,
    guild_id: int,
    event_name: str,
    event_time: datetime,
    registered_users: List[int]
) -> int:
    """
    Send reminder notifications to all registered users.

    Returns:
        Number of notifications sent successfully
    """
    sent_count = 0
    users_to_notify = get_users_to_notify(guild_id, event_name)

    # Only notify users who are registered for the event
    registered_set = set(registered_users)

    for pref in users_to_notify:
        if pref.user_id in registered_set:
            time_str = f"<t:{int(event_time.timestamp())}:R>"
            message = (
                f"⏰ **Reminder:** Your event **{event_name}** starts {time_str}!\n\n"
                f"Don't forget to check your availability and join when it starts."
            )

            if await send_dm_notification(client, pref.user_id, message, guild_id=guild_id):
                sent_count += 1

    logger.info(f"Sent {sent_count} reminder notifications for event '{event_name}'")
    return sent_count


async def notify_event_start(
    client: discord.Client,
    guild_id: int,
    event_name: str,
    registered_users: List[int]
) -> int:
    """
    Send event start notifications to all registered users.

    Returns:
        Number of notifications sent successfully
    """
    sent_count = 0
    users_to_notify = get_users_to_notify(guild_id, event_name)
    registered_set = set(registered_users)

    for pref in users_to_notify:
        if pref.user_id in registered_set and pref.notify_on_start:
            message = (
                f"🎉 **{event_name}** is starting now!\n\n"
                f"Head over to the server to join in."
            )

            if await send_dm_notification(client, pref.user_id, message, guild_id=guild_id):
                sent_count += 1

    logger.info(f"Sent {sent_count} start notifications for event '{event_name}'")
    return sent_count


async def notify_event_canceled(
    client: discord.Client,
    guild_id: int,
    event_name: str,
    reason: Optional[str] = None
) -> int:
    """
    Send cancellation notifications to all users who wanted notifications.

    Returns:
        Number of notifications sent successfully
    """
    sent_count = 0
    users_to_notify = get_users_to_notify(guild_id, event_name)

    for pref in users_to_notify:
        if pref.notify_on_cancel:
            message = f"❌ **{event_name}** has been canceled."
            if reason:
                message += f"\n\n**Reason:** {reason}"

            if await send_dm_notification(client, pref.user_id, message, guild_id=guild_id):
                sent_count += 1

    # Clean up preferences for this event
    for pref in users_to_notify:
        remove_notification_preference(pref.user_id, guild_id, event_name)

    logger.info(f"Sent {sent_count} cancellation notifications for event '{event_name}'")
    return sent_count


async def notify_event_changed(
    client: discord.Client,
    guild_id: int,
    event_name: str,
    changes: str
) -> int:
    """
    Send change notifications to all users who wanted notifications.

    Returns:
        Number of notifications sent successfully
    """
    sent_count = 0
    users_to_notify = get_users_to_notify(guild_id, event_name)

    for pref in users_to_notify:
        if pref.notify_on_change:
            message = (
                f"📝 **{event_name}** has been updated!\n\n"
                f"**Changes:**\n{changes}"
            )

            if await send_dm_notification(client, pref.user_id, message, guild_id=guild_id):
                sent_count += 1

    logger.info(f"Sent {sent_count} change notifications for event '{event_name}'")
    return sent_count


async def notify_event_confirmed(
    client: discord.Client,
    guild_id: int,
    event_name: str,
    confirmed_time: datetime
) -> int:
    """
    Send confirmation notifications when an event date is finalized.

    Returns:
        Number of notifications sent successfully
    """
    sent_count = 0
    users_to_notify = get_users_to_notify(guild_id, event_name)

    time_str = f"<t:{int(confirmed_time.timestamp())}:F>"

    for pref in users_to_notify:
        message = (
            f"✅ **{event_name}** has been confirmed!\n\n"
            f"**Date & Time:** {time_str}\n\n"
            f"You'll receive a reminder before it starts."
        )

        if await send_dm_notification(client, pref.user_id, message, guild_id=guild_id):
            sent_count += 1

    logger.info(f"Sent {sent_count} confirmation notifications for event '{event_name}'")
    return sent_count


# =============================================================================
# Background Scheduler
# =============================================================================

class NotificationScheduler:
    """
    Background task that checks for and sends scheduled notifications.

    This runs as a background task in the Discord bot.
    """

    def __init__(self, client: discord.Client):
        self.client = client
        self.running = False
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        """Start the notification scheduler."""
        if not self.running:
            self.running = True
            self._task = asyncio.create_task(self._run())
            logger.info("Notification scheduler started")

    def stop(self) -> None:
        """Stop the notification scheduler."""
        self.running = False
        if self._task:
            self._task.cancel()
            logger.info("Notification scheduler stopped")

    async def _run(self) -> None:
        """Main scheduler loop."""
        while self.running:
            try:
                await self._check_and_send_notifications()
            except Exception as e:
                logger.error(f"Error in notification scheduler: {e}", exc_info=e)

            # Check every minute
            await asyncio.sleep(60)

    async def _check_and_send_notifications(self) -> None:
        """Check for pending notifications and send them."""
        # Import here to avoid circular imports
        from overlap.core import events, bulletins
        from datetime import timezone

        now_naive = datetime.utcnow()
        now_aware = datetime.now(timezone.utc)
        all_events = {}

        # Load all events from SQLite across all guilds
        from overlap.core.repositories.events import EventRepository
        all_events_by_guild = EventRepository.get_all_events()

        # Archive past events and update their bulletins (runs every check)
        for guild_id_str, guild_events in all_events_by_guild.items():
            guild_id = int(guild_id_str)
            for event in guild_events.values():
                if event.is_past and not event.is_archived:
                    await bulletins.mark_bulletin_as_past(self.client, event)
                    events.archive_event(guild_id_str, event.event_name)

        # Re-load all events for notification checks (archive_event may have mutated state)
        all_events_by_guild = EventRepository.get_all_events()
        for guild_id_str, guild_events in all_events_by_guild.items():
            for event_name, event in guild_events.items():
                all_events[f"{guild_id_str}:{event_name}"] = event

        # Check each event for notifications to send
        for key, event in all_events.items():
            guild_id = int(event.guild_id)

            # Skip events without confirmed dates
            if not event.confirmed_date or event.confirmed_date == "TBD":
                continue

            # Parse confirmed date (assuming ISO format)
            try:
                event_time = datetime.fromisoformat(event.confirmed_date)
            except ValueError:
                continue

            # Use timezone-aware or naive now based on event_time
            now = now_aware if event_time.tzinfo is not None else now_naive

            # Get users who want notifications
            users = get_users_to_notify(guild_id, event.event_name)

            for pref in users:
                # Check if we should send a reminder
                reminder_time = event_time - timedelta(minutes=pref.reminder_minutes)

                # If reminder time is within the last minute, send it
                if reminder_time <= now < reminder_time + timedelta(minutes=1):
                    await notify_event_reminder(
                        self.client,
                        guild_id,
                        event.event_name,
                        event_time,
                        [int(uid) for uid in event.rsvp]
                    )

                # If event is starting now (within last minute), send start notification
                if event_time <= now < event_time + timedelta(minutes=1):
                    await notify_event_start(
                        self.client,
                        guild_id,
                        event.event_name,
                        [int(uid) for uid in event.rsvp]
                    )


# Global scheduler instance (initialized when bot starts)
_scheduler: Optional[NotificationScheduler] = None


def init_scheduler(client: discord.Client) -> NotificationScheduler:
    """Initialize and start the notification scheduler."""
    global _scheduler
    _scheduler = NotificationScheduler(client)
    _scheduler.start()
    return _scheduler


def get_scheduler() -> Optional[NotificationScheduler]:
    """Get the notification scheduler instance."""
    return _scheduler
