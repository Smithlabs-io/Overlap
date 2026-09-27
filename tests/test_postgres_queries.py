"""
Tests for SQL that behaves differently on PostgreSQL than it did on SQLite:
upserts, boolean/integer flag columns, text timestamps, and cleanup queries.
Need TEST_DATABASE_URL (see conftest.py).
"""
from datetime import datetime, timedelta

import pytest

from overlap.core import conf, database, events, userdata
from overlap.core import notifications as core_notifications
from overlap.core.database import execute_one, execute_query
from overlap.core.repositories.availability import AvailabilityMemoryRepository
from overlap.core.repositories.events import EventRepository
from overlap.core.repositories.notifications import NotificationRepository

GUILD_ID = 555
USER_ID = 777


# ---------------------------------------------------------------------------
# Schema check
# ---------------------------------------------------------------------------

def test_schema_is_current():
    database.check_schema()
    assert database.get_schema_version() >= database.required_schema_version()


def test_check_schema_rejects_old_database(monkeypatch):
    monkeypatch.setattr(database, "required_schema_version", lambda: "99999999999999")
    with pytest.raises(RuntimeError, match="dbmate up"):
        database.check_schema()


def test_required_version_is_the_newest_shipped_migration():
    files = sorted(f.name for f in database.MIGRATIONS_DIR.glob("*.sql"))
    assert database.required_schema_version() == files[-1].split("_", 1)[0]


def test_overlap_now_matches_python_text_format():
    row = execute_one("SELECT overlap_now() AS now")
    parsed = datetime.strptime(row["now"], "%Y-%m-%d %H:%M:%S")
    assert abs((datetime.utcnow() - parsed).total_seconds()) < 5


# ---------------------------------------------------------------------------
# Guild config: bool <-> INTEGER flags, upsert
# ---------------------------------------------------------------------------

def test_config_round_trips_bools_and_upserts():
    cfg = conf.ServerConfigState(guild_id=str(GUILD_ID), use_24hr_time=True, bulletin_use_threads=False)
    conf.modify_config(cfg)

    fetched = conf.get_config(GUILD_ID)
    assert fetched.use_24hr_time is True
    assert fetched.bulletin_use_threads is False

    cfg.use_24hr_time = False
    conf.modify_config(cfg)  # second write must update, not duplicate
    assert conf.get_config(GUILD_ID).use_24hr_time is False
    assert len(execute_query("SELECT 1 FROM guild_configs WHERE guild_id = %s", (str(GUILD_ID),))) == 1


def test_python_bool_params_are_accepted_by_integer_columns():
    from overlap.core.database import execute_write
    execute_write("INSERT INTO guild_configs (guild_id, use_24hr_time) VALUES (%s, %s)", ("g-bool", True))
    assert execute_one("SELECT use_24hr_time AS v FROM guild_configs WHERE guild_id = 'g-bool'")["v"] == 1


# ---------------------------------------------------------------------------
# User data
# ---------------------------------------------------------------------------

def test_user_timezone_and_time_format():
    assert userdata.set_user_timezone(USER_ID, "America/Chicago") is True
    assert userdata.get_user_timezone(USER_ID) == "America/Chicago"

    from overlap.core.repositories.users import UserRepository
    assert UserRepository.set_time_format(USER_ID, True) is True
    assert UserRepository.get_time_format(USER_ID) is True
    assert UserRepository.clear_time_format(USER_ID) is True
    assert UserRepository.get_time_format(USER_ID) is None


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def _pref(**kw):
    return core_notifications.NotificationPreference(
        user_id=USER_ID, guild_id=GUILD_ID, event_name="Game Night", **kw
    )


def test_notification_preference_upsert_and_rename():
    core_notifications.set_notification_preference(_pref(reminder_minutes=30))
    core_notifications.set_notification_preference(_pref(reminder_minutes=45, notify_on_cancel=False))

    got = core_notifications.get_event_preference(USER_ID, GUILD_ID, "Game Night")
    assert got.reminder_minutes == 45
    assert got.notify_on_cancel is False
    assert len(core_notifications.get_users_to_notify(GUILD_ID, "Game Night")) == 1

    core_notifications.migrate_event_notification_preferences(GUILD_ID, "Game Night", "Board Games")
    assert core_notifications.get_event_preference(USER_ID, GUILD_ID, "Board Games") is not None


def test_scheduled_notifications_lifecycle_and_cleanup():
    kind = core_notifications.NotificationType.EVENT_REMINDER
    soon = datetime.utcnow() - timedelta(minutes=1)
    sent_id = NotificationRepository.schedule_notification(kind, USER_ID, GUILD_ID, "E", soon, "hi")
    pending_id = NotificationRepository.schedule_notification(kind, USER_ID, GUILD_ID, "E", soon, "later")

    assert {n.id for n in NotificationRepository.get_pending_notifications()} == {sent_id, pending_id}
    assert NotificationRepository.mark_notification_sent(sent_id) is True
    assert {n.id for n in NotificationRepository.get_pending_notifications()} == {pending_id}

    # A cutoff in the future makes every sent row "old"; unsent rows must survive.
    assert NotificationRepository.cleanup_sent_notifications(older_than_days=-1) == 1
    remaining = execute_query("SELECT id FROM scheduled_notifications")
    assert [r["id"] for r in remaining] == [pending_id]


