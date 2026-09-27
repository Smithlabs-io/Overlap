-- migrate:up

-- Timestamps are stored as UTC text ("YYYY-MM-DD HH24:MI:SS"), matching what the
-- application reads and writes. overlap_now() is the single source for defaults
-- and "updated_at" writes.
CREATE FUNCTION overlap_now() RETURNS text
    LANGUAGE sql STABLE
    AS $$ SELECT to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS') $$;

-- =============================================================================
-- Guild Configuration
-- =============================================================================
CREATE TABLE guild_configs (
    guild_id TEXT PRIMARY KEY,
    admin_roles TEXT DEFAULT '[]',              -- JSON array of role IDs
    event_organizer_roles TEXT DEFAULT '[]',    -- JSON array of role IDs
    event_attendee_roles TEXT DEFAULT '[]',     -- JSON array of role IDs
    bulletin_channel TEXT,
    roles_and_permissions_settings_enabled INTEGER DEFAULT 1,
    bulletin_settings_enabled INTEGER DEFAULT 0,
    display_settings_enabled INTEGER DEFAULT 1,
    notifications_enabled INTEGER DEFAULT 1,
    default_reminder_minutes INTEGER DEFAULT 60,
    notification_channel TEXT,
    use_24hr_time INTEGER DEFAULT 0,
    bulletin_use_threads INTEGER DEFAULT 1,
    created_at TEXT DEFAULT overlap_now(),
    updated_at TEXT DEFAULT overlap_now()
);

-- =============================================================================
-- Events
-- =============================================================================
CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    guild_id TEXT NOT NULL,
    event_name TEXT NOT NULL,
    max_attendees INTEGER DEFAULT 0,
    organizer TEXT NOT NULL,                    -- User ID
    organizer_cname TEXT,                       -- Display name
    confirmed_date TEXT,                        -- ISO datetime or 'TBD'
    bulletin_channel_id TEXT,
    bulletin_message_id TEXT,
    bulletin_thread_id TEXT,
    archived_at TEXT,                           -- ISO datetime when archived, NULL if active
    created_at TEXT DEFAULT overlap_now(),
    updated_at TEXT DEFAULT overlap_now(),

    recurrence_type TEXT DEFAULT 'none' CHECK (recurrence_type IN ('none', 'daily', 'weekly', 'biweekly', 'monthly')),
    recurrence_interval INTEGER DEFAULT 1,
    recurrence_end_date TEXT,
    recurrence_occurrences INTEGER,
    parent_event_id TEXT REFERENCES events(event_id),

    UNIQUE (guild_id, event_name)
);

CREATE INDEX idx_events_guild ON events(guild_id);
CREATE INDEX idx_events_organizer ON events(organizer);
CREATE INDEX idx_events_confirmed_date ON events(confirmed_date);
CREATE INDEX idx_events_parent ON events(parent_event_id);

-- =============================================================================
-- Event Slots (proposed time slots)
-- =============================================================================
CREATE TABLE event_slots (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    slot_time TEXT NOT NULL,                    -- ISO datetime
    created_at TEXT DEFAULT overlap_now(),

    UNIQUE (event_id, slot_time)
);

CREATE INDEX idx_event_slots_event ON event_slots(event_id);

-- =============================================================================
-- Event RSVPs
-- =============================================================================
CREATE TABLE event_rsvps (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    created_at TEXT DEFAULT overlap_now(),

    UNIQUE (event_id, user_id)
);

CREATE INDEX idx_event_rsvps_event ON event_rsvps(event_id);
CREATE INDEX idx_event_rsvps_user ON event_rsvps(user_id);

-- =============================================================================
-- Event Availability (user availability per slot)
-- =============================================================================
CREATE TABLE event_availability (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    slot_time TEXT NOT NULL,                    -- ISO datetime
    user_id TEXT NOT NULL,
    position INTEGER NOT NULL,                  -- Queue position
    created_at TEXT DEFAULT overlap_now(),

    UNIQUE (event_id, slot_time, user_id)
);

