# Architecture

**What it is:** a Discord event-scheduling bot and a small FastAPI web app, built from one
Python package (`overlap`) and run as two separate processes against one PostgreSQL
database.

*Verified 2026-09-27.*

## Components

| Path | Role |
|---|---|
| `overlap/bot.py` | Discord client, command registration, background tasks. Run with `python -m overlap`. |
| `overlap/config.py` | Env-based config (`DATABASE_URL`, `MAX_ACTIVE_EVENTS`, `LOG_JSON`, ...) |
| `overlap/plugins.py` | Plugin loader (entry-point group `overlap.plugins`) |
| `overlap/core/entitlements.py` | `EntitlementProvider` interface, `DefaultProvider`, `gate()` |
| `overlap/core/database.py` | psycopg pool, `transaction()`, `check_schema()` |
| `overlap/core/repositories/` | CRUD: availability, bulletins, configs, events, notifications, users |
| `overlap/core/` | Events, permissions, notifications, bulletins |
| `overlap/commands/` | Slash commands: `event`, `user`, `configs`, `bot_info` |
| `overlap/web/server.py` | FastAPI app: `/health`. Run with `python -m overlap.web`. |
| `overlap/data/timezone_data.json` | Reference data, shipped inside the package |
| `overlap/db/migrations/` | SQL schema migrations, applied with dbmate |

## Processes and images

The bot and the web app are separate processes from one image (`python -m overlap` and
`python -m overlap.web`); `dbmate up` runs from the same image. Neither process keeps local
state; everything is in PostgreSQL.

- **Bot: exactly one replica.** Two bots would open two gateway connections for one token
  and process every interaction twice. Use a `Recreate` strategy, not a rolling update.
- **Web: scale freely.** It is stateless.

## Database

PostgreSQL, reached through `DATABASE_URL` (bring your own). The bot and web app **never
create tables**. The schema is plain SQL in `overlap/db/migrations`, shipped in the package
and the image, and applied as an explicit step (`dbmate up`): a compose service, a
Kubernetes Job or init container, or by hand. At startup the bot calls `check_schema()` and
exits if the newest applied migration is older than the newest file in that directory, so
there is no version constant to keep in step.

Creating the database and role is a separate one-time step that needs elevated privileges
(`scripts/bootstrap-db.sh`). Compose and operators like CloudNativePG do it for you. The app
and its migrations run as a role with no superuser or create-database rights.

Repositories are synchronous and use a psycopg connection pool. Inside a `transaction()`
block, helper calls share that transaction's connection. Moving to an async driver is a
planned follow-up and should stay inside `database.py` and its callers.

A plugin ships its own migrations directory and applies it with a separate version table
(`dbmate --migrations-dir ... --migrations-table schema_migrations_<addon> up`), so private
tables never appear here.

## The plugin seam

Every limit and feature check goes through `core/entitlements.py`. An add-on package
registers under the `overlap.plugins` entry-point group and may:

- `setup()`: call `entitlements.set_provider(...)` to change limits and gates
- `register_commands(tree, guild)`: add slash commands (bot process)
- `register_routes(app)`: add routes (web process)

Gate points: `/export`, the notification button (`Feature.NOTIFICATIONS`), and
`/recurrence`. Limit checks: event creation. `Feature.PERSISTENT_AVAILABILITY` is checked
in `core/availability_memory.py`.

Installing the add-on is the opt-in. **A plugin that fails to import stops startup**, so a
broken add-on can never silently fall back to the free edition.

## Conventions

- All event times stored UTC, converted for display with pytz.
- Timestamp columns are UTC text (`YYYY-MM-DD HH24:MI:SS`) written via `overlap_now()`.
- Flag columns are `INTEGER` 0/1. The pool sends Python bools as integers.
- Permission levels: ATTENDEE (1) < ORGANIZER (2) < ADMIN (3).
