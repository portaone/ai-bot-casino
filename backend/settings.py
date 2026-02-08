from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List, Optional, Dict


class Settings(BaseSettings):
    # Application settings
    debug: bool = Field(default=False, description="Enable debug mode for detailed logging")
    app_name: str = "aibotcasino"
    cors_allowed_origins: List[str] = Field(default_factory=list, description="Allowed origins for CORS")

    # Mock mode - uses InMemoryDict instead of Firestore
    mock_mode: bool = Field(default=True, description="Enable mock mode for testing without Firestore")

    # Database settings
    database_name: str = Field(default="aibotcasino", description="Firestore database name")

    # Authentication settings
    auth_jwt_secret: Optional[str] = Field(default=None, min_length=32, description="JWT secret key (use: openssl rand -hex 32)")
    auth_otp_expires: int = Field(default=15, description="OTP expiration in minutes")
    auth_access_token_expires: int = Field(default=24 * 30, description="Access token expiration in hours")

    # Test users configuration
    test_users_enabled: bool = Field(default=False, description="Enable test users with predefined OTP")
    test_users_otp: str = Field(default="123456", description="Predefined OTP code for test users")

    # reCAPTCHA settings
    recaptcha_secret_key: Optional[str] = Field(default=None, description="Google reCAPTCHA v3 secret key")
    recaptcha_skip: bool = Field(default=False, description="Skip reCAPTCHA verification (dev only)")
    recaptcha_debug: bool = Field(default=False, description="Enable reCAPTCHA debug logging")

    # Casino game settings
    table_betting_duration: int = Field(default=30, description="Betting window duration in seconds")
    table_spin_duration: int = Field(default=5, description="Spin phase duration in seconds")
    table_settlement_duration: int = Field(default=2, description="Settlement phase duration in seconds")
    table_pause_duration: int = Field(default=3, description="Pause between rounds in seconds")
    table_max_bots: int = Field(default=25, description="Maximum bots per table")
    bot_starting_balance: int = Field(default=1000, description="Starting BotChips for new bots")
    bot_refill_amount: int = Field(default=1000, description="BotChips refill amount")
    bot_refill_cooldown_hours: int = Field(default=24, description="Hours between refills")
    bot_min_bet: int = Field(default=1, description="Minimum bet in BotChips")
    bot_rate_limit_seconds: float = Field(default=1.0, description="Minimum seconds between bets per bot")

    # Email settings
    email_mailer: Optional[str] = Field(default=None, description="Email mailer module (mailersend_mailer)")
    email_mailer_dry_run: bool = Field(default=True, description="Dry run email sending")
    email_mailersend_api_key: Optional[str] = Field(default=None, description="MailerSend API token")
    email_from_address: Optional[str] = Field(default=None, description="From address for emails")
    email_mailersend_templates: Dict[str, str] = Field(default_factory=dict, description="MailerSend template IDs")
    email_mailersend_subjects: Dict[str, str] = Field(default_factory=dict, description="MailerSend subjects")

    # Frontend URL for email links
    frontend_url: str = Field(default="http://localhost:5173", description="Frontend base URL for email links")

    # Public API URL for bot-facing endpoints (MCP, A2A, REST)
    # If not set, falls back to frontend_url with port 8080
    api_public_url: Optional[str] = Field(default=None, description="Public API base URL shown to bots (e.g., https://play.aibotcasino.com)")

    # Logging settings
    log_headers: List[str] = Field(default_factory=lambda: ["client-ip"], description="Headers to log")
    log_headers_full: bool = Field(default=False, description="Whether to log all headers")
    log_headers_sensitive: bool = Field(default=False, description="Whether to fully log sensitive headers")
    log_file: Optional[str] = Field(default=None, description="Path to log file")

    # GCP settings
    gcp_project_id: Optional[str] = Field(default=None, description="Google Cloud project ID")

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env_pydantic",
        case_sensitive=False,
    )


settings = Settings()
