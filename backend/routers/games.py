"""Game API endpoints - table management and betting."""
import logging
import re
import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from request_trace import RouteWithLogging
from auth import get_current_bot
from core.types import PlaceBetRequest

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["games"],
    route_class=RouteWithLogging,
)


def _get_engine():
    """Get the game engine instance from main module."""
    from main import game_engine
    if game_engine is None:
        raise HTTPException(status_code=503, detail="Game engine not initialized")
    return game_engine


# Chat rate limiting: bot_id -> last_message_time
_chat_rate_limits: dict[str, float] = {}
CHAT_RATE_LIMIT_SECONDS = 5.0
CHAT_MAX_LENGTH = 200

# Pattern to detect URLs, emails, and other spammy content
_URL_PATTERN = re.compile(
    r'(https?://|www\.|\.com|\.net|\.org|\.io|\.xyz|\.info|\.ru|'
    r'\.cn|\.tk|@[\w.-]+\.\w|bit\.ly|t\.co|tinyurl|discord\.gg)',
    re.IGNORECASE,
)


class ChatMessageRequest(BaseModel):
    """Chat message from a bot."""
    message: str = Field(min_length=1, max_length=CHAT_MAX_LENGTH)


def _sanitize_chat(message: str) -> str:
    """Sanitize chat message: strip whitespace, remove control characters, check for URLs."""
    # Strip and collapse whitespace
    cleaned = ' '.join(message.split())
    # Remove control characters
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
    # Check for URLs/spam patterns
    if _URL_PATTERN.search(cleaned):
        raise HTTPException(status_code=400, detail="URLs and links are not allowed in chat")
    return cleaned


@router.get("/games")
async def list_games(bot_data: dict = Depends(get_current_bot)):
    """List available games and tables."""
    engine = _get_engine()
    table = engine.table
    logger.info(f"Bot {bot_data['bot_id']} listing games")
    return {
        "games": [
            {
                "game_type": "european_roulette",
                "tables": [
                    {
                        "table_id": table.table_id,
                        "phase": table.phase.value,
                        "bot_count": len(table.seated_bots),
                        "max_bots": table.max_bots,
                    }
                ]
            }
        ]
    }


@router.post("/tables/{table_id}/join")
async def join_table(table_id: str, bot_data: dict = Depends(get_current_bot)):
    """Join a roulette table. Required before placing bets."""
    engine = _get_engine()
    bot = bot_data["bot"]
    bot_id = bot_data["bot_id"]

    # Get bot attributes safely
    name = bot.name if hasattr(bot, 'name') else bot.get('name', '')
    avatar_seed = bot.avatar_seed if hasattr(bot, 'avatar_seed') else bot.get('avatar_seed', '')
    avatar_style = bot.avatar_style if hasattr(bot, 'avatar_style') else bot.get('avatar_style', 'bottts')

    engine.table.join(bot_id, name, avatar_seed, avatar_style)

    logger.info(f"Bot {bot_id} ({name}) joined table {table_id}")
    return {"message": f"Joined table {table_id}", "table_id": table_id, "bot_id": bot_id}


@router.post("/tables/{table_id}/leave")
async def leave_table(table_id: str, bot_data: dict = Depends(get_current_bot)):
    """Leave a roulette table."""
    engine = _get_engine()
    bot_id = bot_data["bot_id"]

    engine.table.leave(bot_id)

    logger.info(f"Bot {bot_id} left table {table_id}")
    return {"message": f"Left table {table_id}", "table_id": table_id}


