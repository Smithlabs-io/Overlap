"""
Persistent Availability Memory for Event Bot.

Remembers users' typical availability patterns across events,
allowing pre-selection of historically common hours in /register.

A thin, datetime-based convenience layer over AvailabilityMemoryRepository,
which owns the actual availability_patterns SQL.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from overlap.core import entitlements
from overlap.core.entitlements import Feature
from overlap.core.logging import get_logger
from overlap.core.repositories.availability import AvailabilityMemoryRepository

logger = get_logger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class TimeSlotPattern:
    """A pattern representing a user's typical availability."""
    day_of_week: int  # 0=Monday, 6=Sunday
    hour: int         # 0-23
    count: int = 1
    last_used: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "day_of_week": self.day_of_week,
            "hour": self.hour,
            "count": self.count,
            "last_used": self.last_used,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TimeSlotPattern":
        return TimeSlotPattern(
            day_of_week=data["day_of_week"],
            hour=data["hour"],
            count=data.get("count", 1),
            last_used=data.get("last_used", datetime.utcnow().isoformat()),
        )


@dataclass
class UserAvailabilityMemory:
    """A user's availability patterns for a guild."""
    user_id: int
    guild_id: int
    patterns: List[TimeSlotPattern] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def get_pattern(self, day_of_week: int, hour: int) -> Optional[TimeSlotPattern]:
        for pattern in self.patterns:
            if pattern.day_of_week == day_of_week and pattern.hour == hour:
                return pattern
        return None

    def get_suggested_slots(self, min_count: int = 2) -> List[TimeSlotPattern]:
        """Get slots the user is frequently available at."""
        return sorted(
            [p for p in self.patterns if p.count >= min_count],
            key=lambda p: p.count,
            reverse=True,
        )


# =============================================================================
# Public API
# =============================================================================

def get_user_memory(user_id: int, guild_id: int) -> Optional[UserAvailabilityMemory]:
    """Get a user's availability patterns for a guild. Returns None if none exist."""
    rows = AvailabilityMemoryRepository.get_user_patterns(user_id, guild_id)
    if not rows:
        return None
    patterns = [TimeSlotPattern(**row) for row in rows]
    return UserAvailabilityMemory(user_id=user_id, guild_id=guild_id, patterns=patterns)


def record_availability(
    user_id: int,
    guild_id: int,
    availability_slots: List[datetime],
) -> bool:
    """
    Record a user's availability selections to build their pattern.

    Args:
        user_id: The Discord user ID
        guild_id: The Discord guild ID
        availability_slots: List of datetime objects the user selected

    Returns:
        True if recorded, False if the feature is off or no slots were given.
    """
    if not entitlements.has_feature(guild_id, Feature.PERSISTENT_AVAILABILITY) or not availability_slots:
        return False

    slots = [(slot.weekday(), slot.hour) for slot in availability_slots]
    recorded = AvailabilityMemoryRepository.record_availability(user_id, guild_id, slots)
    if recorded:
        logger.info(
            f"Recorded {len(availability_slots)} availability slots "
            f"for user {user_id} in guild {guild_id}"
        )
    return recorded


def get_suggested_availability(
    user_id: int,
    guild_id: int,
    proposed_slots: List[datetime],
    min_count: int = 2,
) -> List[datetime]:
    """
    Filter proposed_slots to those matching the user's historical patterns.

    Returns the subset of proposed_slots the user has been available at
    (same day-of-week + hour) at least min_count times.
    """
    frequent = AvailabilityMemoryRepository.get_frequent_patterns(user_id, guild_id, min_count)
    if not frequent:
        return []

    pattern_set = {(p["day_of_week"], p["hour"]) for p in frequent}
    return [s for s in proposed_slots if (s.weekday(), s.hour) in pattern_set]


def clear_user_memory(user_id: int, guild_id: int) -> bool:
    """Clear all availability patterns for a user in a guild."""
    return AvailabilityMemoryRepository.clear_user_patterns(user_id, guild_id)


def get_memory_stats(user_id: int, guild_id: int) -> Optional[Dict[str, Any]]:
    """Get statistics about a user's availability memory."""
    return AvailabilityMemoryRepository.get_pattern_stats(user_id, guild_id)
