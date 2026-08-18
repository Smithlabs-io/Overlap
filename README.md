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
| `/vote` | Vote for Overlap on bot listing sites |
| `/info` | About Overlap — version, links, support |

### Admin

| Command | Description |
|---------|-------------|
| `/server_settings` | Configure bot settings for your server |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Required:
```env
DISCORD_TOKEN=your_discord_bot_token
```

Optional:
```env
FREE_TIER_MAX_EVENTS=25    # Active event cap per server (default: 25)
DEV_GUILD_ID=              # Restrict commands to one guild for faster sync
LOG_JSON=false             # true = JSON logs for Loki/Grafana
```

### 3. Run the Bot

```bash
python bot.py
```

## Project Structure

```
├── bot.py                    # Entry point, command registration, background tasks
├── config.py                 # Environment configuration
│
├── commands/                 # Slash command handlers
│   ├── event/               # Event management (create, list, register, export, recurrence)
│   ├── user/                # User commands (settings, notifications, vote)
│   ├── admin/               # Admin commands (server settings)
│   └── configs/             # Server configuration views
│
├── core/                    # Business logic
│   ├── events.py            # Event state and operations
│   ├── entitlements.py      # Feature access (all enabled by default)
│   ├── votes.py             # Vote tracking for /vote command
│   ├── bulletins.py         # Public event announcements
│   ├── notifications.py     # Notification scheduler
│   ├── database.py          # SQLite schema and migrations
│   └── repositories/        # Data access layer
│
└── web/                     # Web server
    └── server.py            # FastAPI app: /health, /vote/redirect, /webhooks/votes
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_TOKEN` | — | **Required.** Your Discord bot token |
| `FREE_TIER_MAX_EVENTS` | `25` | Active event cap per server |
| `ENV` | `development` | `development` or `production` |
| `DEV_GUILD_ID` | — | Restrict commands to one guild (faster sync) |
| `DATA_DIR` | `./data` | Where to store the SQLite database |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `LOG_JSON` | `false` | Emit JSON logs for Loki/Grafana |
| `WEB_HOST` | `0.0.0.0` | Web server bind address |
| `WEB_PORT` | `8080` | Web server port |
| `WEB_BASE_URL` | `http://localhost:8080` | Public URL (used for vote click-tracking) |
| `VERIFY_VOTE` | `false` | Use webhook-verified votes instead of honor mode |
| `TOPGG_WEBHOOK_AUTH` | — | Secret token for top.gg vote webhooks |

## Requirements

- Python 3.10+
- discord.py 2.3+
- SQLite (included with Python)
- FastAPI + Uvicorn (for web server — vote redirect and health check)

## Permissions

The bot needs these Discord permissions:
- Read Messages / View Channels
- Send Messages
- Embed Links
- Use Slash Commands
- Create Public Threads (for bulletins)
- Manage Threads (for bulletins)

## Running Tests

```bash
pytest tests/
```

## Contributing

Pull requests welcome! Please open an issue first for major changes.

## License

MIT

---

**Overlap** — Schedule together, without the back-and-forth.
