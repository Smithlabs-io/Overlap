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

5. **Keep PRs small.** One concern per PR. Mechanical changes (file moves, import
   rewrites) go in their own PR with no logic changes mixed in.

## Repo-specific rules

- **This repo is the upstream.** Hosted-only features live in a separate private overlay
  package that plugs in through `overlap.plugins`. Nothing here imports it, and nothing
  is synced from it.
- **One bot replica, `Recreate`, forever.** Two bots mean two Discord gateway connections
  on one token. The web app is stateless and can scale.
- **This repo is public.** Nothing private belongs in it — no infrastructure hostnames,
  bucket names, internal URLs, or premium implementation detail. That includes billing,
  vote-gating and subscription code, and any add-on's tables in `overlap/db/migrations`.
- **Schema changes are migrations.** Add a new file under `overlap/db/migrations` with a
  working `down`. Never edit one that has shipped. The bot never creates tables.
- **Tests need Postgres.** Set `TEST_DATABASE_URL` to a database whose name contains
  `test`, with the migrations applied. See `README.md`.
- Never commit `project_state.md` or `HANDOFF.md`.

## At the start of every task

Read `project_state.md` and `HANDOFF.md` in this repo for current work-in-progress state and known debt. These files are not committed — they are live working notes.

## Repo structure

```
overlap/bot.py             — Discord client, command registration, background tasks
overlap/config.py          — env-based config (DATABASE_URL, MAX_ACTIVE_EVENTS, LOG_JSON, ...)
overlap/plugins.py         — plugin loader (entry-point group `overlap.plugins`)
overlap/core/              — business logic (entitlements, permissions, events, bulletins, db)
overlap/core/repositories/ — database CRUD layer
overlap/commands/          — slash command modules (event, user, configs)
overlap/web/server.py      — FastAPI app: /health (plugins add routes)
overlap/db/migrations/     — SQL schema migrations, applied with dbmate
scripts/bootstrap-db.sh    — one-time role and database setup for a bare Postgres server
```

## Editions

- **This repo** (`Smithlabs-io/Overlap`) is the community edition and the source of truth
  - All features free; one configurable active-event cap (`MAX_ACTIVE_EVENTS`, default 10)
  - No billing, no vote gates, no `/vote`
  - `core/entitlements.py` defines the `EntitlementProvider` interface and the default provider
- **Private repo** (`Smithlabs-io/Overlap-Premium`) is an overlay package
  - Depends on this repo; adds vote gating and Stripe through a plugin
  - Keeps its own migrations in a separate version table

## Important conventions

- Never commit `project_state.md` or `HANDOFF.md`
- All event times stored in UTC, converted to local on display using pytz
- Timestamp columns are UTC text written with `overlap_now()`; flag columns are `INTEGER` 0/1
- Permission levels: ATTENDEE (1) < ORGANIZER (2) < ADMIN (3)
- Every limit and feature check goes through `core/entitlements.py`
- Repositories are synchronous; inside `transaction()`, helper calls share its connection

## Observability

- Set `LOG_JSON=true` in `.env` for structured JSON output (Loki/Grafana ingestion)
- Set `LOG_JSON=false` (default) for human-readable text logs in development
- Health check: `GET /health` on the web app

## Updating handoff files

After significant changes, update:
- `project_state.md` — what changed, current feature status, known debt
- `HANDOFF.md` — what's in progress, what's next, context for the next session
