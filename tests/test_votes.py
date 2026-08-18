"""
Tests for vote tracking: VoteRepository CRUD and core/votes.py logic.
"""
from datetime import datetime, timedelta
from unittest.mock import patch

from core.votes import (
    has_voted,
    get_vote_state,
    record_vote,
    record_link_click,
    mark_prompted,
    mark_shame_shown,
    VOTE_WINDOW_HOURS,
)
from core.repositories.votes import VoteRepository


USER_ID = 42


# ---------------------------------------------------------------------------
# VoteRepository — CRUD
# ---------------------------------------------------------------------------

class TestVoteRepository:

    def test_get_unknown_user_returns_none(self):
        assert VoteRepository.get(USER_ID) is None

    def test_record_vote_creates_row(self):
        VoteRepository.record_vote(USER_ID)
        row = VoteRepository.get(USER_ID)
        assert row is not None
        assert row["voted_at"] is not None

    def test_record_vote_sets_voted_at(self):
        before = datetime.utcnow()
        VoteRepository.record_vote(USER_ID)
        voted_at = datetime.fromisoformat(VoteRepository.get(USER_ID)["voted_at"])
        assert voted_at >= before

    def test_record_vote_resets_link_clicked_and_shame(self):
        VoteRepository.record_link_click(USER_ID)
        VoteRepository.mark_shame_shown(USER_ID)
        VoteRepository.record_vote(USER_ID)
        row = VoteRepository.get(USER_ID)
        assert row["link_clicked"] == 0
        assert row["shame_shown"] == 0

    def test_record_vote_is_idempotent(self):
        """Calling record_vote twice must update, not crash on UNIQUE constraint."""
        VoteRepository.record_vote(USER_ID)
        VoteRepository.record_vote(USER_ID)
        assert VoteRepository.get(USER_ID) is not None

    def test_record_link_click_sets_flag(self):
        VoteRepository.record_link_click(USER_ID)
        assert VoteRepository.get(USER_ID)["link_clicked"] == 1

    def test_record_link_click_is_idempotent(self):
        VoteRepository.record_link_click(USER_ID)
        VoteRepository.record_link_click(USER_ID)
        assert VoteRepository.get(USER_ID)["link_clicked"] == 1

    def test_mark_prompted_sets_flag(self):
        VoteRepository.mark_prompted(USER_ID)
        assert VoteRepository.get(USER_ID)["vote_prompted"] == 1

    def test_mark_shame_shown_sets_flag(self):
        VoteRepository.mark_shame_shown(USER_ID)
        assert VoteRepository.get(USER_ID)["shame_shown"] == 1

    def test_different_users_are_isolated(self):
        VoteRepository.record_vote(USER_ID)
        assert VoteRepository.get(USER_ID + 1) is None


# ---------------------------------------------------------------------------
# has_voted
# ---------------------------------------------------------------------------

class TestHasVoted:

    def test_unknown_user_has_not_voted(self):
        assert has_voted(USER_ID) is False

    def test_recent_vote_returns_true(self):
        record_vote(USER_ID)
        assert has_voted(USER_ID) is True

    def test_vote_within_window_returns_true(self):
        record_vote(USER_ID)
        still_inside = datetime.utcnow() + timedelta(hours=VOTE_WINDOW_HOURS - 1)
        with patch("core.votes.datetime") as mock_dt:
            mock_dt.fromisoformat = datetime.fromisoformat
            mock_dt.utcnow.return_value = still_inside
            assert has_voted(USER_ID) is True

    def test_expired_vote_returns_false(self):
        record_vote(USER_ID)
        past_window = datetime.utcnow() + timedelta(hours=VOTE_WINDOW_HOURS + 1)
        with patch("core.votes.datetime") as mock_dt:
            mock_dt.fromisoformat = datetime.fromisoformat
            mock_dt.utcnow.return_value = past_window
            assert has_voted(USER_ID) is False

    def test_exactly_at_window_boundary_is_expired(self):
        record_vote(USER_ID)
        at_boundary = datetime.utcnow() + timedelta(hours=VOTE_WINDOW_HOURS)
        with patch("core.votes.datetime") as mock_dt:
            mock_dt.fromisoformat = datetime.fromisoformat
            mock_dt.utcnow.return_value = at_boundary
            assert has_voted(USER_ID) is False


# ---------------------------------------------------------------------------
# get_vote_state
# ---------------------------------------------------------------------------

class TestGetVoteState:

    def test_unknown_user_returns_all_false(self):
        state = get_vote_state(USER_ID)
        assert state == {
            "has_voted": False,
            "link_clicked": False,
            "shame_shown": False,
            "vote_prompted": False,
        }

    def test_reflects_recorded_vote(self):
        record_vote(USER_ID)
        state = get_vote_state(USER_ID)
        assert state["has_voted"] is True
        assert state["link_clicked"] is False

    def test_reflects_link_click(self):
        record_link_click(USER_ID)
        assert get_vote_state(USER_ID)["link_clicked"] is True

    def test_reflects_prompted(self):
        mark_prompted(USER_ID)
        assert get_vote_state(USER_ID)["vote_prompted"] is True

    def test_reflects_shame_shown(self):
        mark_shame_shown(USER_ID)
        assert get_vote_state(USER_ID)["shame_shown"] is True

    def test_vote_and_click_both_reflected(self):
        record_vote(USER_ID)
        record_link_click(USER_ID)
        state = get_vote_state(USER_ID)
        assert state["has_voted"] is True
        assert state["link_clicked"] is True
