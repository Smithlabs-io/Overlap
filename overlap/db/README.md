# Database migrations

The PostgreSQL schema for Overlap. Migrations are plain SQL files applied with
[dbmate](https://github.com/amacneil/dbmate). They ship inside the package and the image, so
the schema always matches the code.

The bot and web app never create tables. At startup the bot compares the database against
the newest file in `migrations/` and exits if it is behind.

## Apply them

```bash
export DATABASE_URL="postgres://user:pass@host:5432/overlap?sslmode=disable"
export DBMATE_MIGRATIONS_DIR=overlap/db/migrations DBMATE_NO_DUMP_SCHEMA=true
dbmate up
```

The Docker image sets both variables already, so `dbmate up` works as a command in it.

To create the database and role first, see `scripts/bootstrap-db.sh`. Compose and CNPG
create them for you.

## Writing a migration

- One file per change: `<timestamp>_<description>.sql`, with `-- migrate:up` and
  `-- migrate:down` sections. `dbmate new <description>` creates one.
- Never edit a migration that has shipped. Add a new one.
- Every migration needs a working `down`. CI applies, rolls back and re-applies all of them.
- Timestamps are UTC text (`YYYY-MM-DD HH24:MI:SS`). Use `overlap_now()` for defaults and
  `updated_at`.
- Flag columns are `INTEGER` 0/1, not `BOOLEAN`. The pool sends Python bools as integers.

## Add-on migrations

A plugin that needs its own tables ships its own migrations directory and applies it with a
separate version table, so the two histories never collide:

```bash
dbmate --migrations-dir /path/to/addon/migrations --migrations-table schema_migrations_addon up
```

Add-on tables never go in this directory.
