from datetime import datetime
from core.database import get_cursor
from core.logging import get_logger

logger = get_logger(__name__)


class VoteRepository:

    @staticmethod
    def get(user_id: int) -> dict | None:
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM user_votes WHERE user_id = ?", (str(user_id),))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def _upsert(user_id: int, **fields):
        user_id_str = str(user_id)
        with get_cursor() as cursor:
            cursor.execute(
                "INSERT OR IGNORE INTO user_votes (user_id) VALUES (?)",
                (user_id_str,),
            )
            if fields:
                set_clause = ", ".join(f"{k} = ?" for k in fields)
                set_clause += ", updated_at = datetime('now')"
                cursor.execute(
                    f"UPDATE user_votes SET {set_clause} WHERE user_id = ?",
                    list(fields.values()) + [user_id_str],
                )

    @staticmethod
    def record_vote(user_id: int):
        VoteRepository._upsert(
            user_id,
            voted_at=datetime.utcnow().isoformat(),
            link_clicked=0,
            shame_shown=0,
        )

    @staticmethod
    def record_link_click(user_id: int):
        VoteRepository._upsert(user_id, link_clicked=1)

    @staticmethod
    def mark_prompted(user_id: int):
        VoteRepository._upsert(user_id, vote_prompted=1)

    @staticmethod
    def mark_shame_shown(user_id: int):
        VoteRepository._upsert(user_id, shame_shown=1)
