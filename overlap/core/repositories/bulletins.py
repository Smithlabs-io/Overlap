"""
Bulletin Repository.

Persists posted bulletin messages (the head message, its thread, and the
per-slot thread messages) so they survive restarts.
"""
from typing import Dict, List

from psycopg.types.json import Jsonb

from overlap.core.database import execute_query, execute_write, get_cursor
from overlap.core.logging import get_logger

logger = get_logger(__name__)


class BulletinRepository:
    """Data access for bulletin_entries."""

    @staticmethod
    def get_all() -> List[dict]:
        """Every stored bulletin, across all guilds."""
        return execute_query(
            """
            SELECT guild_id, msg_head_id, event_name, channel_id, thread_id, thread_messages
            FROM bulletin_entries
            """
        )

    @staticmethod
    def get_for_guild(guild_id: str) -> List[dict]:
        return execute_query(
            """
            SELECT guild_id, msg_head_id, event_name, channel_id, thread_id, thread_messages
            FROM bulletin_entries
            WHERE guild_id = %s
            """,
            (guild_id,),
        )

    @staticmethod
    def upsert(
        guild_id: str,
        msg_head_id: str,
        event_name: str,
        channel_id: str,
        thread_id: str,
        thread_messages: Dict[str, Dict[str, str]],
    ) -> None:
        with get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO bulletin_entries
                    (guild_id, msg_head_id, event_name, channel_id, thread_id, thread_messages)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (guild_id, msg_head_id) DO UPDATE SET
                    event_name = EXCLUDED.event_name,
                    channel_id = EXCLUDED.channel_id,
                    thread_id = EXCLUDED.thread_id,
                    thread_messages = EXCLUDED.thread_messages,
                    updated_at = overlap_now()
                """,
                (guild_id, msg_head_id, event_name, channel_id, thread_id, Jsonb(thread_messages)),
            )

    @staticmethod
    def delete(guild_id: str, msg_head_id: str) -> bool:
        return execute_write(
            "DELETE FROM bulletin_entries WHERE guild_id = %s AND msg_head_id = %s",
            (guild_id, msg_head_id),
        ) > 0
