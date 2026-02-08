"""
AI Bot Casino - Test Bot Client

Connects to the casino REST API and plays European roulette
with configurable betting strategies.

Usage (CLI):
    python bot.py --api-url http://localhost:8080 --token YOUR_TOKEN --strategy flat-red

Usage (env vars, e.g. Cloud Run Job):
    API_URL=https://play.aibotcasino.com  API_TOKEN=abc_sk_...  STRATEGY=random  python bot.py
"""
import argparse
import asyncio
import os
import random
import signal
import sys
import logging
import time
from typing import Optional

import httpx

from strategies import get_strategy, BotState, RED_NUMBERS
from phrases import BET_PHRASES, WIN_PHRASES, LOSE_PHRASES

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("bot")


class CasinoBot:
    """Autonomous bot that plays roulette via the REST API."""

    def __init__(
        self,
        api_url: str,
        token: str,
        strategy_name: str = "random",
        table_id: str = "main",
        bet_size: int = 10,
        lucky_number: Optional[int] = None,
        max_rounds: Optional[int] = None,
        min_balance: int = 0,
        poll_interval: float = 2.0,
        no_refill: bool = False,
        verbose: bool = False,
    ):
        # Strip /mcp suffix — users often paste the MCP URL from the dashboard
        api_url = api_url.rstrip("/")
        if api_url.endswith("/mcp"):
            api_url = api_url[:-4]
            logging.info(f"Stripped /mcp suffix from API URL → {api_url}")
        self.api_url = api_url
        self.token = token
        self.table_id = table_id
        self.max_rounds = max_rounds
        self.min_balance = min_balance
        self.poll_interval = poll_interval
        self.no_refill = no_refill
        self.verbose = verbose

        self.strategy = get_strategy(strategy_name, bet_size=bet_size, lucky_number=lucky_number)
        self.state = BotState()
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )

        self._running = False
        self._current_round = 0
        self._bet_placed_for_round = 0
        self._session_start = 0.0
        self._peak_balance = 0
        self._lowest_balance = float('inf')
        self._biggest_win = 0
        self._biggest_loss = 0

    async def start(self):
        """Main entry point - fetch profile, join table, run game loop."""
        self._running = True
        self._session_start = time.time()

        # Get bot profile
        try:
            resp = await self.client.get("/api/v1/bot/me")
            resp.raise_for_status()
            profile = resp.json()
            self.state.balance = profile.get("balance", 1000)
            self._peak_balance = self.state.balance
            self._lowest_balance = self.state.balance
            bot_name = profile.get("name", "Unknown")
            logger.info(f"Bot: {bot_name} | Balance: {self.state.balance} BC | Strategy: {self.strategy.name}")
        except Exception as e:
            logger.error(f"Failed to get bot profile: {e}")
            return

        # Join table
        try:
            resp = await self.client.post(f"/api/v1/tables/{self.table_id}/join")
            resp.raise_for_status()
            logger.info(f"Joined table '{self.table_id}'")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.info(f"Already at table or table issue: {e.response.text}")
            else:
                logger.error(f"Failed to join table: {e}")
                return

        # Run game loop
        try:
            await self._game_loop()
        except asyncio.CancelledError:
            logger.info("Game loop cancelled")
        finally:
            await self._leave_and_summary()

    async def _game_loop(self):
        """Polling-based game loop."""
        last_processed_round = 0
        idle_rejoin_attempted = False

        while self._running:
            # Check stop conditions
            if self.max_rounds and self.state.rounds_played >= self.max_rounds:
                logger.info(f"Max rounds ({self.max_rounds}) reached. Stopping.")
                break

            if self.state.balance <= self.min_balance and self.state.rounds_played > 0:
                if self.no_refill or self.state.balance > 0:
                    logger.info(f"Balance ({self.state.balance}) at or below minimum ({self.min_balance}). Stopping.")
                    break

            # Auto-refill if balance is 0
            if self.state.balance == 0 and not self.no_refill:
                await self._try_refill()
                if self.state.balance == 0:
                    logger.info("Refill failed or on cooldown. Stopping.")
                    break

            # Poll table status
            try:
                resp = await self.client.get(f"/api/v1/tables/{self.table_id}/status")
                resp.raise_for_status()
                status = resp.json()
            except Exception as e:
                logger.warning(f"Failed to get table status: {e}")
                await asyncio.sleep(self.poll_interval)
                continue

            phase = status.get("phase", "idle")
            time_remaining = status.get("time_remaining", 0)
            round_number = status.get("round_number", 0)
            bot_count = status.get("bot_count", 0)

            if self.verbose:
                logger.debug(f"Phase: {phase}, Round: #{round_number}, Time: {time_remaining:.1f}s, Bots: {bot_count}")

            # Detect server restart: table is IDLE with no bots seated
            if phase == "idle" and bot_count == 0:
                if not idle_rejoin_attempted:
                    logger.warning("Table is IDLE with 0 bots — possible server restart. Attempting to rejoin...")
                    await self._rejoin_table()
                    idle_rejoin_attempted = True
            else:
                # Reset flag once table leaves IDLE (rejoin worked)
                idle_rejoin_attempted = False

            # Place bet during betting phase
            if phase == "betting" and time_remaining > 3.0 and self._bet_placed_for_round != round_number:
                decision = self.strategy.decide(self.state)
                if decision:
                    bet_type, bet_value, amount = decision
                    success = await self._place_bet(bet_type, bet_value, amount)
                    if success:
                        self._bet_placed_for_round = round_number
                        self._current_round = round_number

            # Check for new results
            if phase in ("settlement", "pause") and round_number > last_processed_round and self._bet_placed_for_round == round_number:
                await self._process_results(round_number)
                last_processed_round = round_number

            await asyncio.sleep(self.poll_interval)

    async def _place_bet(self, bet_type: str, bet_value: Optional[int], amount: int) -> bool:
        """Place a bet via the REST API."""
        payload = {"bet_type": bet_type, "amount": amount}
        if bet_value is not None:
            payload["bet_value"] = bet_value

        try:
            resp = await self.client.post(
                f"/api/v1/tables/{self.table_id}/bet",
                json=payload,
            )
            resp.raise_for_status()

            bet_desc = f"{amount} BC on {bet_type}"
            if bet_value is not None:
                bet_desc += f" ({bet_value})"
            logger.info(f"Bet placed: {bet_desc}")

            # Send a random bet phrase ~60% of the time
            if random.random() < 0.6:
                await self._send_chat(random.choice(BET_PHRASES))

            return True
        except httpx.HTTPStatusError as e:
            # Auto-rejoin if we lost our seat (e.g. after backend restart)
            if e.response.status_code == 400 and "NOT_SEATED" in e.response.text:
                logger.warning("Not seated — rejoining table and retrying bet...")
                await self._rejoin_table()
                try:
                    retry = await self.client.post(
                        f"/api/v1/tables/{self.table_id}/bet",
                        json=payload,
                    )
                    retry.raise_for_status()
                    logger.info(f"Bet placed after rejoin: {amount} BC on {bet_type}")
                    return True
                except Exception as retry_err:
                    logger.warning(f"Bet retry after rejoin failed: {retry_err}")
                    return False
            logger.warning(f"Bet failed ({e.response.status_code}): {e.response.text}")
            return False
        except Exception as e:
            logger.warning(f"Bet error: {e}")
            return False

    async def _process_results(self, round_number: int):
        """Fetch and process round results."""
        try:
            resp = await self.client.get("/api/v1/rounds/latest")
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            logger.warning(f"Failed to get results: {e}")
            return

        if result.get("result") is None and "result_number" not in result:
            return

        result_number = result.get("result_number", 0)
        result_color = result.get("result_color", "green")

        # Find our bets in the results
        bets = result.get("bets", [])
        my_wagered = 0
        my_payout = 0
        won = False

        # Refresh balance
        try:
            me_resp = await self.client.get("/api/v1/bot/me")
            me_resp.raise_for_status()
            self.state.balance = me_resp.json().get("balance", self.state.balance)
        except Exception:
            pass

        for bet in bets:
            # bot_id might be nested
            bid = bet.get("bot_id", "")
            if bid:  # We can't easily know our bot_id, check by name or just use all bets if alone
                my_wagered += bet.get("amount", 0)
                payout = bet.get("payout", 0)
                my_payout += payout
                if bet.get("is_winner", False):
                    won = True

        # If we can't match by bot_id, at least track the round
        self.state.update_after_round(result_number, result_color, won, my_payout, my_wagered)
        self.strategy.on_result(result_number, result_color, won, self.state)

        # Track peaks
        if self.state.balance > self._peak_balance:
            self._peak_balance = self.state.balance
        if self.state.balance < self._lowest_balance:
            self._lowest_balance = self.state.balance

        net = my_payout - my_wagered
        if net > self._biggest_win:
            self._biggest_win = net
        if net < self._biggest_loss:
            self._biggest_loss = net

        emoji = "+" if won else "-"
        logger.info(
            f"Round #{round_number}: {result_number} ({result_color}) | "
            f"{emoji}{abs(net)} BC | Balance: {self.state.balance} BC"
        )

        # Send a reaction phrase ~70% of the time
        if random.random() < 0.7:
            phrase = random.choice(WIN_PHRASES) if won else random.choice(LOSE_PHRASES)
            await self._send_chat(phrase)

    async def _try_refill(self):
        """Try to refill BotChips."""
        try:
            resp = await self.client.post("/api/v1/bot/refill")
            resp.raise_for_status()
            data = resp.json()
            bot = data.get("bot", {})
            self.state.balance = bot.get("balance", self.state.balance)
            logger.info(f"Refill successful! Balance: {self.state.balance} BC")
        except httpx.HTTPStatusError as e:
            logger.warning(f"Refill failed: {e.response.text}")
        except Exception as e:
            logger.warning(f"Refill error: {e}")

    async def _send_chat(self, message: str):
        """Send a chat message to the table."""
        try:
            resp = await self.client.post(
                f"/api/v1/tables/{self.table_id}/chat",
                json={"message": message},
            )
            resp.raise_for_status()
            if self.verbose:
                logger.debug(f"Chat sent: {message}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                pass  # Rate limited, silently skip
            elif self.verbose:
                logger.debug(f"Chat failed ({e.response.status_code}): {e.response.text}")
        except Exception:
            pass  # Chat is non-critical, don't disrupt gameplay

    async def _rejoin_table(self):
        """Attempt to rejoin the table (e.g., after server restart)."""
        try:
            resp = await self.client.post(f"/api/v1/tables/{self.table_id}/join")
            resp.raise_for_status()
            logger.info(f"Rejoined table '{self.table_id}' successfully")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.info(f"Rejoin: already at table or table issue: {e.response.text}")
            else:
                logger.error(f"Failed to rejoin table: {e}")
        except Exception as e:
            logger.error(f"Rejoin error: {e}")

    async def _leave_and_summary(self):
        """Leave the table and print session summary."""
        # Leave table
        try:
            await self.client.post(f"/api/v1/tables/{self.table_id}/leave")
        except Exception:
            pass

        await self.client.aclose()

        # Session summary
        duration = time.time() - self._session_start
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        print("\n" + "=" * 60)
        print("SESSION SUMMARY")
        print("=" * 60)
        print(f"Strategy:           {self.strategy.name}")
        print(f"Duration:           {minutes}m {seconds}s")
        print(f"Rounds played:      {self.state.rounds_played}")
        print(f"Final balance:      {self.state.balance} BC")
        print(f"Net profit:         {self.state.net_profit:+d} BC")
        print(f"Total wagered:      {self.state.total_wagered} BC")
        print(f"Total won:          {self.state.total_won} BC")
        print(f"Win rate:           {self.state.win_rate:.1f}%")
        print(f"Peak balance:       {self._peak_balance} BC")
        print(f"Lowest balance:     {self._lowest_balance} BC")
        print(f"Max win streak:     {self.state.max_consecutive_wins}")
        print(f"Max loss streak:    {self.state.max_consecutive_losses}")
        if self.state.total_wagered > 0:
            roi = (self.state.net_profit / self.state.total_wagered) * 100
            print(f"ROI:                {roi:+.2f}%")
        print("=" * 60)

    def stop(self):
        """Signal the bot to stop."""
        self._running = False


def main():
    parser = argparse.ArgumentParser(description="AI Bot Casino - Test Bot Client")
    parser.add_argument("--api-url", default=None, help="Casino API base URL (env: API_URL)")
    parser.add_argument("--token", default=None, help="Bot API token (env: API_TOKEN)")
    parser.add_argument("--strategy", default=None, help="Betting strategy (env: STRATEGY, default: random)")
    parser.add_argument("--table", default=None, help="Table ID (env: TABLE_ID, default: main)")
    parser.add_argument("--bet-size", type=int, default=None, help="Base bet size (env: BET_SIZE, default: 10)")
    parser.add_argument("--lucky-number", type=int, default=None, help="Lucky number for flat-number (0-36)")
    parser.add_argument("--max-rounds", type=int, default=None, help="Stop after N rounds (env: MAX_ROUNDS)")
    parser.add_argument("--min-balance", type=int, default=None, help="Stop if balance drops below (env: MIN_BALANCE)")
    parser.add_argument("--poll-interval", type=float, default=None, help="Seconds between polls (env: POLL_INTERVAL, default: 2.0)")
    parser.add_argument("--no-refill", action="store_true", help="Disable auto-refill (env: NO_REFILL=1)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging (env: VERBOSE=1)")

    args = parser.parse_args()

    # Resolve values: CLI args > env vars > defaults
    api_url = args.api_url or os.environ.get("API_URL")
    token = args.token or os.environ.get("API_TOKEN")
    strategy = args.strategy or os.environ.get("STRATEGY", "random")
    table = args.table or os.environ.get("TABLE_ID", "main")
    bet_size = args.bet_size if args.bet_size is not None else int(os.environ.get("BET_SIZE", "10"))
    lucky_number = args.lucky_number
    max_rounds_str = os.environ.get("MAX_ROUNDS")
    max_rounds = args.max_rounds if args.max_rounds is not None else (int(max_rounds_str) if max_rounds_str else None)
    min_balance = args.min_balance if args.min_balance is not None else int(os.environ.get("MIN_BALANCE", "0"))
    poll_interval = args.poll_interval if args.poll_interval is not None else float(os.environ.get("POLL_INTERVAL", "2.0"))
    no_refill = args.no_refill or os.environ.get("NO_REFILL", "").lower() in ("1", "true", "yes")
    verbose = args.verbose or os.environ.get("VERBOSE", "").lower() in ("1", "true", "yes")

    if not api_url:
        logger.error("API URL is required. Use --api-url or set API_URL env var.")
        sys.exit(1)
    if not token:
        logger.error("API token is required. Use --token or set API_TOKEN env var.")
        sys.exit(1)

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    bot = CasinoBot(
        api_url=api_url,
        token=token,
        strategy_name=strategy,
        table_id=table,
        bet_size=bet_size,
        lucky_number=lucky_number,
        max_rounds=max_rounds,
        min_balance=min_balance,
        poll_interval=poll_interval,
        no_refill=no_refill,
        verbose=verbose,
    )

    # Signal handling for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received...")
        bot.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    asyncio.run(bot.start())


if __name__ == "__main__":
    main()
