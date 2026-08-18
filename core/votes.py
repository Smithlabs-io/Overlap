"""
Vote tracking for the free-tier vote wall.

Free users must vote on a bot listing site to unlock certain features.
Premium guilds bypass this check entirely.

Two modes (controlled by config.VERIFY_VOTE):
  False (default): Honor system. User clicks "I Voted". Click-tracking adds
                   a shame mechanic if they claim to vote without opening a link.
  True:            Server-side. top.gg/discordbotlist webhook records votes
                   automatically. No "I Voted" button needed.
"""
from datetime import datetime, timedelta
from core.repositories.votes import VoteRepository
from core.logging import get_logger

logger = get_logger(__name__)

VOTE_WINDOW_HOURS = 12


def has_voted(user_id: int) -> bool:
    row = VoteRepository.get(user_id)
    if not row or not row.get("voted_at"):
        return False
    try:
        voted_at = datetime.fromisoformat(row["voted_at"])
        return datetime.utcnow() - voted_at < timedelta(hours=VOTE_WINDOW_HOURS)
    except ValueError:
        return False


def get_vote_state(user_id: int) -> dict:
    row = VoteRepository.get(user_id) or {}
    return {
        "has_voted": has_voted(user_id),
        "link_clicked": bool(row.get("link_clicked", 0)),
        "shame_shown": bool(row.get("shame_shown", 0)),
        "vote_prompted": bool(row.get("vote_prompted", 0)),
    }


def record_vote(user_id: int):
    VoteRepository.record_vote(user_id)
    logger.info(f"Vote recorded for user {user_id}")


def record_link_click(user_id: int):
    VoteRepository.record_link_click(user_id)


def mark_prompted(user_id: int):
    VoteRepository.mark_prompted(user_id)


def mark_shame_shown(user_id: int):
    VoteRepository.mark_shame_shown(user_id)
