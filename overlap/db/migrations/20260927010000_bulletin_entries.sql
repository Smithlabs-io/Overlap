-- migrate:up

-- Posted bulletin messages (the head message, its thread, and the per-slot thread
-- messages), replacing event_bulletin.json. Keyed by guild + head message, matching
-- how core/bulletins.py looks entries up.
CREATE TABLE bulletin_entries (
    guild_id TEXT NOT NULL,
    msg_head_id TEXT NOT NULL,
    event_name TEXT NOT NULL DEFAULT '',
    channel_id TEXT NOT NULL DEFAULT '',
    thread_id TEXT NOT NULL DEFAULT '',
    thread_messages JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {THREAD_MSG_ID: {"options": {emoji: value}}}
    created_at TEXT DEFAULT overlap_now(),
    updated_at TEXT DEFAULT overlap_now(),

    PRIMARY KEY (guild_id, msg_head_id)
);

-- migrate:down

DROP TABLE bulletin_entries;
