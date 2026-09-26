# Data flow

*Verified against source 2026-09-26.*

## Tables

`schema_version`, `guild_configs`, `events`, `event_slots`, `event_rsvps`,
`event_availability`, `event_waitlist`, `bulletin_message_map`, `user_data`,
`notification_preferences`, `scheduled_notifications`, `availability_patterns`,
`user_votes`

Created with `CREATE TABLE IF NOT EXISTS` at startup, so a fresh `DATA_DIR`
self-initialises. Migrations are tracked in `schema_version`.

## HTTP routes (`web/server.py`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Root |
| GET | `/health` | Liveness/readiness target |
| GET | `/vote/redirect` | Vote link handoff |
| POST | `/webhooks/votes` | Vote ingestion |

## Flows

**Event lifecycle:** slash command → `commands/event/*` → `core/events.py` →
`core/repositories/events.py` → SQLite. Bulletins render to a Discord message; the
message ID is stored in `bulletin_message_map` and mirrored to `event_bulletin.json`.

**Entitlements:** free-tier limits come from `FEATURE_LIMITS`, which reads config **at
import time**. A config value referenced there but missing crashes at module load, not
at first use.

**Notifications:** a background task registered in `bot.py` polls
`scheduled_notifications`; per-user opt-in lives in `notification_preferences`.

## Writes outside SQLite

`core/storage.py` writes `event_bulletin.json` into `DATA_DIR`. Any backup covering only
the database file misses it.
