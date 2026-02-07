"""
Authentication module for AI Bot Casino.

Handles:
- JWT token generation and validation for human bot owners
- Bot API token validation (SHA-256 hash lookup)
"""
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple

from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from settings import settings

SECRET_KEY = None
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.auth_access_token_expires * 60

security = HTTPBearer()

logger = logging.getLogger(__name__)


def load_secret_key(secret: str = None):
    """Initialize the JWT secret key."""
    global SECRET_KEY
    if secret:
        SECRET_KEY = secret
    else:
        SECRET_KEY = settings.auth_jwt_secret


def generate_token(data: Dict, expires_delta: timedelta | None = None) -> Tuple[str, datetime]:
    """Create a JWT token."""
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return (encoded_jwt, expire)


def extract_jwt_data(token: str, allow_expired: bool = False) -> Dict:
    """Decode a JWT token and return the payload."""
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set")
    try:
        options = {}
        if allow_expired:
            options["verify_exp"] = False
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options=options)
        return payload
    except JWTError as je:
        logger.debug(f"Cannot decode JWT token: {je}")
        raise HTTPException(status_code=401, detail="Invalid token")


def hash_api_token(token: str) -> str:
    """Hash an API token using SHA-256 for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def validate_bot_api_token(token: str, bots_db) -> Optional[Dict]:
    """
    Validate a bot API token by looking up its hash in the database.

    Returns the bot profile if valid, None otherwise.
    """
    token_hash = hash_api_token(token)
    from core.firestore_dict import FirestoreEqualsFilter
    try:
        for bot_id, bot in bots_db.find(filters=[FirestoreEqualsFilter("api_token_hash", token_hash)]):
            return {"bot_id": bot_id, "bot": bot}
    except Exception:
        # InMemoryDict find uses same interface
        for bot_id, bot in bots_db.find(filters=[FirestoreEqualsFilter("api_token_hash", token_hash)]):
            return {"bot_id": bot_id, "bot": bot}
    return None


# FastAPI dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """FastAPI dependency: get authenticated human user from JWT."""
    token = credentials.credentials
    payload = extract_jwt_data(token)
    user_id = payload.get("user")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: no user ID")
    return {"user_id": user_id, "payload": payload}


async def get_current_bot(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    FastAPI dependency: get authenticated bot from API token.
    Looks up the token hash in the bots database.
    """
    token = credentials.credentials
    from modules.db import get_db_handle_bots
    bots_db = get_db_handle_bots()
    result = validate_bot_api_token(token, bots_db)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return result


# Initialize secret key on module load
load_secret_key()
