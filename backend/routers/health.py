from fastapi import APIRouter
from settings import settings
import datetime

router = APIRouter(prefix="", tags=["monitoring"])


@router.get("/health")
async def check_health():
    """Health check endpoint to verify the service is running"""
    return {
        "status": "healthy",
        "service": "aibotcasino-api",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "mock_mode": settings.mock_mode,
    }


@router.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "AI Bot Casino API",
        "description": "The world's first online casino for AI agents",
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/api/v1/config")
async def get_config():
    """Get public configuration for the frontend."""
    return {
        "mock_mode": settings.mock_mode,
        "features": {
            "mcp": True,
            "a2a": True,
            "spectator_ws": True,
        },
        "table": {
            "betting_duration": settings.table_betting_duration,
            "max_bots": settings.table_max_bots,
            "min_bet": settings.bot_min_bet,
        },
    }


def initialize():
    """Initialize the module"""
    pass
