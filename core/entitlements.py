"""
Feature entitlements for Overlap (community edition).

All features are enabled by default. The FREE_TIER_MAX_EVENTS config controls
the active-event cap per server — raise it via environment variable.
"""
from enum import Enum

import config
from core.logging import get_logger
from core.exceptions import EventLimitReachedError

logger = get_logger(__name__)


class Feature(Enum):
    """Features that can be checked via has_feature()."""
    MAX_EVENTS = "max_events"
    RECURRING_EVENTS = "recurring_events"
    PERSISTENT_AVAILABILITY = "persistent_availability"
    ADVANCED_NOTIFICATIONS = "advanced_notifications"
    PRIORITY_SUPPORT = "priority_support"


def is_premium(guild_id: int) -> bool:
    """Always True in the community edition — all features are free."""
    return True


def has_feature(guild_id: int, feature: Feature) -> bool:
    """Always True in the community edition — all features are enabled."""
    return True


def get_event_limit(guild_id: int) -> int:
    """Return the active-event cap for a server (set FREE_TIER_MAX_EVENTS to raise it)."""
    return config.FREE_TIER_MAX_EVENTS


def check_event_limit(guild_id: int, current_count: int) -> None:
    """
    Raise EventLimitReachedError if current_count is at or above the limit.
    The limit defaults to 25 and is configurable via FREE_TIER_MAX_EVENTS.
    """
    limit = get_event_limit(guild_id)
    if current_count >= limit:
        logger.info(f"Event limit reached for guild {guild_id}: {current_count}/{limit}")
        raise EventLimitReachedError(current_count, limit, guild_id)
