from typing import Any, Dict, Optional


class CasinoError(Exception):
    """Base exception for all casino errors."""

    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class BettingClosedError(CasinoError):
    def __init__(self, message: str = "Betting is closed for this round"):
        super().__init__("BETTING_CLOSED", message)


class InsufficientBalanceError(CasinoError):
    def __init__(self, balance: int, required: int):
        super().__init__(
            "INSUFFICIENT_BALANCE",
            f"Insufficient balance: have {balance}, need {required}",
            {"balance": balance, "required": required},
        )


class TableFullError(CasinoError):
    def __init__(self, table_id: str, max_bots: int):
        super().__init__(
            "TABLE_FULL",
            f"Table {table_id} is full ({max_bots} bots max)",
            {"table_id": table_id, "max_bots": max_bots},
        )


class BotNotSeatedError(CasinoError):
    def __init__(self, bot_id: str, table_id: str):
        super().__init__(
            "BOT_NOT_SEATED",
            f"Bot {bot_id} is not seated at table {table_id}",
            {"bot_id": bot_id, "table_id": table_id},
        )


class RateLimitError(CasinoError):
    def __init__(self, message: str = "Rate limit exceeded: 1 bet per second"):
        super().__init__("RATE_LIMIT_EXCEEDED", message)


class RefillCooldownError(CasinoError):
    def __init__(self, next_refill_at: str):
        super().__init__(
            "REFILL_COOLDOWN",
            "Refill is on cooldown",
            {"next_refill_at": next_refill_at},
        )
