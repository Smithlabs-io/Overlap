"""
Tests for core/entitlements.py.

The community edition's DefaultProvider allows every feature and enforces one
limit, MAX_ACTIVE_EVENTS (default 10). Add-ons can swap the provider.
"""
from unittest.mock import MagicMock

import pytest

from overlap import config as app_config
from overlap.core import entitlements
from overlap.core.entitlements import (
    DefaultProvider,
    EntitlementProvider,
    Feature,
    check_event_limit,
    get_event_limit,
    has_feature,
)
from overlap.core.exceptions import EventLimitReachedError

GUILD_ID = 99999


@pytest.fixture(autouse=True)
def restore_provider():
    original = entitlements.get_provider()
    yield
    entitlements.set_provider(original)


# ---------------------------------------------------------------------------
# DefaultProvider
# ---------------------------------------------------------------------------

def test_default_provider_satisfies_protocol():
    assert isinstance(DefaultProvider(), EntitlementProvider)


def test_all_features_enabled_by_default():
    for feature in Feature:
        assert has_feature(GUILD_ID, feature) is True


def test_default_event_limit_is_10():
    assert app_config.MAX_ACTIVE_EVENTS == 10
    assert get_event_limit(GUILD_ID) == 10


async def test_default_gate_always_allows():
    for feature in Feature:
        assert await entitlements.gate(MagicMock(), feature) is True


# ---------------------------------------------------------------------------
# check_event_limit
# ---------------------------------------------------------------------------

def test_check_event_limit_passes_under_limit():
    check_event_limit(GUILD_ID, get_event_limit(GUILD_ID) - 1)


def test_check_event_limit_raises_at_limit():
    limit = get_event_limit(GUILD_ID)
    with pytest.raises(EventLimitReachedError) as exc_info:
        check_event_limit(GUILD_ID, limit)
    assert exc_info.value.limit == limit
    assert exc_info.value.current_count == limit


def test_limit_message_includes_provider_hint():
    limit = get_event_limit(GUILD_ID)
    with pytest.raises(EventLimitReachedError) as exc_info:
        check_event_limit(GUILD_ID, limit)
    assert "MAX_ACTIVE_EVENTS" in exc_info.value.user_message


def test_event_limit_respects_config_override(monkeypatch):
    monkeypatch.setattr(app_config, "MAX_ACTIVE_EVENTS", 3)
    assert get_event_limit(GUILD_ID) == 3
    check_event_limit(GUILD_ID, 2)
    with pytest.raises(EventLimitReachedError):
        check_event_limit(GUILD_ID, 3)


# ---------------------------------------------------------------------------
# Swapping the provider
# ---------------------------------------------------------------------------

class _Custom:
    def __init__(self, limit, allowed=(), gate_result=True):
        self._limit, self._allowed, self._gate_result = limit, set(allowed), gate_result

    def event_limit(self, guild_id):
        return self._limit

    def limit_hint(self, guild_id):
        return "Upgrade for more."

    def has_feature(self, guild_id, feature):
        return feature in self._allowed

    async def gate(self, interaction, feature):
        return self._gate_result


def test_unlimited_provider_never_raises():
    entitlements.set_provider(_Custom(limit=None))
    assert get_event_limit(GUILD_ID) is None
    check_event_limit(GUILD_ID, 10_000)


def test_custom_provider_controls_features():
    entitlements.set_provider(_Custom(limit=5, allowed={Feature.EXPORT}))
    assert has_feature(GUILD_ID, Feature.EXPORT) is True
    assert has_feature(GUILD_ID, Feature.RECURRING_EVENTS) is False


def test_custom_provider_hint_reaches_error():
    entitlements.set_provider(_Custom(limit=1))
    with pytest.raises(EventLimitReachedError) as exc_info:
        check_event_limit(GUILD_ID, 1)
    assert "Upgrade for more." in exc_info.value.user_message


async def test_gate_delegates_to_provider():
    entitlements.set_provider(_Custom(limit=5, gate_result=False))
    assert await entitlements.gate(MagicMock(), Feature.EXPORT) is False


def test_set_provider_rejects_non_providers():
    with pytest.raises(TypeError):
        entitlements.set_provider(object())
