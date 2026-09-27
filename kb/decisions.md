# Decisions

## PostgreSQL, bring your own
The database is an external dependency named by `DATABASE_URL`. This lets the bot and web
app run as separate containers, gives a self-hoster their own backup story, and removes
the single-writer constraint SQLite forced. There is no dual-backend period and no
SQLite-to-Postgres data migration: the cutover happened before this project had any live
data to move.

**Consequence:** the bot needs a migrated database before it starts.

## Migrations ship with the app
The schema is plain SQL in `overlap/db/migrations`, applied with dbmate, and shipped in the
same package and image as the code, so the two cannot drift. The bot verifies the version at
startup and never creates tables. An add-on keeps its own migrations in its own directory and
version table, so private tables never appear here.

We considered a separate schema repository and rejected it: a schema repo suits a database
shared by several services. One app owns this schema.

## Database setup is separate from migrations
Creating the database and role needs elevated privileges; migrations and the app should not
have them. `scripts/bootstrap-db.sh` does the one-time setup for a bare server, and compose
and CloudNativePG do it declaratively.

## Migrations run as an explicit step
A compose service, a Job or an init container runs `dbmate up`. Auto-migrating on every app
start is fine for one replica but races once the web tier scales.

## One package, an overlay for hosted features
Overlap is the upstream. Hosted-only features (billing, vote gates) live in a separate
private package that registers through the `overlap.plugins` entry-point group. There is
no file sync and no fork, so private code cannot leak into this repo by accident.

**Consequence:** anything an add-on needs from core must be an interface here
(`EntitlementProvider`, the plugin hooks), not an import from core into the add-on.

## A failing plugin stops startup
Falling back to the free edition would silently drop any gates the add-on enforces.

## No vote gates in this edition
Vote gating only makes sense for a hosted bot that wants listings. It lives in the
overlay. This edition ships no `/vote`, no vote webhook and no click tracking.

## Times stored in UTC
Event times are stored as UTC ISO strings and converted for display. Avoids DST and
per-guild locale bugs. Changing it invalidates every stored row.

## Timestamps and flags keep their SQLite-era types
Timestamps are UTC text and flags are `INTEGER` 0/1, unchanged by the move to Postgres, so
repository logic did not have to change. Moving to `timestamptz` and `boolean` is possible
later but touches every dataclass that reads `created_at`.

## Repositories wrap all SQL
`core/repositories/` and `core/database.py` are the only places that talk to the database.

## Upsert atomically
Repository writes use `INSERT ... ON CONFLICT` rather than get-then-branch, which races
under concurrent handlers. In `DO UPDATE`, qualify a column that shares a name with an
`EXCLUDED` column (`availability_patterns.count + 1`), or Postgres reports it ambiguous.

## Sync driver first, async later
The pool is synchronous, matching the existing repository and `core/` signatures. Queries
block the event loop for a network round trip. An async migration is a separate change.
