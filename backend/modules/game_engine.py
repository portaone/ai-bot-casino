"""
Core game engine managing the European roulette game loop.

This module implements the main game logic including:
- Table management (seating, betting, phase transitions)
- European roulette rules and payout calculations
- Round settlement and balance updates
- WebSocket broadcasting for real-time updates
"""

import asyncio
import logging
import secrets
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from settings import settings
from core.types import (
    BetType,
    BetRecord,
    RoundResult,
    TablePhase,
    TableStatus,
    LeaderboardEntry,
    generate_id,
)
from core.exceptions import (
    BettingClosedError,
    InsufficientBalanceError,
    TableFullError,
    BotNotSeatedError,
    RateLimitError,
)
from modules.db import get_db_handle_bots, get_db_handle_rounds

logger = logging.getLogger(__name__)


def _get_attr(obj, key, default=None):
    """Safely get a value from either a Pydantic model or a dict."""
    if hasattr(obj, key):
        val = getattr(obj, key)
        return val if val is not None else default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


# European Roulette Constants
RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}

PAYOUT_MAP = {
    BetType.STRAIGHT: 35,
    BetType.RED: 1,
    BetType.BLACK: 1,
    BetType.EVEN: 1,
    BetType.ODD: 1,
    BetType.DOZEN_1: 2,
    BetType.DOZEN_2: 2,
    BetType.DOZEN_3: 2,
}


class Table:
    """Represents a roulette table with game state management."""

    def __init__(self, table_id: str = "main"):
        self.table_id = table_id
        self.phase = TablePhase.IDLE
        self.phase_start_time = 0.0
        self.round_number = 0
        self.seated_bots: Dict[str, Dict] = {}  # bot_id -> {bot_id, name, avatar_seed, avatar_style, joined_at}
        self.current_bets: List[BetRecord] = []
        self.last_result: Optional[RoundResult] = None
        self.last_bet_times: Dict[str, float] = {}  # bot_id -> last bet timestamp
        self.total_rounds_today = 0
        self.total_wagered_today = 0
        logger.info(f"Table {table_id} initialized")

    def join(self, bot_id: str, name: str, avatar_seed: str, avatar_style: str) -> None:
        """Add bot to table."""
        if len(self.seated_bots) >= settings.table_max_bots:
            logger.warning(f"Bot {bot_id} tried to join full table {self.table_id}")
            raise TableFullError(self.table_id, settings.table_max_bots)

        self.seated_bots[bot_id] = {
            "bot_id": bot_id,
            "name": name,
            "avatar_seed": avatar_seed,
            "avatar_style": avatar_style,
            "joined_at": time.time(),
        }
        logger.info(f"Bot {bot_id} ({name}) joined table {self.table_id}. Seated: {len(self.seated_bots)}/{settings.table_max_bots}")

    def leave(self, bot_id: str) -> None:
        """Remove bot from table."""
        if bot_id in self.seated_bots:
            bot_name = self.seated_bots[bot_id]["name"]
            del self.seated_bots[bot_id]
            if bot_id in self.last_bet_times:
                del self.last_bet_times[bot_id]
            logger.info(f"Bot {bot_id} ({bot_name}) left table {self.table_id}. Seated: {len(self.seated_bots)}/{settings.table_max_bots}")

    def is_seated(self, bot_id: str) -> bool:
        """Check if bot is seated at table."""
        return bot_id in self.seated_bots

    def place_bet(
        self,
        bot_id: str,
        bot_name: str,
        bot_avatar_seed: str,
        bet_type: BetType,
        bet_value: Optional[int],
        amount: int,
        bot_balance: int,
    ) -> BetRecord:
        """
        Validate and place a bet for a bot.

        Raises:
            BettingClosedError: If betting phase is not active
            BotNotSeatedError: If bot is not seated at table
            RateLimitError: If bot is betting too frequently
            InsufficientBalanceError: If bot lacks funds
            ValueError: If bet parameters are invalid
        """
        # Validate phase
        if self.phase != TablePhase.BETTING:
            logger.warning(f"Bot {bot_id} tried to bet during {self.phase} phase")
            raise BettingClosedError()

        # Validate seating
        if not self.is_seated(bot_id):
            logger.warning(f"Bot {bot_id} tried to bet without being seated")
            raise BotNotSeatedError(bot_id, self.table_id)

        # Rate limit check
        current_time = time.time()
        if bot_id in self.last_bet_times:
            time_since_last_bet = current_time - self.last_bet_times[bot_id]
            if time_since_last_bet < settings.bot_rate_limit_seconds:
                logger.warning(f"Bot {bot_id} hit rate limit (last bet {time_since_last_bet:.2f}s ago)")
                raise RateLimitError()

        # Validate minimum bet
        if amount < settings.bot_min_bet:
            raise ValueError(f"Bet amount {amount} is below minimum {settings.bot_min_bet}")

        # Validate straight bet value
        if bet_type == BetType.STRAIGHT:
            if bet_value is None or bet_value < 0 or bet_value > 36:
                raise ValueError(f"Straight bet value must be 0-36, got {bet_value}")

        # Calculate total committed by this bot
        existing_bets_total = sum(bet.amount for bet in self.current_bets if bet.bot_id == bot_id)
        total_required = existing_bets_total + amount

        if total_required > bot_balance:
            logger.warning(
                f"Bot {bot_id} insufficient balance: has {bot_balance}, "
                f"needs {total_required} (existing {existing_bets_total} + new {amount})"
            )
            raise InsufficientBalanceError(bot_balance, total_required)

        # Create and record bet
        bet_record = BetRecord(
            bot_id=bot_id,
            bot_name=bot_name,
            bot_avatar_seed=bot_avatar_seed,
            bet_type=bet_type,
            bet_value=bet_value,
            amount=amount,
            payout=0,
            is_winner=False,
        )

        self.current_bets.append(bet_record)
        self.last_bet_times[bot_id] = current_time

        logger.info(
            f"Bot {bot_id} placed bet: {bet_type.value}"
            f"{f'({bet_value})' if bet_value is not None else ''} "
            f"for {amount}. Total bets this round: {len(self.current_bets)}"
        )

        return bet_record

    def get_time_remaining(self) -> float:
        """Calculate time remaining in current phase."""
        if self.phase == TablePhase.IDLE:
            return 0.0

        phase_durations = {
            TablePhase.BETTING: settings.table_betting_duration,
            TablePhase.SPINNING: settings.table_spin_duration,
            TablePhase.SETTLEMENT: settings.table_settlement_duration,
            TablePhase.PAUSE: settings.table_pause_duration,
        }

        duration = phase_durations.get(self.phase, 0)
        elapsed = time.time() - self.phase_start_time
        remaining = max(0, duration - elapsed)
        return remaining

    def get_status(self) -> TableStatus:
        """Build current table status."""
        seated_bots_list = list(self.seated_bots.values())

        return TableStatus(
            table_id=self.table_id,
            phase=self.phase,
            time_remaining=self.get_time_remaining(),
            round_number=self.round_number,
            seated_bots=seated_bots_list,
            bot_count=len(self.seated_bots),
            max_bots=settings.table_max_bots,
            current_bets=self.current_bets,
            last_result=self.last_result,
            total_rounds_today=self.total_rounds_today,
            total_wagered_today=self.total_wagered_today,
        )


