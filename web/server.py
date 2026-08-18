"""
Web Server for Overlap Bot.

FastAPI-based web server for:
- Vote redirect / webhook handling
- Health checks

Run standalone:
    python -m web.server

Or integrate with bot:
    from web.server import start_web_server
    await start_web_server()
"""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import config
from core.logging import get_logger

logger = get_logger(__name__)

# Static files directory
STATIC_DIR = Path(__file__).parent / "static"

# FastAPI import (optional dependency)
try:
    from fastapi import FastAPI, Request, HTTPException, Header
    from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, RedirectResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not installed. Run: pip install fastapi uvicorn")


# =============================================================================
# Application Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app):
    """Application startup and shutdown."""
    logger.info("Web server starting up...")
    yield
    logger.info("Web server shutting down...")


# =============================================================================
# Create Application
# =============================================================================

def create_app() -> Optional["FastAPI"]:
    """Create the FastAPI application."""
    if not FASTAPI_AVAILABLE:
        return None

    app = FastAPI(
        title="Overlap API",
        description="Schedule together, without the back-and-forth",
        version="1.0.0",
        lifespan=lifespan
    )

    # ==========================================================================
    # Health Endpoints
    # ==========================================================================

    @app.get("/health")
    async def health_check():
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "service": "overlap-api"
        }

    # ==========================================================================
    # Vote Redirect Endpoint (click-tracking for honor-mode shame mechanic)
    # ==========================================================================

    @app.get("/vote/redirect")
    async def vote_redirect(user_id: str, site: str):
        """
        Record that the user clicked a vote link, then redirect to the actual site.
        Only used in honor mode (VERIFY_VOTE=false) with a public WEB_BASE_URL.
        """
        from core import votes as vote_core
        try:
            vote_core.record_link_click(int(user_id))
        except Exception as e:
            logger.warning(f"Could not record vote link click for user {user_id}: {e}")

        destinations = {
            "topgg": config.TOPGG_VOTE_URL,
            "discordbots": config.DISCORDBOTS_VOTE_URL,
        }
        url = destinations.get(site, config.TOPGG_VOTE_URL)
        return RedirectResponse(url=url, status_code=302)

    # ==========================================================================
    # Top.gg / discordbotlist Vote Webhook (VERIFY_VOTE=true mode)
    # ==========================================================================

    @app.post("/webhooks/votes")
    async def vote_webhook(
        request: Request,
        authorization: str = Header(None, alias="Authorization"),
    ):
        """
        Receives vote webhooks from top.gg and discordbotlist.com.
        Configure both listing sites to POST here with their auth token.
        """
        if not config.VERIFY_VOTE:
            raise HTTPException(status_code=404, detail="Vote verification not enabled")

        if config.TOPGG_WEBHOOK_AUTH and authorization != config.TOPGG_WEBHOOK_AUTH:
            logger.warning("Vote webhook received with invalid auth token")
            raise HTTPException(status_code=401, detail="Unauthorized")

        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        user_id_str = payload.get("user") or payload.get("id")
        vote_type = payload.get("type", "upvote")

        if not user_id_str:
            raise HTTPException(status_code=400, detail="Missing user ID in payload")

        if vote_type == "test":
            logger.info(f"Vote webhook test received for user {user_id_str}")
            return {"status": "ok", "note": "test vote acknowledged"}

        try:
            from core import votes as vote_core
            vote_core.record_vote(int(user_id_str))
            logger.info(f"Vote webhook: recorded vote for user {user_id_str}")
        except Exception as e:
            logger.error(f"Failed to record vote for user {user_id_str}: {e}")
            raise HTTPException(status_code=500, detail="Failed to record vote")

        return {"status": "ok"}

    # ==========================================================================
    # Info Endpoints
    # ==========================================================================

    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Overlap",
            "tagline": "Schedule together, without the back-and-forth",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "vote_redirect": "/vote/redirect",
                "vote_webhook": "/webhooks/votes",
            },
        }

    # Mount static files if directory exists
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


# =============================================================================
# Server Runner
# =============================================================================

app = create_app()


async def start_web_server(
    host: str = None,
    port: int = None,
    log_level: str = "info"
) -> Optional[asyncio.Task]:
    """
    Start the web server as an async task.

    Returns:
        The server task, or None if FastAPI is not available
    """
    if not FASTAPI_AVAILABLE or app is None:
        logger.warning("Cannot start web server: FastAPI not installed")
        return None

    host = host or config.WEB_HOST
    port = port or config.WEB_PORT

    config_obj = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level=log_level,
        access_log=True
    )
    server = uvicorn.Server(config_obj)

    logger.info(f"Starting web server on {host}:{port}")

    task = asyncio.create_task(server.serve())
    return task


def run_server():
    """Run the web server standalone."""
    if not FASTAPI_AVAILABLE or app is None:
        print("Error: FastAPI is not installed.")
        print("Install with: pip install fastapi uvicorn")
        return

    uvicorn.run(
        "web.server:app",
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        reload=config.ENV == "development",
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
