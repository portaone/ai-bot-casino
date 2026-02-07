"""
MCP (Model Context Protocol) server for AI Bot Casino.
Provides tools for AI agents to play roulette.
"""
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Create MCP server
mcp_server = FastMCP(
    "AI Bot Casino",
    instructions="You are playing European Roulette at AI Bot Casino. "
    "Use list_games to see available tables, join_table to sit down, "
    "place_bet during the betting window, and get_results to see outcomes. "
    "Bet types: straight (number 0-36, pays 35:1), red/black/even/odd (pays 1:1), "
    "dozen_1/dozen_2/dozen_3 (pays 2:1).",
)


def _get_engine():
    from main import game_engine
    return game_engine


def _get_bot_from_context(ctx) -> dict:
    """
    Extract bot authentication from MCP context.
    The bot API token should be passed in the Authorization header.
    Returns {"bot_id": str, "bot": BotProfile} or raises an error.
    """
    # Try to get token from request headers
    # MCP SDK passes the request context
    token = None

    # Try to extract from the transport/session context
    try:
        request = ctx.request
        if request and hasattr(request, 'headers'):
            auth_header = request.headers.get('authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
    except Exception:
        pass

    if not token:
        # Try session metadata
        try:
            session = ctx.session
            if session and hasattr(session, 'metadata'):
                token = session.metadata.get('api_token')
        except Exception:
            pass

    if not token:
        raise ValueError("No API token provided. Include Authorization: Bearer <token> header.")

    from modules.db import get_db_handle_bots
    from auth import validate_bot_api_token

    result = validate_bot_api_token(token, get_db_handle_bots())
    if not result:
        raise ValueError("Invalid API token")

    return result


@mcp_server.tool()
async def list_games(ctx) -> str:
    """List available games and tables at the casino."""
    engine = _get_engine()
    if not engine:
        return "Casino is not running."

    table = engine.table
    import json
    return json.dumps({
        "games": [{
            "game_type": "european_roulette",
            "description": "European Roulette - 37 pockets (0-36), 2.7% house edge",
            "tables": [{
                "table_id": table.table_id,
                "phase": table.phase.value,
                "bot_count": len(table.seated_bots),
                "max_bots": table.max_bots,
                "round_number": table.round_number,
            }]
        }]
    }, indent=2)


@mcp_server.tool()
async def join_table(ctx, table_id: str = "main") -> str:
    """Join a roulette table. You must join before placing bets.

    Args:
        table_id: The table to join (default: "main")
    """
    engine = _get_engine()
    if not engine:
        return "Casino is not running."

    bot_data = _get_bot_from_context(ctx)
    bot = bot_data["bot"]
    bot_id = bot_data["bot_id"]

    name = bot.name if hasattr(bot, 'name') else bot.get('name', '')
    avatar_seed = bot.avatar_seed if hasattr(bot, 'avatar_seed') else bot.get('avatar_seed', '')
    avatar_style = bot.avatar_style if hasattr(bot, 'avatar_style') else bot.get('avatar_style', 'bottts')

    try:
        engine.table.join(bot_id, name, avatar_seed, avatar_style)
        return f"Successfully joined table '{table_id}'. Wait for the betting phase to place bets."
    except Exception as e:
        return f"Failed to join table: {str(e)}"


@mcp_server.tool()
async def leave_table(ctx, table_id: str = "main") -> str:
    """Leave a roulette table.

    Args:
        table_id: The table to leave (default: "main")
    """
    engine = _get_engine()
    if not engine:
        return "Casino is not running."

    bot_data = _get_bot_from_context(ctx)
    bot_id = bot_data["bot_id"]

    engine.table.leave(bot_id)
    return f"Left table '{table_id}'."


@mcp_server.tool()
async def place_bet(ctx, bet_type: str, amount: int, bet_value: int = None) -> str:
    """Place a bet on the current round. Only works during the betting phase.

    Args:
        bet_type: Type of bet - one of: straight, red, black, even, odd, dozen_1, dozen_2, dozen_3
        amount: Amount of BotChips to wager (minimum 1)
        bet_value: For 'straight' bets only - the number to bet on (0-36)
    """
    engine = _get_engine()
    if not engine:
        return "Casino is not running."

    bot_data = _get_bot_from_context(ctx)
    bot = bot_data["bot"]
    bot_id = bot_data["bot_id"]

    from core.types import BetType
    try:
        bt = BetType(bet_type)
    except ValueError:
        return f"Invalid bet type '{bet_type}'. Valid types: {', '.join([t.value for t in BetType])}"

    name = bot.name if hasattr(bot, 'name') else bot.get('name', '')
    avatar_seed = bot.avatar_seed if hasattr(bot, 'avatar_seed') else bot.get('avatar_seed', '')
    balance = bot.balance if hasattr(bot, 'balance') else bot.get('balance', 0)

    try:
        bet_record = engine.table.place_bet(
            bot_id=bot_id,
            bot_name=name,
            bot_avatar_seed=avatar_seed,
            bet_type=bt,
            bet_value=bet_value,
            amount=amount,
            bot_balance=balance,
        )

        # Broadcast to spectators
        if engine.ws_manager:
            await engine.ws_manager.broadcast({
                "type": "new_bet",
                "bet": {
                    "bot_id": bot_id,
                    "bot_name": name,
                    "bet_type": bet_type,
                    "bet_value": bet_value,
                    "amount": amount,
                },
            })

        return f"Bet placed: {amount} BotChips on {bet_type}" + (f" ({bet_value})" if bet_value is not None else "")
    except Exception as e:
        return f"Bet failed: {str(e)}"


@mcp_server.tool()
async def get_balance(ctx) -> str:
    """Get your current BotChips balance and bot profile info."""
    bot_data = _get_bot_from_context(ctx)
    bot = bot_data["bot"]

    import json
    data = bot.model_dump() if hasattr(bot, 'model_dump') else dict(bot)
    # Remove sensitive hash
    data.pop("api_token_hash", None)
    return json.dumps(data, indent=2, default=str)


@mcp_server.tool()
async def get_results(ctx, round_id: str = None) -> str:
    """Get the latest round results or a specific round.

    Args:
        round_id: Optional specific round ID. If omitted, returns the latest result.
    """
    engine = _get_engine()
    if not engine:
        return "Casino is not running."

    import json

    if round_id:
        from modules.db import get_db_handle_rounds
        rounds_db = get_db_handle_rounds()
        round_data = rounds_db.get(round_id)
        if round_data is None:
            return f"Round {round_id} not found."
        data = round_data.model_dump() if hasattr(round_data, 'model_dump') else dict(round_data)
        return json.dumps(data, indent=2, default=str)

    if engine.table.last_result is None:
        return "No rounds played yet."

    return json.dumps(engine.table.last_result.model_dump(), indent=2, default=str)


@mcp_server.tool()
async def get_table_status(ctx, table_id: str = "main") -> str:
    """Get the current status of a roulette table including phase, time remaining, and seated bots.

    Args:
        table_id: The table ID (default: "main")
    """
    engine = _get_engine()
    if not engine:
        return "Casino is not running."

    import json
    status = engine.table.get_status()
    return json.dumps(status.model_dump(), indent=2, default=str)


@mcp_server.tool()
async def request_refill(ctx) -> str:
    """Request a BotChips refill. Only available when balance is 0 and 24h cooldown has passed."""
    bot_data = _get_bot_from_context(ctx)
    bot_id = bot_data["bot_id"]

    from modules.bot import request_refill as do_refill
    try:
        updated = do_refill(bot_id)
        balance = updated.balance if hasattr(updated, 'balance') else updated.get('balance', 0)
        return f"Refill successful! New balance: {balance} BotChips."
    except Exception as e:
        return f"Refill failed: {str(e)}"
