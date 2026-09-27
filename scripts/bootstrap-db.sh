#!/usr/bin/env bash
# One-time setup for a bare PostgreSQL server: create the Overlap role and database.
#
# Not needed with docker-compose (the postgres image does this from POSTGRES_DB) or with a
# managed operator such as CloudNativePG. Run it once with an admin connection, then apply
# the migrations (see overlap/db/README.md) using the role this script creates.
#
#   ADMIN_DATABASE_URL=postgresql://postgres:secret@host:5432/postgres \
#   OVERLAP_DB_PASSWORD=choose-a-password \
#   ./scripts/bootstrap-db.sh
#
# Optional: OVERLAP_DB_NAME (default overlap), OVERLAP_DB_USER (default overlap).
# Safe to re-run. The app role gets no superuser or create-database rights.

set -euo pipefail

: "${ADMIN_DATABASE_URL:?set ADMIN_DATABASE_URL to an admin connection string}"
: "${OVERLAP_DB_PASSWORD:?set OVERLAP_DB_PASSWORD}"
DB_NAME="${OVERLAP_DB_NAME:-overlap}"
DB_USER="${OVERLAP_DB_USER:-overlap}"

for name in "$DB_NAME" "$DB_USER"; do
  if ! [[ "$name" =~ ^[a-z_][a-z0-9_]*$ ]]; then
    echo "Invalid name '$name': use lowercase letters, digits and underscores." >&2
    exit 1
  fi
done

psql "$ADMIN_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -v db="$DB_NAME" -v usr="$DB_USER" -v pw="$OVERLAP_DB_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'usr', :'pw')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'usr') \gexec

SELECT format('ALTER ROLE %I PASSWORD %L', :'usr', :'pw') \gexec

SELECT format('CREATE DATABASE %I OWNER %I', :'db', :'usr')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'db') \gexec
SQL

echo "Ready: database '$DB_NAME' owned by role '$DB_USER'."
