# Overlap

> Schedule together, without the back-and-forth.

A Discord bot for coordinating group events. Create events, propose times, collect availability, and find when everyone can meet — all for free.

## Features

- **Create Events** — Launch a wizard to set up events with proposed dates and times
- **Smart Availability** — Users select times they're free, bot finds the overlap
- **Timezone Support** — All times shown in each user's local timezone
- **Public Bulletins** — Post events to a channel for visibility
- **Recurring Events** — Weekly, biweekly, or monthly schedules
- **Customizable Reminders** — Notifications 15min, 1hr, or 1 day before events
- **iCal Export** — Export events to Google Calendar, Outlook, or any calendar app

## Commands

### Event Management

| Command | Description |
|---------|-------------|
| `/create` | Create a new event |
| `/events [name]` | View all events or search by name |
| `/recurrence <event>` | Set a recurring schedule for a confirmed event |
| `/export <event>` | Export event to iCal (.ics) |

### User Actions

| Command | Description |
|---------|-------------|
| `/register <event>` | Select your available times |
| `/settings` | Configure your personal preferences |
| `/info` | About Overlap — version, links, support |

### Admin

| Command | Description |
|---------|-------------|
| `/server_settings` | Configure bot settings for your server |

## Quick Start

Overlap needs a PostgreSQL database. The schema ships inside the image and the package
(`overlap/db/migrations`); the bot never creates tables and refuses to start if the database
is behind.

### Docker Compose (Postgres included)

```bash
cp .env.example .env     # set DISCORD_TOKEN and POSTGRES_PASSWORD
docker compose up -d
```

One image runs three ways: Compose starts Postgres, applies the migrations (`dbmate up`),
then starts the bot (`python -m overlap`) and the web app (`python -m overlap.web`).

### Bring your own database

```bash
# 1. First time only, on a bare server: create the role and database
ADMIN_DATABASE_URL=postgresql://postgres:secret@host:5432/postgres \
OVERLAP_DB_PASSWORD=choose-a-password ./scripts/bootstrap-db.sh

# 2. Apply the schema (needs dbmate; the image includes it)
export DATABASE_URL="postgres://overlap:choose-a-password@host:5432/overlap?sslmode=disable"
export DBMATE_MIGRATIONS_DIR=overlap/db/migrations DBMATE_NO_DUMP_SCHEMA=true
dbmate up

# 3. Install and run
pip install ".[bot]"
export DISCORD_TOKEN=... DATABASE_URL=postgresql://overlap:choose-a-password@host:5432/overlap
python -m overlap
```

Step 1 is only for a bare server. Managed databases and operators such as CloudNativePG
create the database and role for you. The web app (health checks) is a separate process:
`pip install ".[web]"` then `python -m overlap.web`.

## Project Structure

```
├── overlap/
│   ├── bot.py                 # Discord client, command registration, background tasks
│   ├── config.py              # Environment configuration
│   ├── plugins.py             # Plugin hook for optional add-ons
│   ├── commands/               # Slash command handlers (event, user, configs)
│   ├── core/
│   │   ├── events.py           # Event state and operations
│   │   ├── entitlements.py     # Feature and limit checks (provider interface)
│   │   ├── bulletins.py        # Public event announcements
│   │   ├── notifications.py    # Notification scheduler
│   │   ├── database.py         # PostgreSQL pool and schema check
│   │   └── repositories/       # Data access layer
│   ├── db/migrations/          # SQL schema migrations (applied with dbmate)
│   ├── data/                   # Reference data shipped with the package
│   └── web/                    # FastAPI app (`python -m overlap.web`)
├── tests/
├── scripts/bootstrap-db.sh     # One-time role and database setup for a bare server
└── Dockerfile                  # One image: bot, web app, or `dbmate up`
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_TOKEN` | — | **Required.** Your Discord bot token |
| `DATABASE_URL` | — | **Required.** PostgreSQL connection string |
| `MAX_ACTIVE_EVENTS` | `10` | Active event cap per server |
| `DB_POOL_MIN` / `DB_POOL_MAX` | `1` / `5` | Connection pool size |
| `ENV` | `development` | `development` or `production` |
| `DEV_GUILD_ID` | — | Restrict commands to one guild (faster sync) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `LOG_JSON` | `false` | Emit JSON logs for Loki/Grafana |
| `WEB_HOST` | `0.0.0.0` | Web app bind address |
| `WEB_PORT` | `8080` | Web app port |

## Requirements

- Python 3.10+
- PostgreSQL 14+ with the migrations applied (`dbmate up`)
- discord.py 2.3+ (bot), FastAPI + Uvicorn (web app)

## Permissions

The bot needs these Discord permissions:
- Read Messages / View Channels
- Send Messages
- Embed Links
- Use Slash Commands
- Create Public Threads (for bulletins)
- Manage Threads (for bulletins)

## Running Tests

Tests that touch the database need a Postgres database with the migrations applied
(`dbmate up`). Its name must contain `test`; the suite empties its tables before every test.

```bash
pip install -e ".[bot,web,test]"
export TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/overlap_test
pytest tests/
```

Without `TEST_DATABASE_URL`, tests that need the database fail with a clear message and the
rest still run.

## Extending Overlap

Overlap has a plugin hook (`overlap.plugins` entry-point group) for add-ons that gate
features or add limits — see `overlap/core/entitlements.py` and `overlap/plugins.py`. Core
never imports an add-on; installing one is the opt-in.

## Contributing

Pull requests welcome! Please open an issue first for major changes.

## License

MIT

---

**Overlap** — Schedule together, without the back-and-forth.
