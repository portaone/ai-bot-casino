"""
A2A (Agent-to-Agent) protocol server for AI Bot Casino.
Implements the Google A2A protocol for agent-to-agent communication.
"""
import logging
import json
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from request_trace import RouteWithLogging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["a2a"], route_class=RouteWithLogging)

# Agent Card - describes this agent's capabilities
AGENT_CARD = {
    "name": "AI Bot Casino Dealer",
    "description": "European Roulette dealer at AI Bot Casino (aibotcasino.com). "
                   "I manage roulette tables where AI agents bet virtual BotChips. "
                   "No real money involved.",
    "url": "https://api.aibotcasino.com/a2a",
    "version": "1.0.0",
    "capabilities": {
        "streaming": False,
        "pushNotifications": False,
    },
    "skills": [
        {
            "id": "play_roulette",
            "name": "Play European Roulette",
            "description": "Join a roulette table, place bets, and receive results. "
                          "Bet types: straight (35:1), red/black/even/odd (1:1), dozens (2:1).",
            "tags": ["game", "roulette", "casino", "entertainment"],
            "examples": [
                "Join the roulette table",
                "Place a bet of 10 BotChips on red",
                "Place a straight bet on number 17 for 5 BotChips",
                "Check my balance",
                "Get the latest round results",
                "Leave the table",
            ],
        }
    ],
    "authentication": {
        "schemes": ["bearer"],
        "credentials": "Bot API token issued during registration at aibotcasino.com",
    },
}


def _get_bot_from_request(request: Request) -> dict:
    """Extract and validate bot from Authorization header."""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header[7:]
    from modules.db import get_db_handle_bots
    from auth import validate_bot_api_token

    result = validate_bot_api_token(token, get_db_handle_bots())
    if not result:
        raise HTTPException(status_code=401, detail="Invalid API token")

    return result


def _get_engine():
    from main import game_engine
    return game_engine


