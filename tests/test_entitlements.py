"""
Tests for core/entitlements.py (community edition).

All features are always enabled. The only configurable limit is
FREE_TIER_MAX_EVENTS (default 25), enforced by check_event_limit.
"""
import pytest
import config as app_config

from core.entitlements import (
    Feature,
    check_event_limit,
    get_event_limit,
    has_feature,
    is_premium,
)
from core.exceptions import EventLimitReachedError


GUILD_ID = 99999


# ---------------------------------------------------------------------------
# Always-on behaviour
# ---------------------------------------------------------------------------

def test_is_premium_always_true():
    assert is_premium(GUILD_ID) is True


def test_has_feature_always_true():
    for feature in Feature:
        assert has_feature(GUILD_ID, feature) is True


def test_get_event_limit_returns_config_value():
    assert get_event_limit(GUILD_ID) == app_config.FREE_TIER_MAX_EVENTS


def test_free_tier_max_events_default_is_25():
    assert app_config.FREE_TIER_MAX_EVENTS == 25


# ---------------------------------------------------------------------------
# check_event_limit enforcement
# ---------------------------------------------------------------------------

def test_check_event_limit_passes_under_limit():
    limit = get_event_limit(GUILD_ID)
    check_event_limit(GUILD_ID, limit - 1)  # must not raise


def test_check_event_limit_raises_at_limit():
    limit = get_event_limit(GUILD_ID)
    with pytest.raises(EventLimitReachedError) as exc_info:
        check_event_limit(GUILD_ID, limit)
    err = exc_info.value
    assert err.limit == limit
    assert err.current_count == limit


def test_check_event_limit_raises_above_limit():
    limit = get_event_limit(GUILD_ID)
    with pytest.raises(EventLimitReachedError):
        check_event_limit(GUILD_ID, limit + 10)


def test_event_limit_respects_config_override(monkeypatch):
    monkeypatch.setattr(app_config, "FREE_TIER_MAX_EVENTS", 5)
    assert get_event_limit(GUILD_ID) == 5
    check_event_limit(GUILD_ID, 4)  # should pass
    with pytest.raises(EventLimitReachedError):
        check_event_limit(GUILD_ID, 5)
