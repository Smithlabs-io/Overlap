"""
Feature entitlements for Overlap.

Every limit and feature check in the bot goes through this module. The behavior
behind it comes from an `EntitlementProvider`. The community edition ships
`DefaultProvider`: every feature is on, and the only limit is
`MAX_ACTIVE_EVENTS` per server.

An add-on package can replace the provider through the plugin hook in
`overlap.plugins` (see `set_provider`). Core never imports an add-on.
"""
from enum import Enum
from typing import Optional, Protocol, runtime_checkable

import discord

from overlap import config
from overlap.core.exceptions import EventLimitReachedError
from overlap.core.logging import get_logger

logger = get_logger(__name__)


class Feature(Enum):
    """Features a provider can allow or deny."""
    RECURRING_EVENTS = "recurring_events"
    PERSISTENT_AVAILABILITY = "persistent_availability"
    NOTIFICATIONS = "notifications"
    EXPORT = "export"


@runtime_checkable
class EntitlementProvider(Protocol):
    """What the bot needs to know about a server's entitlements."""

    def event_limit(self, guild_id: int) -> Optional[int]:
        """Active-event cap for a server. None means unlimited."""

    def limit_hint(self, guild_id: int) -> str:
        """Sentence appended to the limit-reached message (how to get more room)."""

    def has_feature(self, guild_id: int, feature: Feature) -> bool:
        """Whether the server may use a feature."""

    async def gate(self, interaction: discord.Interaction, feature: Feature) -> bool:
        """
        Check access at a user-facing entry point.

        Return True to let the interaction proceed. Return False after sending
        the user your own message, and the caller stops.
        """


class DefaultProvider:
    """Community edition: everything is on, one configurable event cap."""

    def event_limit(self, guild_id: int) -> Optional[int]:
        return config.MAX_ACTIVE_EVENTS

    def limit_hint(self, guild_id: int) -> str:
        return "Server admins can raise this with `MAX_ACTIVE_EVENTS`."

    def has_feature(self, guild_id: int, feature: Feature) -> bool:
        return True

    async def gate(self, interaction: discord.Interaction, feature: Feature) -> bool:
        return True


_provider: EntitlementProvider = DefaultProvider()


def set_provider(provider: EntitlementProvider) -> None:
    """Replace the active provider. Called by plugins during setup."""
    global _provider
    if not isinstance(provider, EntitlementProvider):
        raise TypeError(f"{type(provider).__name__} does not implement EntitlementProvider")
    logger.info(f"Entitlement provider set: {type(provider).__name__}")
    _provider = provider


def get_provider() -> EntitlementProvider:
    return _provider


def has_feature(guild_id: int, feature: Feature) -> bool:
    return _provider.has_feature(guild_id, feature)


def get_event_limit(guild_id: int) -> Optional[int]:
    """Active-event cap for a server, or None if unlimited."""
    return _provider.event_limit(guild_id)


def check_event_limit(guild_id: int, current_count: int) -> None:
    """Raise EventLimitReachedError if current_count is at or above the limit."""
    limit = _provider.event_limit(guild_id)
    if limit is None:
        return
    if current_count >= limit:
        logger.info(f"Event limit reached for guild {guild_id}: {current_count}/{limit}")
        raise EventLimitReachedError(current_count, limit, guild_id, hint=_provider.limit_hint(guild_id))


async def gate(interaction: discord.Interaction, feature: Feature) -> bool:
    """True if the interaction may proceed. If False, the user has already been told why."""
    return await _provider.gate(interaction, feature)
