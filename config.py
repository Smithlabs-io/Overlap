"""
Configuration module for Event Bot.

Loads settings from environment variables with sensible defaults.
"""
import os
from pathlib import Path
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
# Data Storage
# =============================================================================

# Base directory for data files
DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

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
FREE_TIER_MAX_EVENTS = int(os.getenv("FREE_TIER_MAX_EVENTS", "25"))

# Web server for vote redirect, health checks
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))
WEB_BASE_URL = os.getenv("WEB_BASE_URL", f"http://localhost:{WEB_PORT}")

# =============================================================================
# Vote Tracking
# =============================================================================

# Set VERIFY_VOTE=true to require top.gg/discordbotlist webhook verification.
# False (default) = honor system with click-tracking + shame mechanic.
VERIFY_VOTE = os.getenv("VERIFY_VOTE", "false").lower() == "true"

# Secret token top.gg sends in the Authorization header when POSTing a vote webhook.
TOPGG_WEBHOOK_AUTH = os.getenv("TOPGG_WEBHOOK_AUTH")

# Vote page URLs — fill these in once the bot is listed.
TOPGG_VOTE_URL = os.getenv("TOPGG_VOTE_URL", "https://top.gg/bot/1359004428044079126/vote")
DISCORDBOTS_VOTE_URL = os.getenv("DISCORDBOTS_VOTE_URL", "https://discordbotlist.com/bots/1359004428044079126/upvote")

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

    return errors