class GameEngine:
    """Singleton game engine managing the roulette table and game loop."""

    def __init__(self, ws_manager=None):
        self.table = Table()
        self.ws_manager = ws_manager
        self._running = False
        self._task = None
        logger.info("GameEngine initialized")

    async def run(self) -> None:
        """Main game loop managing all phases of the roulette game."""
        self._running = True
        logger.info("GameEngine starting main loop")

        try:
            while self._running:
                # IDLE: wait for bots
                while len(self.table.seated_bots) == 0 and self._running:
                    if self.table.phase != TablePhase.IDLE:
                        self.table.phase = TablePhase.IDLE
                        logger.info("Table entering IDLE phase (no bots seated)")
                    await asyncio.sleep(1)

                if not self._running:
                    break

                # BETTING phase
                self.table.phase = TablePhase.BETTING
                self.table.phase_start_time = time.time()
                self.table.current_bets = []
                self.table.round_number += 1
                logger.info(f"Round {self.table.round_number} BETTING phase started ({settings.table_betting_duration}s)")
                await self.broadcast_phase_change("betting")
                await asyncio.sleep(settings.table_betting_duration)

                if not self._running:
                    break

                # SPINNING phase
                self.table.phase = TablePhase.SPINNING
                self.table.phase_start_time = time.time()
                result_number = secrets.randbelow(37)
                result_color = "green" if result_number == 0 else ("red" if result_number in RED_NUMBERS else "black")
                logger.info(
                    f"Round {self.table.round_number} SPINNING: result is {result_number} ({result_color}). "
                    f"Bets placed: {len(self.table.current_bets)}"
                )
                await self.broadcast_phase_change("spinning", result_number, result_color)
                await asyncio.sleep(settings.table_spin_duration)

                if not self._running:
                    break

                # SETTLEMENT phase
                self.table.phase = TablePhase.SETTLEMENT
                self.table.phase_start_time = time.time()
                logger.info(f"Round {self.table.round_number} SETTLEMENT phase started")
                round_result = await self.settle_round(result_number, result_color)
                await self.broadcast_settlement(round_result)
                await asyncio.sleep(settings.table_settlement_duration)

                if not self._running:
                    break

                # PAUSE phase
                self.table.phase = TablePhase.PAUSE
                self.table.phase_start_time = time.time()
                logger.info(f"Round {self.table.round_number} PAUSE phase started")
                await self.broadcast_phase_change("pause")
                await asyncio.sleep(settings.table_pause_duration)

        except Exception as e:
            logger.error(f"GameEngine main loop error: {e}", exc_info=True)
            raise
        finally:
            logger.info("GameEngine main loop stopped")

    async def settle_round(self, result_number: int, result_color: str) -> RoundResult:
        """
        Process all bets and update bot balances.

        Returns:
            RoundResult with all bet outcomes and statistics
        """
        bots_db = get_db_handle_bots()
        rounds_db = get_db_handle_rounds()

        total_wagered = 0
        total_payout = 0
        winners_count = 0
        losers_count = 0

        logger.info(f"Settling round {self.table.round_number}: processing {len(self.table.current_bets)} bets")

        # Process each bet
        for bet in self.table.current_bets:
            total_wagered += bet.amount
            is_winner = self.check_bet_wins(bet, result_number, result_color)

            if is_winner:
                # Winner gets payout multiplier + original bet back
                payout = bet.amount * PAYOUT_MAP[bet.bet_type] + bet.amount
                bet.payout = payout
                bet.is_winner = True
                total_payout += payout
                winners_count += 1

                # Update bot balance and stats
                bot = bots_db.get(bet.bot_id)
                if bot:
                    net_win = payout - bet.amount
                    bots_db.update(bet.bot_id, {
                        "balance": _get_attr(bot, "balance", 0) + payout - bet.amount,
                        "total_wagered": _get_attr(bot, "total_wagered", 0) + bet.amount,
                        "total_won": _get_attr(bot, "total_won", 0) + net_win,
                        "rounds_played": _get_attr(bot, "rounds_played", 0) + 1,
                        "wins": _get_attr(bot, "wins", 0) + 1,
                    })
                    logger.debug(
                        f"Bot {bet.bot_id} WON: bet {bet.amount} on {bet.bet_type.value}, "
                        f"payout {payout}, net +{net_win}"
                    )
            else:
                # Loser: no payout
                bet.payout = 0
                bet.is_winner = False
                losers_count += 1

                # Update bot balance and stats
                bot = bots_db.get(bet.bot_id)
                if bot:
                    bots_db.update(bet.bot_id, {
                        "balance": _get_attr(bot, "balance", 0) - bet.amount,
                        "total_wagered": _get_attr(bot, "total_wagered", 0) + bet.amount,
                        "total_lost": _get_attr(bot, "total_lost", 0) + bet.amount,
                        "rounds_played": _get_attr(bot, "rounds_played", 0) + 1,
                        "losses": _get_attr(bot, "losses", 0) + 1,
                    })
                    logger.debug(
                        f"Bot {bet.bot_id} LOST: bet {bet.amount} on {bet.bet_type.value}"
                    )

        # Create round result
        round_result = RoundResult(
            round_id=generate_id(),
            table_id=self.table.table_id,
            round_number=self.table.round_number,
            result_number=result_number,
            result_color=result_color,
            timestamp=datetime.now(timezone.utc),
            bets=self.table.current_bets,
            total_wagered=total_wagered,
            total_payout=total_payout,
        )

        # Save to database
        rounds_db[round_result.round_id] = round_result.model_dump()

        # Update table stats
        self.table.last_result = round_result
        self.table.total_rounds_today += 1
        self.table.total_wagered_today += total_wagered

        logger.info(
            f"Round {self.table.round_number} settled: {result_number} ({result_color}). "
            f"Winners: {winners_count}, Losers: {losers_count}, "
            f"Wagered: {total_wagered}, Payout: {total_payout}, Net: {total_payout - total_wagered}"
        )

        return round_result

    def check_bet_wins(self, bet: BetRecord, number: int, color: str) -> bool:
        """
        Pure function to determine if a bet wins.

        Args:
            bet: The bet to check
            number: Winning number (0-36)
            color: Winning color ("red", "black", "green")

        Returns:
            True if bet wins, False otherwise
        """
        if bet.bet_type == BetType.STRAIGHT:
            return bet.bet_value == number
        elif bet.bet_type == BetType.RED:
            return color == "red"
        elif bet.bet_type == BetType.BLACK:
            return color == "black"
        elif bet.bet_type == BetType.EVEN:
            return number != 0 and number % 2 == 0
        elif bet.bet_type == BetType.ODD:
            return number != 0 and number % 2 == 1
        elif bet.bet_type == BetType.DOZEN_1:
            return 1 <= number <= 12
        elif bet.bet_type == BetType.DOZEN_2:
            return 13 <= number <= 24
        elif bet.bet_type == BetType.DOZEN_3:
            return 25 <= number <= 36
        else:
            return False

    async def broadcast_phase_change(
        self,
        phase: str,
        result_number: Optional[int] = None,
        result_color: Optional[str] = None,
    ) -> None:
        """Broadcast phase change to all spectators."""
        if not self.ws_manager:
            return

        data = {
            "type": "phase_change",
            "phase": phase,
            "time_remaining": self.table.get_time_remaining(),
            "round_number": self.table.round_number,
            "table_id": self.table.table_id,
            "seated_bots": list(self.table.seated_bots.values()),
            "current_bets": [bet.model_dump() for bet in self.table.current_bets],
        }

        if result_number is not None:
            data["result_number"] = result_number
        if result_color is not None:
            data["result_color"] = result_color

        await self.ws_manager.broadcast(data)
        logger.debug(f"Broadcast phase_change: {phase}, round {self.table.round_number}")

    async def broadcast_settlement(self, round_result: RoundResult) -> None:
        """Broadcast round result to all spectators."""
        if not self.ws_manager:
            return

        leaderboard = self.get_leaderboard(limit=20)

        data = {
            "type": "round_result",
            "round_id": round_result.round_id,
            "round_number": round_result.round_number,
            "result_number": round_result.result_number,
            "result_color": round_result.result_color,
            "bets": [bet.model_dump() for bet in round_result.bets],
            "total_wagered": round_result.total_wagered,
            "total_payout": round_result.total_payout,
            "leaderboard": [entry.model_dump() for entry in leaderboard],
        }

        await self.ws_manager.broadcast(data)
        logger.debug(
            f"Broadcast round_result: {round_result.result_number} ({round_result.result_color}), "
            f"{len(round_result.bets)} bets"
        )

    def get_leaderboard(self, limit: int = 20) -> List[LeaderboardEntry]:
        """
        Get top bots by balance.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of LeaderboardEntry sorted by balance descending
        """
        bots_db = get_db_handle_bots()
        all_bots = list(bots_db.values())

        # Sort by balance descending
        sorted_bots = sorted(all_bots, key=lambda b: _get_attr(b, "balance", 0), reverse=True)

        leaderboard = []
        for bot_data in sorted_bots[:limit]:
            total_won = _get_attr(bot_data, "total_won", 0)
            total_lost = _get_attr(bot_data, "total_lost", 0)
            net = total_won - total_lost

            if net > 0:
                trend = "up"
            elif net < 0:
                trend = "down"
            else:
                trend = "neutral"

            entry = LeaderboardEntry(
                bot_id=_get_attr(bot_data, "bot_id", ""),
                name=_get_attr(bot_data, "name", ""),
                avatar_seed=_get_attr(bot_data, "avatar_seed", ""),
                avatar_style=_get_attr(bot_data, "avatar_style", "bottts"),
                balance=_get_attr(bot_data, "balance", 0),
                total_wagered=_get_attr(bot_data, "total_wagered", 0),
                total_won=total_won,
                rounds_played=_get_attr(bot_data, "rounds_played", 0),
                trend=trend,
            )
            leaderboard.append(entry)

        return leaderboard

    def stop(self) -> None:
        """Stop the game engine."""
        logger.info("GameEngine stopping")
        self._running = False
