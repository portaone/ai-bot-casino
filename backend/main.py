import asyncio
import logging
import importlib
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from settings import settings
from core.rqid_in_logs import AddRequestID
import os
from logging.handlers import RotatingFileHandler
from logging import Formatter

from modules.game_engine import GameEngine
from modules.ws_manager import WebSocketManager

# Configure file logging if enabled
if settings.log_file:
    log_dir = os.path.dirname(settings.log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    log_format = "[%(asctime)s] %(levelname)s [Req-ID: %(request_id)s]: %(message)s"

    file_handler = RotatingFileHandler(
        settings.log_file, maxBytes=5_000_000, backupCount=5
    )
    file_handler.setFormatter(Formatter(log_format))
    file_handler.addFilter(AddRequestID())

    root_logger = logging.getLogger()

    handler_exists = any(
        isinstance(h, RotatingFileHandler) and h.baseFilename == os.path.abspath(settings.log_file)
        for h in root_logger.handlers
    )

    if not handler_exists:
        root_logger.addHandler(file_handler)

    logging.getLogger("uvicorn").propagate = True
    logging.getLogger("uvicorn.access").propagate = True
    logging.getLogger("uvicorn.error").propagate = True

# Reduce verbose logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("watchfiles").setLevel(logging.WARNING)
logging.getLogger("watchfiles.main").setLevel(logging.WARNING)


VERSION = "0.2.0"

# Global game engine and WebSocket manager instances
# These are accessed by routers via: from main import game_engine, ws_manager
game_engine: Optional[GameEngine] = None
ws_manager: Optional[WebSocketManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application on startup, cleanup on shutdown."""
    # Initialize database
    from modules.db import initialize as init_db
    init_db()

    # Initialize auth (load JWT secret)
    from auth import load_secret_key
    if settings.mock_mode and not settings.auth_jwt_secret:
        # Use a default secret in mock mode for convenience
        load_secret_key("mock-secret-key-for-development-only-change-in-production!!")
        logging.warning("Using default JWT secret for mock mode")
    else:
        load_secret_key()

    if settings.mock_mode:
        logging.info("=" * 60)
        logging.info("MOCK MODE ENABLED - Using in-memory storage")
        logging.info("=" * 60)

    # Initialize WebSocket manager and game engine
    global ws_manager, game_engine
    ws_manager = WebSocketManager()
    game_engine = GameEngine(ws_manager=ws_manager)

    # Start game engine as background task
    engine_task = asyncio.create_task(game_engine.run())
    logging.info("Game engine started as background task")

    logging.info(f"AI Bot Casino API v{VERSION} started")

    yield

    # Shutdown game engine
    logging.info("AI Bot Casino API shutting down...")
    game_engine.stop()
    engine_task.cancel()
    try:
        await engine_task
    except asyncio.CancelledError:
        pass
    logging.info("Game engine stopped")


app = FastAPI(
    title="AI Bot Casino API",
    description="The world's first online casino for AI agents. "
                "Bots register, receive BotChips, and play European roulette at shared tables.",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redocs",
    lifespan=lifespan,
)

# CORS
allowed_origins = settings.cors_allowed_origins if settings.cors_allowed_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.info(f"CORS allowed origins: {allowed_origins}")

# Load routers dynamically
routes_to_load = ["health", "auth", "bot", "games", "spectator"]
for route_name in routes_to_load:
    route_name = route_name.strip()
    if route_name:
        try:
            router_module = importlib.import_module(f"routers.{route_name}")
            if hasattr(router_module, "initialize"):
                router_module.initialize()

            if hasattr(router_module, "router"):
                if router_module.router is not None:
                    app.include_router(router_module.router)
                    logging.info(f"Loaded router: {route_name}")
            else:
                logging.error(f"Router module {route_name} has no 'router' attribute")
        except ImportError as e:
            logging.error(f"Failed to import router {route_name}: {str(e)}")
            raise e
        except Exception as e:
            logging.error(f"Error loading router {route_name}: {str(e)}")


# A2A router (at root level for /.well-known/agent.json and /a2a)
try:
    from a2a.server import router as a2a_router
    app.include_router(a2a_router)
    logging.info("Loaded A2A router")
except ImportError as e:
    logging.warning(f"A2A router not available: {e}")

# MCP server mount
try:
    from mcp.server import mcp_server
    mcp_app = mcp_server.streamable_http_app()
    app.mount("/mcp", mcp_app)
    logging.info("MCP server mounted at /mcp")
except ImportError as e:
    logging.warning(f"MCP server not available: {e}")
except Exception as e:
    logging.warning(f"Failed to mount MCP server: {e}")


if __name__ == "__main__":
    pass