async def _process_task(message: str, bot_data: dict) -> str:
    """Process an A2A task message and return a response."""
    engine = _get_engine()
    if not engine:
        return "The casino is currently offline. Please try again later."

    bot = bot_data["bot"]
    bot_id = bot_data["bot_id"]
    name = bot.name if hasattr(bot, 'name') else bot.get('name', '')
    avatar_seed = bot.avatar_seed if hasattr(bot, 'avatar_seed') else bot.get('avatar_seed', '')
    avatar_style = bot.avatar_style if hasattr(bot, 'avatar_style') else bot.get('avatar_style', 'bottts')
    balance = bot.balance if hasattr(bot, 'balance') else bot.get('balance', 0)

    msg_lower = message.lower().strip()

    # Parse intent from message
    if any(word in msg_lower for word in ["join", "sit", "enter"]):
        try:
            engine.table.join(bot_id, name, avatar_seed, avatar_style)
            status = engine.table.get_status()
            return (f"Welcome to the table, {name}! "
                    f"Phase: {status.phase.value}, Round #{status.round_number}. "
                    f"Your balance: {balance} BotChips. "
                    f"Wait for the betting phase to place your bets.")
        except Exception as e:
            return f"Could not join the table: {str(e)}"

    elif any(word in msg_lower for word in ["leave", "quit", "exit"]):
        engine.table.leave(bot_id)
        return f"You've left the table. See you next time, {name}!"

    elif any(word in msg_lower for word in ["bet", "wager", "place"]):
        # Try to parse bet from message
        from core.types import BetType
        bet_type = None
        bet_value = None
        amount = 10  # default

        # Parse bet type
        for bt in BetType:
            if bt.value.replace("_", " ") in msg_lower or bt.value in msg_lower:
                bet_type = bt
                break

        if bet_type is None:
            if "red" in msg_lower:
                bet_type = BetType.RED
            elif "black" in msg_lower:
                bet_type = BetType.BLACK
            elif "even" in msg_lower:
                bet_type = BetType.EVEN
            elif "odd" in msg_lower:
                bet_type = BetType.ODD
            elif "dozen" in msg_lower:
                if "1" in msg_lower or "first" in msg_lower:
                    bet_type = BetType.DOZEN_1
                elif "2" in msg_lower or "second" in msg_lower:
                    bet_type = BetType.DOZEN_2
                elif "3" in msg_lower or "third" in msg_lower:
                    bet_type = BetType.DOZEN_3

        # Parse number for straight bets
        import re
        numbers = re.findall(r'\b(\d+)\b', message)
        for n in numbers:
            n_int = int(n)
            if 0 <= n_int <= 36 and bet_type is None:
                bet_type = BetType.STRAIGHT
                bet_value = n_int
            elif n_int > 0 and n_int <= balance:
                amount = n_int

        if bet_type is None:
            return ("I couldn't understand your bet. Please specify: "
                    "bet type (red, black, even, odd, straight, dozen_1/2/3) "
                    "and amount. Example: 'Bet 10 on red'")

        try:
            bet_record = engine.table.place_bet(
                bot_id=bot_id,
                bot_name=name,
                bot_avatar_seed=avatar_seed,
                bet_type=bet_type,
                bet_value=bet_value,
                amount=amount,
                bot_balance=balance,
            )
            return (f"Bet placed: {amount} BotChips on {bet_type.value}"
                    + (f" ({bet_value})" if bet_value is not None else "")
                    + f". Good luck, {name}!")
        except Exception as e:
            return f"Bet failed: {str(e)}"

    elif any(word in msg_lower for word in ["balance", "chips", "money"]):
        return f"Your balance: {balance} BotChips, {name}."

    elif any(word in msg_lower for word in ["result", "outcome", "last", "spin"]):
        if engine.table.last_result:
            r = engine.table.last_result
            return (f"Last spin: {r.result_number} ({r.result_color}), "
                    f"Round #{r.round_number}. "
                    f"Total wagered: {r.total_wagered}, Total payout: {r.total_payout}.")
        return "No rounds played yet."

    elif any(word in msg_lower for word in ["status", "table", "phase"]):
        status = engine.table.get_status()
        return (f"Table '{status.table_id}': Phase={status.phase.value}, "
                f"Round #{status.round_number}, "
                f"Time remaining: {status.time_remaining:.1f}s, "
                f"Bots seated: {status.bot_count}/{status.max_bots}.")

    elif any(word in msg_lower for word in ["refill", "reload"]):
        from modules.bot import request_refill
        try:
            updated = request_refill(bot_id)
            new_balance = updated.balance if hasattr(updated, 'balance') else updated.get('balance', 0)
            return f"Refill successful! New balance: {new_balance} BotChips."
        except Exception as e:
            return f"Refill failed: {str(e)}"

    elif any(word in msg_lower for word in ["help", "what", "how"]):
        return ("Welcome to AI Bot Casino! I'm your roulette dealer. Here's what you can do:\n"
                "- 'join' - Sit at the roulette table\n"
                "- 'bet 10 on red' - Place a bet (types: red, black, even, odd, straight, dozen_1/2/3)\n"
                "- 'balance' - Check your BotChips\n"
                "- 'results' - See the last spin\n"
                "- 'status' - See the table status\n"
                "- 'refill' - Get more chips (when balance is 0)\n"
                "- 'leave' - Leave the table")

    else:
        return ("I'm the roulette dealer at AI Bot Casino. "
                "Say 'help' to see what I can do, or 'join' to sit at the table!")


@router.get("/.well-known/agent.json")
async def get_agent_card():
    """Return the A2A agent card describing this agent's capabilities."""
    return AGENT_CARD


@router.post("/a2a")
async def handle_a2a_task(request: Request):
    """
    Handle an A2A task request.
    Expects JSON body with A2A task format.
    """
    bot_data = _get_bot_from_request(request)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Extract the task/message from A2A format
    task_id = body.get("id", "")

    # A2A message can come in different formats
    message = ""
    if "message" in body:
        msg = body["message"]
        if isinstance(msg, str):
            message = msg
        elif isinstance(msg, dict):
            # A2A format: message.parts[].text
            parts = msg.get("parts", [])
            for part in parts:
                if isinstance(part, dict) and "text" in part:
                    message += part["text"] + " "
                elif isinstance(part, str):
                    message += part + " "
            if not message and "content" in msg:
                message = msg["content"]
            if not message and "text" in msg:
                message = msg["text"]
    elif "input" in body:
        message = body["input"]
    elif "text" in body:
        message = body["text"]

    message = message.strip()
    if not message:
        message = "help"

    # Process the task
    response_text = await _process_task(message, bot_data)

    # Return A2A task response format
    return {
        "id": task_id,
        "status": {
            "state": "completed",
        },
        "artifacts": [
            {
                "parts": [
                    {"type": "text", "text": response_text}
                ]
            }
        ],
    }
