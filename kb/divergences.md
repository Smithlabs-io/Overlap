# Divergences

Gaps between docs and reality. **Add entries the moment you find one**, before
continuing. Recording is not fixing.

Format: date found · what docs say · what's true · status

---

### 2026-09-26 · This edition lags upstream
The last publish was 2026-08-18 ("full premium/Stripe scrub from public edition").
Upstream has continued since, including an aiohttp keepalive fix not present here. Treat
the version here as a periodic snapshot, not a mirror.
**Status:** open — publish cadence undecided

### 2026-09-26 · `project_state.md` / `HANDOFF.md` are uncommitted
`CLAUDE.md` treats them as live working notes, but they're gitignored, so a fresh clone
never sees them. Anything load-bearing belongs in `kb/`.
**Status:** open

### 2026-09-27 · This repo moved from SQLite to PostgreSQL; docs still say SQLite
The KB, README and CLAUDE.md all describe a single-file SQLite database. The bot now
requires PostgreSQL (`DATABASE_URL`), with the schema in `overlap/db/migrations`. Also
stale: `.env.example`'s "Feature Limits" section still names `FREE_TIER_MAX_EVENTS`,
renamed to `MAX_ACTIVE_EVENTS` in OVERLAP-17.
**Status:** open — OVERLAP-22 covers the full doc rewrite
