import logging
import importlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from settings import settings
from core.rqid_in_logs import AddRequestID
import os
from logging.handlers import RotatingFileHandler
from logging import Formatter

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


VERSION = "0.1.0"


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

    logging.info(f"AI Bot Casino API v{VERSION} started")

    yield

    logging.info("AI Bot Casino API shutting down...")


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
routes_to_load = ["health", "auth"]
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


if __name__ == "__main__":
    pass
