"""
Shared pytest fixtures.

Every test gets empty tables in the PostgreSQL test database (autouse).
Discord objects are mocked via helpers — import them in test files as needed.
"""
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Ensure project root is importable from any test file
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Database isolation
# ---------------------------------------------------------------------------
#
# Tests that touch the database need a PostgreSQL database with the
# migrations applied, named in TEST_DATABASE_URL. Tables are emptied before
# every test. DATABASE_URL is never used, so a real database can't be hit by
# accident; the database name must also contain "test".

@pytest.fixture(scope="session", autouse=True)
def _database():
    from psycopg.conninfo import conninfo_to_dict

    from overlap import config
    import overlap.core.database as db_mod

    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        config.DATABASE_URL = None  # DB tests fail loudly instead of using a real database
        yield None
        return

    dbname = conninfo_to_dict(url).get("dbname", "")
    if "test" not in dbname:
        pytest.exit(f"Refusing to run: TEST_DATABASE_URL database {dbname!r} must contain 'test'", returncode=2)

    config.DATABASE_URL = url
    db_mod.close_connection()
    db_mod.check_schema()
    yield url
    db_mod.close_connection()


@pytest.fixture(autouse=True)
def fresh_db(_database):
    """Empty every table before each test (when a test database is configured)."""
    if _database is None:
        yield
        return

    from overlap.core.database import get_cursor

    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT quote_ident(tablename) AS t FROM pg_tables
            WHERE schemaname = 'public' AND tablename NOT LIKE 'schema_migrations%%'
            """
        )
        tables = [row["t"] for row in cursor.fetchall()]
        cursor.execute(f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE")
    yield


# ---------------------------------------------------------------------------
# Discord mock helpers (import in tests that need them)
# ---------------------------------------------------------------------------

def make_member(role_ids=None, is_admin=False, user_id=999):
    """Return a mock discord.Member with the given roles."""
    import discord
    member = MagicMock(spec=discord.Member)
    member.id = user_id
    member.roles = []
    for rid in (role_ids or []):
        role = MagicMock()
        role.id = rid
        member.roles.append(role)
    perms = MagicMock()
    perms.administrator = is_admin
    member.guild_permissions = perms
    member.guild = MagicMock()
    member.guild.id = 12345
    return member


def make_interaction(guild_id=12345, user=None):
    """Return a mock discord.Interaction."""
    interaction = MagicMock()
    interaction.guild_id = guild_id
    interaction.user = user or make_member()
    interaction.response = AsyncMock()
    return interaction
