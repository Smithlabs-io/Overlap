# Architecture

**What it is:** a Discord event-scheduling bot plus a small FastAPI web server, running
as a single Python process.

*Verified 2026-09-26.*

## Components

| Path | Role |
|---|---|
| `bot.py` | Entry point: command registration, background tasks, DB init |
| `config.py` | Env-based config (`FREE_TIER_MAX_EVENTS`, `LOG_JSON`, `DATA_DIR`) |
| `core/` | Events, votes, entitlements, permissions, notifications |
| `core/database.py` | SQLite connection, schema creation, `PRAGMA journal_mode = WAL` |
| `core/repositories/` | CRUD: availability, configs, events, notifications, users, votes |
| `core/storage.py` | JSON read/write inside `DATA_DIR` |
| `commands/` | Slash commands: `admin`, `event`, `user`, `configs` |
| `web/server.py` | FastAPI: health, vote redirect, vote webhook |

## Runtime shape

One process holds the Discord gateway connection and serves HTTP, which makes it
**single-instance by nature**. Two processes would mean two gateway connections on one
shard and two writers on one SQLite file. Run one replica; if you containerise it, use a
`Recreate` strategy rather than a rolling update.

## Storage

- `data/eventbot.db` — SQLite in WAL mode. The system of record.
- `data/timezone_data.json` — read-only reference data **shipped in the image**
- `data/event_bulletin.json` — runtime state written outside SQLite

**Mounting a volume at `data/` hides files the image ships there.**
`timezone_data.json` is read at import time in `commands/user/timezone.py`, so a plain
volume mount breaks startup. Copy reference data in, or mount a subpath.

Set `PRAGMA busy_timeout` on the connection if you run anything else against the
database file — backup tools take brief locks, and without a busy timeout you get
`database is locked` instead of a wait.

## Conventions

- All event times stored UTC (ISO), converted for display with pytz.
- Permission levels: ATTENDEE (1) < ORGANIZER (2) < ADMIN (3).
