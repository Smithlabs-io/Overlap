"""
Web Server for Overlap Bot.

FastAPI-based web server for health checks.

Run standalone:
    python -m web.server

Or integrate with bot:
    from overlap.web.server import start_web_server
    await start_web_server()
"""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from overlap import __version__, config
from overlap.core.logging import get_logger

logger = get_logger(__name__)

# Static files directory
STATIC_DIR = Path(__file__).parent / "static"

# FastAPI import (optional dependency)
try:
    from fastapi import FastAPI
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
        version=__version__,
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
    # Info Endpoints
    # ==========================================================================

    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Overlap",
            "tagline": "Schedule together, without the back-and-forth",
            "version": __version__,
            "endpoints": {
                "health": "/health",
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
