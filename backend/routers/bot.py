"""Bot API endpoints - authenticated via API token."""
import logging
from fastapi import APIRouter, Depends
from request_trace import RouteWithLogging
from auth import get_current_bot
from modules.bot import get_bot_profile, request_refill, get_bot_history
from core.types import BotProfile

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/bot",
    tags=["bot"],
    route_class=RouteWithLogging,
)


@router.get("/me")
async def bot_me(bot_data: dict = Depends(get_current_bot)):
    """Get the authenticated bot's profile."""
    bot = bot_data["bot"]
    if hasattr(bot, 'model_dump'):
        data = bot.model_dump()
    else:
        data = dict(bot)
    # Remove sensitive fields
    data.pop("api_token_hash", None)
    logger.info(f"Bot {bot_data['bot_id']} retrieved profile")
    return data


@router.post("/refill")
async def bot_refill(bot_data: dict = Depends(get_current_bot)):
    """Request a BotChips refill (balance must be 0, 24h cooldown)."""
    bot_id = bot_data["bot_id"]
    logger.info(f"Bot {bot_id} requesting refill")
    updated_bot = request_refill(bot_id)
    data = updated_bot.model_dump() if hasattr(updated_bot, 'model_dump') else dict(updated_bot)
    data.pop("api_token_hash", None)
    return {"message": "Refill successful", "bot": data}


@router.get("/history")
async def bot_history(
    limit: int = 20,
    bot_data: dict = Depends(get_current_bot)
):
    """Get recent game history for this bot."""
    bot_id = bot_data["bot_id"]
    logger.info(f"Bot {bot_id} retrieving history (limit={limit})")
    history = get_bot_history(bot_id, limit=min(limit, 100))
    return {"rounds": history, "count": len(history)}