CREATE INDEX idx_event_availability_event ON event_availability(event_id);
CREATE INDEX idx_event_availability_slot ON event_availability(event_id, slot_time);
CREATE INDEX idx_event_availability_user ON event_availability(user_id);

-- =============================================================================
-- Event Waitlist
-- =============================================================================
CREATE TABLE event_waitlist (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    slot_time TEXT NOT NULL,                    -- ISO datetime
    user_id TEXT NOT NULL,
    position INTEGER NOT NULL,                  -- Queue position
    created_at TEXT DEFAULT overlap_now(),

    UNIQUE (event_id, slot_time, user_id)
);

CREATE INDEX idx_event_waitlist_event ON event_waitlist(event_id);

-- =============================================================================
-- Bulletin message mapping (event slot -> message, for updating embeds)
-- =============================================================================
CREATE TABLE bulletin_message_map (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    slot_time TEXT NOT NULL,                    -- ISO datetime
    thread_id TEXT,
    message_id TEXT,
    embed_index INTEGER,
    field_name TEXT,
    created_at TEXT DEFAULT overlap_now(),

    UNIQUE (event_id, slot_time)
);

CREATE INDEX idx_bulletin_message_map_event ON bulletin_message_map(event_id);

-- =============================================================================
-- User data
-- =============================================================================
CREATE TABLE user_data (
    user_id TEXT PRIMARY KEY,
    timezone TEXT,
    use_24hr_time INTEGER,
    created_at TEXT DEFAULT overlap_now(),
    updated_at TEXT DEFAULT overlap_now()
);

-- =============================================================================
-- Notification preferences
-- =============================================================================
CREATE TABLE notification_preferences (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    event_name TEXT NOT NULL,
    reminder_minutes INTEGER DEFAULT 60,
    notify_on_start INTEGER DEFAULT 1,
    notify_on_change INTEGER DEFAULT 1,
    notify_on_cancel INTEGER DEFAULT 1,
    created_at TEXT DEFAULT overlap_now(),
    updated_at TEXT DEFAULT overlap_now(),

    UNIQUE (user_id, guild_id, event_name)
);

CREATE INDEX idx_notification_prefs_user ON notification_preferences(user_id);
CREATE INDEX idx_notification_prefs_guild_event ON notification_preferences(guild_id, event_name);

-- =============================================================================
-- Scheduled notifications
-- =============================================================================
CREATE TABLE scheduled_notifications (
    id TEXT PRIMARY KEY,
    notification_type TEXT NOT NULL CHECK (notification_type IN ('event_reminder', 'event_start', 'event_canceled', 'event_changed', 'event_confirmed')),
    user_id TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    event_name TEXT NOT NULL,
    scheduled_time TEXT NOT NULL,               -- ISO datetime
    message TEXT NOT NULL,
    sent INTEGER DEFAULT 0,
    created_at TEXT DEFAULT overlap_now()
);

CREATE INDEX idx_scheduled_notifications_time ON scheduled_notifications(scheduled_time);
CREATE INDEX idx_scheduled_notifications_sent ON scheduled_notifications(sent);

-- =============================================================================
-- Availability memory (per-user weekly patterns)
-- =============================================================================
CREATE TABLE availability_patterns (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    hour INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 23),
    count INTEGER DEFAULT 1,
    last_used TEXT DEFAULT overlap_now(),
    created_at TEXT DEFAULT overlap_now(),

    UNIQUE (user_id, guild_id, day_of_week, hour)
);

CREATE INDEX idx_availability_patterns_user_guild ON availability_patterns(user_id, guild_id);

-- migrate:down

DROP TABLE availability_patterns;
DROP TABLE scheduled_notifications;
DROP TABLE notification_preferences;
DROP TABLE user_data;
DROP TABLE bulletin_message_map;
DROP TABLE event_waitlist;
DROP TABLE event_availability;
DROP TABLE event_rsvps;
DROP TABLE event_slots;
DROP TABLE events;
DROP TABLE guild_configs;
DROP FUNCTION overlap_now();