# ---------------------------------------------------------------------------
# Availability patterns
# ---------------------------------------------------------------------------

def test_availability_patterns_count_up_and_cleanup():
    slots = [(1, 18), (3, 20)]
    assert AvailabilityMemoryRepository.record_availability(USER_ID, GUILD_ID, slots) is True
    assert AvailabilityMemoryRepository.record_availability(USER_ID, GUILD_ID, slots) is True

    counts = {r["count"] for r in execute_query("SELECT count FROM availability_patterns")}
    assert counts == {2}

    # Rows used a moment ago are "older" than a future cutoff, and count < 3.
    assert AvailabilityMemoryRepository.cleanup_old_patterns(older_than_days=-1) == 2
    assert execute_query("SELECT 1 FROM availability_patterns") == []


def test_old_patterns_with_high_counts_survive_cleanup():
    slot = [(2, 9)]
    for _ in range(3):
        AvailabilityMemoryRepository.record_availability(USER_ID, GUILD_ID, slot)
    assert AvailabilityMemoryRepository.cleanup_old_patterns(older_than_days=-1) == 0


def test_availability_memory_builds_up_and_suggests():
    from overlap.core import availability_memory as memory

    monday_6pm = datetime(2027, 1, 4, 18, 0)   # a Monday
    slots = [monday_6pm]
    assert memory.record_availability(USER_ID, GUILD_ID, slots) is True
    assert memory.record_availability(USER_ID, GUILD_ID, slots) is True  # second call hits ON CONFLICT

    stats = memory.get_memory_stats(USER_ID, GUILD_ID)
    assert stats is not None

    next_monday = monday_6pm + timedelta(days=7)
    other_day = monday_6pm + timedelta(days=1)
    assert memory.get_suggested_availability(USER_ID, GUILD_ID, [next_monday, other_day]) == [next_monday]

    assert memory.clear_user_memory(USER_ID, GUILD_ID) is True
    assert memory.get_user_memory(USER_ID, GUILD_ID) is None


# ---------------------------------------------------------------------------
# Event upserts (INSERT OR REPLACE / IGNORE replacements)
# ---------------------------------------------------------------------------

def _create_event(name="Upsert Event", **kw):
    event = events.EventState(
        guild_id=str(GUILD_ID), event_name=name, max_attendees="5",
        organizer=1, organizer_cname="Org", confirmed_date="TBD", **kw,
    )
    events.modify_event(event)
    return events.get_event(GUILD_ID, name)


def test_set_availability_replaces_position():
    event = _create_event()
    assert EventRepository.set_availability(event.event_id, "2027-01-01T10:00:00", "42", 1)
    assert EventRepository.set_availability(event.event_id, "2027-01-01T10:00:00", "42", 3)
    rows = execute_query("SELECT position FROM event_availability WHERE event_id = %s", (event.event_id,))
    assert [r["position"] for r in rows] == [3]


def test_add_rsvp_is_idempotent():
    event = _create_event("Rsvp Event")
    assert EventRepository.add_rsvp(event.event_id, "42")
    assert EventRepository.add_rsvp(event.event_id, "42")
    assert len(execute_query("SELECT 1 FROM event_rsvps WHERE event_id = %s", (event.event_id,))) == 1


def test_create_event_stores_message_map_and_dedupes_slots():
    slot = "2027-02-02T12:00:00"
    event = _create_event(
        "Mapped Event",
        slots=[slot, slot],
        availability={slot: {"1": "42"}},
        availability_to_message_map={slot: {"thread_id": 9, "message_id": 8, "embed_index": 0, "field_name": "f"}},
    )
    assert len(execute_query("SELECT 1 FROM event_slots WHERE event_id = %s", (event.event_id,))) == 1
    row = execute_one("SELECT message_id, thread_id FROM bulletin_message_map WHERE event_id = %s", (event.event_id,))
    assert (row["message_id"], row["thread_id"]) == ("8", "9")


def test_event_deletion_cascades():
    event = _create_event("Cascade Event")
    EventRepository.add_rsvp(event.event_id, "42")
    assert events.delete_event(GUILD_ID, "Cascade Event")
    assert execute_query("SELECT 1 FROM event_rsvps WHERE event_id = %s", (event.event_id,)) == []


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

def test_transaction_rolls_back_on_error():
    with pytest.raises(RuntimeError):
        with database.transaction() as cur:
            cur.execute("INSERT INTO user_data (user_id) VALUES ('rollback-me')")
            raise RuntimeError("boom")
    assert execute_one("SELECT 1 FROM user_data WHERE user_id = 'rollback-me'") is None


def test_nested_helpers_see_uncommitted_writes_inside_transaction():
    """Helpers called inside transaction() share its connection, as the old single connection did."""
    with database.transaction() as cur:
        cur.execute("INSERT INTO user_data (user_id) VALUES ('same-conn')")
        assert execute_one("SELECT 1 FROM user_data WHERE user_id = 'same-conn'") is not None
