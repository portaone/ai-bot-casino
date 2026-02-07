from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


class Acceptance(BaseModel):
    """Policy acceptance record."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    accepted_via: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    comment: Optional[str] = None


class RegisterUserRequest(BaseModel):
    """Registration request from a human bot owner."""
    first_name: str
    email: str
    recaptcha_token: Optional[str] = None
    callback_url: Optional[str] = None
    accepted_policies: Dict[str, bool] = Field(default_factory=dict)


class LoginUserRequest(BaseModel):
    """Login request - email only (passwordless OTP)."""
    email: str
    recaptcha_token: Optional[str] = None
    callback_url: Optional[str] = None


class OTP(BaseModel):
    """One-time password record."""
    otp_id: str
    otp: str
    otp_expires_at: datetime
    user_id: str
    registration: bool = False
    magic_token: Optional[str] = None
    magic_token_used: bool = False


class VerifyOTPRequest(BaseModel):
    """OTP verification request."""
    otp_id: str
    otp: str
    recaptcha_token: Optional[str] = None


class VerifyMagicLinkRequest(BaseModel):
    """Magic link verification request."""
    otp_id: str
    magic_token: str


class RegisterOrLoginResponse(BaseModel):
    """Response after register or login — contains OTP ID for verification."""
    otp_id: str
    otp_expires_at: datetime


class VerifyOTPResponse(BaseModel):
    """Response after successful OTP/magic link verification."""
    access_token: str
    expires_at: datetime
    api_token: Optional[str] = None
    is_new_user: bool = False


class UserInfo(BaseModel):
    """Human bot owner account."""
    id: str = Field(default_factory=generate_id)
    first_name: str = ""
    email: str = ""
    bot_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    policies: Dict[str, Any] = Field(default_factory=dict)


class BotStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class BotProfile(BaseModel):
    """AI bot profile."""
    bot_id: str = Field(default_factory=generate_id)
    owner_id: str = ""
    name: str = ""
    avatar_seed: str = ""
    avatar_style: str = "bottts"
    api_token_hash: str = ""
    balance: int = 1000
    status: BotStatus = BotStatus.OFFLINE
    last_refill_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_wagered: int = 0
    total_won: int = 0
    total_lost: int = 0
    rounds_played: int = 0
    wins: int = 0
    losses: int = 0


class BetType(str, Enum):
    STRAIGHT = "straight"
    RED = "red"
    BLACK = "black"
    EVEN = "even"
    ODD = "odd"
    DOZEN_1 = "dozen_1"
    DOZEN_2 = "dozen_2"
    DOZEN_3 = "dozen_3"


class PlaceBetRequest(BaseModel):
    """Request to place a bet."""
    bet_type: BetType
    bet_value: Optional[int] = None  # For straight bets: the number (0-36)
    amount: int = Field(ge=1, description="Bet amount in BotChips")


class BetRecord(BaseModel):
    """A single bet placed by a bot."""
    bot_id: str
    bot_name: str = ""
    bot_avatar_seed: str = ""
    bet_type: BetType
    bet_value: Optional[int] = None
    amount: int
    payout: int = 0
    is_winner: bool = False


class RoundResult(BaseModel):
    """Result of a completed roulette round."""
    round_id: str = Field(default_factory=generate_id)
    table_id: str = ""
    round_number: int = 0
    result_number: int = 0
    result_color: str = ""  # "red", "black", "green"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    bets: List[BetRecord] = Field(default_factory=list)
    total_wagered: int = 0
    total_payout: int = 0


class TablePhase(str, Enum):
    IDLE = "idle"
    BETTING = "betting"
    SPINNING = "spinning"
    SETTLEMENT = "settlement"
    PAUSE = "pause"


class TableStatus(BaseModel):
    """Current status of a roulette table."""
    table_id: str = "main"
    phase: TablePhase = TablePhase.IDLE
    time_remaining: float = 0.0
    round_number: int = 0
    seated_bots: List[Dict[str, Any]] = Field(default_factory=list)
    bot_count: int = 0
    max_bots: int = 25
    current_bets: List[BetRecord] = Field(default_factory=list)
    last_result: Optional[RoundResult] = None
    total_rounds_today: int = 0
    total_wagered_today: int = 0


class LeaderboardEntry(BaseModel):
    """A bot entry on the leaderboard."""
    bot_id: str
    name: str
    avatar_seed: str
    avatar_style: str = "bottts"
    balance: int
    total_wagered: int = 0
    total_won: int = 0
    rounds_played: int = 0
    trend: str = "neutral"  # "up", "down", "neutral"


class SetupBotRequest(BaseModel):
    """Request to set up a bot during registration step 2."""
    bot_name: str
    avatar_seed: str


class SetupBotResponse(BaseModel):
    """Response after bot setup with API credentials."""
    bot_id: str
    api_token: str  # Plain text token, shown once
    mcp_url: str = ""
