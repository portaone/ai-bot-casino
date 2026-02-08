from fastapi import APIRouter, Depends, Request, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from request_trace import RouteWithLogging
from modules.auth import (
    register_user, login_user, verify_otp, verify_magic_link,
    get_user_info, setup_bot, regenerate_bot_token,
)
from modules.db import (
    get_db_handle_users, get_db_handle_candidate_users, get_db_handle_otps,
    get_db_handle_bots,
)
from core.types import (
    RegisterUserRequest, LoginUserRequest, RegisterOrLoginResponse,
    VerifyOTPRequest, VerifyMagicLinkRequest, VerifyOTPResponse,
    UserInfo, SetupBotRequest, SetupBotResponse,
)
from settings import settings
from auth import extract_jwt_data
import httpx
import logging
import os

security = HTTPBearer()

router = APIRouter(
    route_class=RouteWithLogging,
    prefix="/api/v1/auth",
    tags=["auth"],
)


async def verify_recaptcha(recaptcha_token: str, remote_ip: str = None) -> bool:
    """Verify the reCAPTCHA token."""
    if settings.recaptcha_skip:
        return True
    if not settings.recaptcha_secret_key:
        logging.warning("reCAPTCHA secret key not configured, skipping verification")
        return True
    try:
        url = "https://www.google.com/recaptcha/api/siteverify"
        data = {
            "secret": settings.recaptcha_secret_key,
            "response": recaptcha_token,
            "remoteip": remote_ip,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            result = response.json()

            if settings.recaptcha_debug:
                logging.debug(f"reCAPTCHA response: {result}")

            if not result.get("success"):
                raise HTTPException(status_code=403, detail="reCAPTCHA verification failed")

            return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"reCAPTCHA verification error: {str(e)}")
        raise HTTPException(status_code=403, detail="reCAPTCHA verification failed")


@router.post("/register", response_model=RegisterOrLoginResponse)
async def register_user_endpoint(
    request: Request,
    req: RegisterUserRequest,
    db_candidate_users=Depends(get_db_handle_candidate_users),
    db_users=Depends(get_db_handle_users),
    db_otps=Depends(get_db_handle_otps),
) -> RegisterOrLoginResponse:
    """Register a new bot owner account."""
    if req.recaptcha_token:
        await verify_recaptcha(req.recaptcha_token, request.client.host)

    return register_user(
        req=req,
        fastapi_request=request,
        candidate_users=db_candidate_users,
        users=db_users,
        otps=db_otps,
    )


@router.post("/login", response_model=RegisterOrLoginResponse)
async def login_user_endpoint(
    request: Request,
    req: LoginUserRequest,
    db_users=Depends(get_db_handle_users),
    db_otps=Depends(get_db_handle_otps),
) -> RegisterOrLoginResponse:
    """Login — sends OTP to email."""
    if req.recaptcha_token:
        await verify_recaptcha(req.recaptcha_token, request.client.host)

    return login_user(req, users=db_users, otps=db_otps)


@router.post("/verify-otp", response_model=VerifyOTPResponse)
async def verify_otp_endpoint(
    request: Request,
    req: VerifyOTPRequest,
    db_users=Depends(get_db_handle_users),
    db_candidate_users=Depends(get_db_handle_candidate_users),
    db_otps=Depends(get_db_handle_otps),
) -> VerifyOTPResponse:
    """Verify OTP code from email."""
    if req.recaptcha_token:
        await verify_recaptcha(req.recaptcha_token, request.client.host)

    return verify_otp(req, candidate_users=db_candidate_users, users=db_users, otps=db_otps)


@router.post("/verify-magic-link", response_model=VerifyOTPResponse)
async def verify_magic_link_endpoint(
    req: VerifyMagicLinkRequest,
    db_users=Depends(get_db_handle_users),
    db_candidate_users=Depends(get_db_handle_candidate_users),
    db_otps=Depends(get_db_handle_otps),
) -> VerifyOTPResponse:
    """Verify magic link token — no reCAPTCHA required."""
    return verify_magic_link(req, candidate_users=db_candidate_users, users=db_users, otps=db_otps)


@router.post("/setup-bot", response_model=SetupBotResponse)
async def setup_bot_endpoint(
    req: SetupBotRequest,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db_users=Depends(get_db_handle_users),
    db_bots=Depends(get_db_handle_bots),
) -> SetupBotResponse:
    """Create bot profile (registration step 2). Requires JWT from verify-otp."""
    token_data = extract_jwt_data(credentials.credentials)
    user_id = token_data.get("user")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return setup_bot(user_id=user_id, req=req, users=db_users, bots=db_bots)


@router.post("/regenerate-token", response_model=SetupBotResponse)
async def regenerate_token_endpoint(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db_users=Depends(get_db_handle_users),
    db_bots=Depends(get_db_handle_bots),
) -> SetupBotResponse:
    """Regenerate API token for the user's bot. Invalidates the old token."""
    token_data = extract_jwt_data(credentials.credentials)
    user_id = token_data.get("user")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return regenerate_bot_token(user_id=user_id, users=db_users, bots=db_bots)


@router.get("/me", response_model=UserInfo)
async def get_me_endpoint(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db_users=Depends(get_db_handle_users),
) -> UserInfo:
    """Get current user's info."""
    token_data = extract_jwt_data(credentials.credentials)
    user_id = token_data.get("user")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return get_user_info(user_id=user_id, users=db_users)


def initialize():
    """Initialize the auth module."""
    pass
