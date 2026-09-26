# Decisions

## SQLite, not a database server
One process, one Discord gateway connection, one writer. A database server adds
operational weight and buys nothing at this scale. WAL mode handles the bot's async
single-process concurrency.

**Consequence:** one replica, always. Horizontal scaling requires moving to a database
server first.

## Times stored in UTC
Event times are stored as UTC ISO strings and converted for display. Avoids DST and
per-guild locale bugs. Changing it invalidates every stored row.

## Repositories wrap all SQL
`core/repositories/` is the only place that talks to SQLite. Business logic in `core/`
calls repositories, never `sqlite3` directly — keeps a future datastore change to one
layer.

## Upsert atomically
Repository writes use `INSERT OR IGNORE` + `UPDATE` rather than get-then-branch, which
races under concurrent handlers.
