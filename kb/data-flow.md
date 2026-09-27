# Data flow

*Verified against source 2026-09-27.*

## Tables

Defined by the migrations in `overlap/db/migrations/`:

`guild_configs`, `events`, `event_slots`, `event_rsvps`, `event_availability`,
`event_waitlist`, `bulletin_message_map`, `bulletin_entries`, `user_data`,
`notification_preferences`, `scheduled_notifications`, `availability_patterns`

`bulletin_entries` holds posted bulletin messages (JSONB thread-message map), keyed by
guild and head message. `bulletin_message_map` maps event slots to messages for embed
updates. They are different things.

## HTTP routes (`overlap/web/server.py`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Name and version |
| GET | `/health` | Liveness/readiness target |

Plugins add routes through `register_routes(app)`.

## Flows

**Event lifecycle:** slash command → `commands/event/*` → `core/events.py` →
`core/repositories/events.py` → PostgreSQL. Bulletins render to a Discord message; the
message ID goes to `events.bulletin_message_id`, and the bulletin's thread-message map is
stored in `bulletin_entries`.

**Event limit:** `commands/event/create.py` calls `entitlements.check_event_limit()`. The
provider decides the cap (`None` = unlimited). `DefaultProvider` returns
`MAX_ACTIVE_EVENTS`.

**Gated actions:** `/export`, the notification button and `/recurrence` call
`entitlements.gate()`. If the provider returns False it has already told the user why.

**Notifications:** a background task registered in `bot.py` polls
`scheduled_notifications`; per-user opt-in lives in `notification_preferences`.

## State outside the database

None. The bot and web app write no local files.
