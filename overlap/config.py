"""
Configuration module for Event Bot.

Loads settings from environment variables with sensible defaults.
"""
import os
from typing import Optional

# =============================================================================
# Environment
# =============================================================================

ENV = os.getenv("ENV", "development")  # development, production

# =============================================================================
# Discord Configuration
# =============================================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Optional: Restrict commands to a specific guild (for development/testing)
# If not set, commands sync globally (takes up to 1 hour)
DEV_GUILD_ID: Optional[int] = None
_dev_guild = os.getenv("DEV_GUILD_ID")
if _dev_guild:
    DEV_GUILD_ID = int(_dev_guild)

# =============================================================================
# Database
# =============================================================================

# PostgreSQL connection string, e.g. postgresql://user:pass@host:5432/overlap
# The schema comes from overlap/db/migrations (dbmate up); the bot never creates it.
DATABASE_URL = os.getenv("DATABASE_URL")
DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "1"))
DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "5"))

# =============================================================================
# Logging
# =============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv(
    "LOG_FORMAT",
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
# Set LOG_JSON=true to emit newline-delimited JSON (for Loki/Grafana ingestion)
LOG_JSON = os.getenv("LOG_JSON", "false").lower() == "true"

# =============================================================================
# Feature Flags / Limits
# =============================================================================

# Maximum active events per server. Raise this via environment variable.
MAX_ACTIVE_EVENTS = int(os.getenv("MAX_ACTIVE_EVENTS", "10"))

# Web server for health checks
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))
WEB_BASE_URL = os.getenv("WEB_BASE_URL", f"http://localhost:{WEB_PORT}")

# =============================================================================
# Validation
# =============================================================================

def validate_config() -> list[str]:
    """
    Validate required configuration.
    Returns a list of error messages (empty if valid).
    """
    errors = []

    if not DISCORD_TOKEN:
        errors.append("DISCORD_TOKEN environment variable is required")

    if not DATABASE_URL:
        errors.append("DATABASE_URL environment variable is required")

    return errors
