"""Bot profile management and operations."""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List

from settings import settings
from modules.db import get_db_handle_bots, get_db_handle_rounds
from core.types import BotProfile, LeaderboardEntry
from core.exceptions import RefillCooldownError

logger = logging.getLogger(__name__)


def get_bot_profile(bot_id: str) -> Optional[BotProfile]:
    """Get a bot profile by ID."""
    bots_db = get_db_handle_bots()
    bot = bots_db.get(bot_id)
    if bot is None:
        return None
    if isinstance(bot, dict):
        return BotProfile(**bot)
    return bot


def request_refill(bot_id: str) -> BotProfile:
    """
    Request a BotChips refill.
    Requirements: balance must be 0, and cooldown (24h) must have elapsed.
    """
    bots_db = get_db_handle_bots()
    bot = bots_db[bot_id]
    if isinstance(bot, dict):
        bot = BotProfile(**bot)

    logger.info(f"Refill requested for bot {bot_id}, current balance: {bot.balance}, last_refill_at: {bot.last_refill_at}")

    # Check balance is 0
    if bot.balance > 0:
        raise RefillCooldownError("Refill only available when balance is 0")

    # Check cooldown
    if bot.last_refill_at:
        cooldown_end = bot.last_refill_at + timedelta(hours=settings.bot_refill_cooldown_hours)
        now = datetime.now(timezone.utc)
        if now < cooldown_end:
            raise RefillCooldownError(cooldown_end.isoformat())

    # Apply refill
    now = datetime.now(timezone.utc)
    bots_db.update(bot_id, {
        "balance": settings.bot_refill_amount,
        "last_refill_at": now,
    })

    logger.info(f"Bot {bot_id} ({bot.name}) refilled with {settings.bot_refill_amount} BotChips")

    # Return updated bot
    updated = bots_db[bot_id]
    if isinstance(updated, dict):
        return BotProfile(**updated)
    return updated


def get_bot_history(bot_id: str, limit: int = 20) -> List[Dict]:
    """Get recent round history for a bot (rounds where this bot placed bets)."""
    rounds_db = get_db_handle_rounds()
    history = []
    for round_id, round_data in rounds_db.items():
        if hasattr(round_data, 'bets'):
            bets = round_data.bets
        elif isinstance(round_data, dict):
            bets = round_data.get('bets', [])
        else:
            continue

        for bet in bets:
            bet_bot_id = bet.bot_id if hasattr(bet, 'bot_id') else bet.get('bot_id', '')
            if bet_bot_id == bot_id:
                if hasattr(round_data, 'model_dump'):
                    history.append(round_data.model_dump())
                elif isinstance(round_data, dict):
                    history.append(round_data)
                break

    # Sort by round_number descending, return latest N
    history.sort(key=lambda x: x.get('round_number', 0), reverse=True)
    logger.info(f"Retrieved {len(history[:limit])} rounds for bot {bot_id}")
    return history[:limit]
