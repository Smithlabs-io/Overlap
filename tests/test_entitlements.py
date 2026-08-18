"""
Tests for entitlement / subscription tier logic in core/entitlements.py.

Uses the real (test-isolated) SQLite DB from the fresh_db fixture.
"""
import pytest
import config as app_config

from core.entitlements import (
    Feature,
    FEATURE_LIMITS,
    SubscriptionTier,
    check_event_limit,
    get_event_limit,
    has_feature,
    is_premium,
)
from core.exceptions import EventLimitReachedError


GUILD_ID = 99999  # arbitrary guild; no subscription row → FREE tier


# ---------------------------------------------------------------------------
# Free-tier defaults
# ---------------------------------------------------------------------------

def test_free_tier_max_events_default_is_25():
    assert app_config.FREE_TIER_MAX_EVENTS == 25


def test_free_tier_max_events_reflected_in_feature_limits():
    assert FEATURE_LIMITS[SubscriptionTier.FREE][Feature.MAX_EVENTS] == app_config.FREE_TIER_MAX_EVENTS


def test_free_tier_recurring_events_disabled_in_limits():
    # The FEATURE_LIMITS table still marks recurring events False for FREE tier.
    # ALL_FEATURES_ENABLED bypasses this at runtime; the table itself is unchanged.
    assert FEATURE_LIMITS[SubscriptionTier.FREE][Feature.RECURRING_EVENTS] is False


# ---------------------------------------------------------------------------
# ALL_FEATURES_ENABLED behaviour (public edition default)
# ---------------------------------------------------------------------------

def test_all_features_enabled_grants_recurring_events(monkeypatch):
    monkeypatch.setattr(app_config, "ALL_FEATURES_ENABLED", True)
    assert has_feature(GUILD_ID, Feature.RECURRING_EVENTS) is True


def test_all_features_enabled_grants_is_premium(monkeypatch):
    monkeypatch.setattr(app_config, "ALL_FEATURES_ENABLED", True)
    assert is_premium(GUILD_ID) is True


def test_gate_active_when_all_features_disabled(monkeypatch):
    monkeypatch.setattr(app_config, "ALL_FEATURES_ENABLED", False)
    assert has_feature(GUILD_ID, Feature.RECURRING_EVENTS) is False


def test_is_premium_false_for_free_guild_when_gate_active(monkeypatch):
    monkeypatch.setattr(app_config, "ALL_FEATURES_ENABLED", False)
    assert is_premium(GUILD_ID) is False


# ---------------------------------------------------------------------------
# check_event_limit enforcement
# ---------------------------------------------------------------------------

def test_check_event_limit_passes_under_limit():
    limit = get_event_limit(GUILD_ID)
    # Should not raise when current_count is one below the limit
    check_event_limit(GUILD_ID, limit - 1)  # no exception


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
