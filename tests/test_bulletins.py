"""
Tests for core/bulletins.py's store (OVERLAP-27: event_bulletin.json -> Postgres).
"""
from overlap.core import bulletins
from overlap.core.database import execute_query

GUILD_ID = 555


def _entry(head="100", **kw):
    return bulletins.BulletinMessageEntry(
        event="Game Night", msg_head_id=head, guild_id=str(GUILD_ID),
        channel_id="200", thread_id="300", **kw,
    )


def test_bulletin_round_trip_preserves_nested_thread_messages():
    thread_messages = {"901": {"options": {"1️⃣": "2027-01-01T10:00:00"}}}
    bulletins.modify_event_bulletin(GUILD_ID, _entry(thread_messages=thread_messages))

    got = bulletins.get_event_bulletin(GUILD_ID)["100"]
    assert got.event == "Game Night"
    assert got.thread_messages == thread_messages


def test_bulletin_upsert_overwrites_and_delete_reports():
    bulletins.modify_event_bulletin(GUILD_ID, _entry(thread_messages={"1": {"options": {}}}))
    bulletins.modify_event_bulletin(GUILD_ID, _entry(thread_messages={"2": {"options": {}}}))
    assert list(bulletins.get_event_bulletin(GUILD_ID)["100"].thread_messages) == ["2"]

    assert bulletins.delete_event_bulletin(GUILD_ID, "100") is True
    assert bulletins.delete_event_bulletin(GUILD_ID, "100") is False
    assert bulletins.get_event_bulletin(GUILD_ID) == {}


def test_get_event_bulletin_for_unknown_guild_is_empty_with_no_write():
    """Unlike the old JSON store, reading an unknown guild writes nothing."""
    assert bulletins.get_event_bulletin(999999) == {}
    assert execute_query("SELECT 1 FROM bulletin_entries WHERE guild_id = '999999'") == []


def test_bulletins_are_scoped_per_guild():
    bulletins.modify_event_bulletin(GUILD_ID, _entry("100"))
    other = bulletins.BulletinMessageEntry(event="X", msg_head_id="100", guild_id="1", channel_id="", thread_id="")
    bulletins.modify_event_bulletin(1, other)

    assert bulletins.get_event_bulletin(GUILD_ID)["100"].event == "Game Night"
    assert bulletins.get_event_bulletin(1)["100"].event == "X"
    assert set(bulletins.load_event_bulletins()) == {str(GUILD_ID), "1"}