@router.post("/tables/{table_id}/bet")
async def place_bet(
    table_id: str,
    bet_request: PlaceBetRequest,
    bot_data: dict = Depends(get_current_bot)
):
    """Place a bet on the current round. Only valid during betting phase."""
    engine = _get_engine()
    bot = bot_data["bot"]
    bot_id = bot_data["bot_id"]

    name = bot.name if hasattr(bot, 'name') else bot.get('name', '')
    avatar_seed = bot.avatar_seed if hasattr(bot, 'avatar_seed') else bot.get('avatar_seed', '')
    balance = bot.balance if hasattr(bot, 'balance') else bot.get('balance', 0)

    logger.info(f"Bot {bot_id} ({name}) placing bet: {bet_request.bet_type.value}, amount={bet_request.amount}, balance={balance}")

    bet_record = engine.table.place_bet(
        bot_id=bot_id,
        bot_name=name,
        bot_avatar_seed=avatar_seed,
        bet_type=bet_request.bet_type,
        bet_value=bet_request.bet_value,
        amount=bet_request.amount,
        bot_balance=balance,
    )

    # Broadcast bet to spectators
    if engine.ws_manager:
        await engine.ws_manager.broadcast({
            "type": "new_bet",
            "bet": {
                "bot_id": bot_id,
                "bot_name": name,
                "bot_avatar_seed": avatar_seed,
                "bet_type": bet_record.bet_type.value,
                "bet_value": bet_record.bet_value,
                "amount": bet_record.amount,
            },
            "table_id": table_id,
        })

    return {
        "message": "Bet placed",
        "bet_type": bet_record.bet_type.value,
        "bet_value": bet_record.bet_value,
        "amount": bet_record.amount,
    }


@router.get("/tables/{table_id}/status")
async def table_status(table_id: str, bot_data: dict = Depends(get_current_bot)):
    """Get current table status including phase, bets, and results."""
    engine = _get_engine()
    status = engine.table.get_status()
    logger.info(f"Bot {bot_data['bot_id']} retrieved table {table_id} status: phase={status.phase.value}, bots={status.bot_count}")
    return status.model_dump()


@router.get("/rounds/latest")
async def latest_round(bot_data: dict = Depends(get_current_bot)):
    """Get the most recent round result."""
    engine = _get_engine()
    if engine.table.last_result is None:
        return {"message": "No rounds played yet", "result": None}
    logger.info(f"Bot {bot_data['bot_id']} retrieved latest round result")
    return engine.table.last_result.model_dump()


@router.post("/tables/{table_id}/chat")
async def send_chat(
    table_id: str,
    req: ChatMessageRequest,
    bot_data: dict = Depends(get_current_bot),
):
    """Send a chat message to the table. Rate limited to 1 message per 5 seconds."""
    engine = _get_engine()
    bot = bot_data["bot"]
    bot_id = bot_data["bot_id"]

    # Verify bot is seated at table
    if not engine.table.is_seated(bot_id):
        raise HTTPException(status_code=400, detail="Must be seated at table to chat")

    # Rate limit
    now = time.time()
    last_msg_time = _chat_rate_limits.get(bot_id, 0)
    if now - last_msg_time < CHAT_RATE_LIMIT_SECONDS:
        remaining = CHAT_RATE_LIMIT_SECONDS - (now - last_msg_time)
        raise HTTPException(
            status_code=429,
            detail=f"Chat rate limited. Try again in {remaining:.1f}s",
        )

    # Sanitize message
    cleaned = _sanitize_chat(req.message)
    if not cleaned:
        raise HTTPException(status_code=400, detail="Message is empty after sanitization")

    _chat_rate_limits[bot_id] = now

    name = bot.name if hasattr(bot, 'name') else bot.get('name', '')
    avatar_seed = bot.avatar_seed if hasattr(bot, 'avatar_seed') else bot.get('avatar_seed', '')

    # Broadcast to spectators
    if engine.ws_manager:
        await engine.ws_manager.broadcast({
            "type": "chat_message",
            "bot_id": bot_id,
            "bot_name": name,
            "bot_avatar_seed": avatar_seed,
            "message": cleaned,
            "table_id": table_id,
        })

    logger.info(f"Chat from {bot_id} ({name}): {cleaned[:50]}{'...' if len(cleaned) > 50 else ''}")
    return {"message": "sent"}
