# Overlap Bot — Public Edition

## Start here — the knowledge base

**Before you touch anything, read `kb/`.** Start with `kb/README.md`, then the pages
covering the area you're changing. Form opinions after reading, not before — a confident
answer built on a skim is the failure mode this exists to prevent.

Check `kb/divergences.md` early. It lists places these docs are known to be wrong.

## Rules for every ticket

1. **Look up context first.** Read the KB pages surrounding the code you're changing.

2. **Changes to architecture, data flow, interfaces, schema, or context require a KB
   update in the same commit.** Not a follow-up ticket, not "later."

3. **Found a divergence between the KB and reality? Document it immediately.** Add a
   dated entry to `kb/divergences.md` before continuing. Recording is not the same as
   fixing — record even when you can't fix, and record even when you can. The gap itself
   is information about how the docs drift.

4. **Cite your work.** Reference the Jira key in the commit message.

## Repo-specific rules

- **This tree is generated.** It's published from a private upstream by an rsync script,
  so direct commits here are overwritten on the next publish. Read, test and propose —
  but land fixes upstream.
- **One replica, `Recreate`, forever.** Two processes means two Discord gateway
  connections and two writers on one SQLite file.
- **This repo is public.** Nothing private belongs in it — no infrastructure hostnames,
  bucket names, internal URLs, or premium implementation detail.
- Never commit `project_state.md` or `HANDOFF.md`.


## At the start of every task

Read `project_state.md` and `HANDOFF.md` in this repo for current work-in-progress state and known debt. These files are not committed — they are live working notes.

## Repo structure

```
bot.py                  — entry point, command registration, background tasks
config.py               — env-based config (FREE_TIER_MAX_EVENTS, LOG_JSON, etc.)
core/                   — business logic (entitlements, permissions, events, votes, db)
core/repositories/      — SQLite CRUD layer
commands/               — slash command modules (event, user, configs)
web/server.py           — FastAPI app, vote redirect at GET /vote/redirect
data/eventbot.db        — SQLite database (runtime, gitignored)
```

## Public vs Private split

- **This repo** (`Smithlabs-io/Overlap`) is the **community/public edition**
  - No Stripe, no payment processor, no premium gating
  - All features free for everyone — no payment code, no gating
  - `FREE_TIER_MAX_EVENTS=25` default active-event cap per server (configurable)
  - `/vote` and `/info` commands present, no vote gates
- **Private repo** (`Smithlabs-io/Overlap-Premium`) is the source of truth for full dev
  - Contains Stripe integration, vote gates, premium subscription system
  - Development happens there; stripped releases are pushed here via `scripts/publish-public.sh`

## Important conventions

- Never commit `project_state.md` or `HANDOFF.md`
- All event times stored in UTC (ISO format), converted to local on display using pytz
- Permission levels: ATTENDEE (1) < ORGANIZER (2) < ADMIN (3)
- `core/entitlements.py` is minimal — `is_premium()` and `has_feature()` always return True; only `check_event_limit()` enforces anything
- Database migrations run automatically on startup via schema version table (currently v6)

## Observability

- Set `LOG_JSON=true` in `.env` for structured JSON output (Loki/Grafana ingestion)
- Set `LOG_JSON=false` (default) for human-readable text logs in development
- Health check: `GET /health` on the web server

## Updating handoff files

After significant changes, update:
- `project_state.md` — what changed, current feature status, known debt
- `HANDOFF.md` — what's in progress, what's next, context for the next session
