"""
Authentication business logic for AI Bot Casino.
Passwordless OTP flow: register → send OTP → verify → create user + bot.
"""
from datetime import datetime, timedelta, timezone
import random
import secrets
import logging
import uuid

from fastapi import HTTPException, Request

from settings import settings
from auth import generate_token, hash_api_token
from core.types import (
    generate_id, RegisterUserRequest, LoginUserRequest,
    RegisterOrLoginResponse, VerifyOTPRequest, VerifyOTPResponse,
    VerifyMagicLinkRequest, UserInfo, OTP, BotProfile, Acceptance,
    SetupBotRequest, SetupBotResponse,
)
from core.email_validate import validate_email


def register_user(req: RegisterUserRequest, fastapi_request: Request,
                  candidate_users, users, otps) -> RegisterOrLoginResponse:
    """Register a new user — creates candidate user + OTP + sends email."""

    def create_policy_history(fastapi_request: Request) -> Acceptance:
        return Acceptance(
            timestamp=datetime.now(timezone.utc),
            accepted_via=fastapi_request.headers.get("User-Agent"),
            ip_address=fastapi_request.client.host,
            user_agent=fastapi_request.headers.get("User-Agent"),
            comment="User self-registered"
        )

    status, proper_email, msg = validate_email(req.email)
    if not status:
        raise HTTPException(status_code=422, detail=f"Invalid email: {msg}")

    # Check if user already exists
    from core.firestore_dict import FirestoreEqualsFilter
    for x in users.find(filters=[FirestoreEqualsFilter("email", proper_email)]):
        raise HTTPException(status_code=400, detail="User already exists")

    req.email = proper_email

    # Generate OTP
    if proper_email == "test@test.com":
        otp_code = "123456"
    elif settings.test_users_enabled and proper_email in settings.test_users_emails:
        otp_code = settings.test_users_otp
    else:
        otp_code = str(random.randint(100000, 999999))

    exp_delta = timedelta(minutes=settings.auth_otp_expires)
    otp_expires_at = datetime.now(timezone.utc) + exp_delta
    user_id = generate_id()

    policies = {}
    for policy, accepted in req.accepted_policies.items():
        if accepted:
            policies[policy] = create_policy_history(fastapi_request)

    candidate_users[user_id] = UserInfo(
        **(req.model_dump(exclude={"recaptcha_token", "callback_url", "accepted_policies"}) |
           {"id": user_id, "policies": policies})
    )

    otp_id = generate_id()
    magic_token = secrets.token_urlsafe(32)
    otp = OTP(
        otp_id=otp_id,
        otp_expires_at=otp_expires_at,
        user_id=user_id,
        otp=otp_code,
        registration=True,
        magic_token=magic_token,
        magic_token_used=False,
    )
    otps[otp_id] = otp

    # Send OTP email
    name = req.first_name or "Bot Owner"
    frontend_url = req.callback_url or settings.frontend_url
    magic_link = f"{frontend_url}/auth/verify?otp_id={otp_id}&magic_token={magic_token}"

    try:
        from modules.email_service import send_email, EmailType, EmailRecipient
        send_email(
            recipient_list=[EmailRecipient(email=proper_email, name=name)],
            email_type=EmailType.SEND_OTP_REGISTRATION,
            attributes={
                "otp_code": otp_code,
                "otp_expires_in": settings.auth_otp_expires,
                "name": name,
                "email": req.email,
                "magic_link": magic_link,
            }
        )
    except Exception as e:
        logging.error(f"Failed to send OTP registration email to {proper_email}: {str(e)}")
        del otps[otp_id]
        del candidate_users[user_id]
        raise HTTPException(
            status_code=500,
            detail="Failed to send verification email. Please try again."
        )

    logging.info(f"Registration OTP sent: user_id={user_id}, email={proper_email}")
    return RegisterOrLoginResponse(otp_id=otp_id, otp_expires_at=otp.otp_expires_at)


def login_user(req: LoginUserRequest, users, otps) -> RegisterOrLoginResponse:
    """Login an existing user — sends OTP to their email."""

    user_email = req.email.strip().lower()

    if user_email == "test@test.com":
        otp_code = "123456"
    elif settings.test_users_enabled and user_email in settings.test_users_emails:
        otp_code = settings.test_users_otp
    else:
        otp_code = str(random.randint(100000, 999999))

    otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.auth_otp_expires)

    # Anti-enumeration: return fake response even if user doesn't exist
    from core.firestore_dict import FirestoreEqualsFilter
    try:
        user_id, user = next(users.find(filters=[FirestoreEqualsFilter("email", user_email)]))
    except StopIteration:
        logging.debug(f"User {user_email} does not exist — returning fake response for anti-enumeration")
        return RegisterOrLoginResponse(otp_id=generate_id(), otp_expires_at=otp_expires_at)

    otp_id = generate_id()
    magic_token = secrets.token_urlsafe(32)
    otp = OTP(
        otp_id=otp_id,
        otp_expires_at=otp_expires_at,
        user_id=user_id,
        otp=otp_code,
        magic_token=magic_token,
        magic_token_used=False,
    )
    otps[otp_id] = otp

    name = user.first_name or "Bot Owner"
    frontend_url = req.callback_url or settings.frontend_url
    magic_link = f"{frontend_url}/auth/verify?otp_id={otp_id}&magic_token={magic_token}"

    try:
        from modules.email_service import send_email, EmailType, EmailRecipient
        send_email(
            recipient_list=[EmailRecipient(email=user_email, name=name)],
            email_type=EmailType.SEND_OTP_LOGIN,
            attributes={
                "otp_code": otp_code,
                "otp_expires_in": settings.auth_otp_expires,
                "name": name,
                "email": user_email,
                "magic_link": magic_link,
            }
        )
    except Exception as e:
        logging.error(f"Failed to send OTP login email to {user_email}: {str(e)}")
        del otps[otp_id]
        raise HTTPException(
            status_code=500,
            detail="Failed to send verification email. Please try again."
        )

    logging.info(f"Login OTP sent: user_id={user_id}, email={user_email}")
    return RegisterOrLoginResponse(otp_id=otp_id, otp_expires_at=otp_expires_at)


def verify_otp(req: VerifyOTPRequest, candidate_users, users, otps) -> VerifyOTPResponse:
    """Verify the OTP code. On registration, moves candidate→user."""
    try:
        otp = otps[req.otp_id]
    except KeyError:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    try:
        if otp.registration:
            user = candidate_users[otp.user_id]
        else:
            user = users[otp.user_id]
    except KeyError:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    if otp.otp_expires_at < datetime.now(timezone.utc):
        del otps[req.otp_id]
        raise HTTPException(status_code=401, detail="OTP expired")

    if otp.otp != req.otp:
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    is_new_user = False
    api_token = None

    if otp.registration:
        # Check user doesn't already exist
        existing = users.get(otp.user_id)
        if existing is not None:
            raise HTTPException(status_code=422, detail="User already registered")

        # Move candidate to users
        users[otp.user_id] = user
        del candidate_users[otp.user_id]
        is_new_user = True

        logging.info(f"New user registered: {otp.user_id} ({user.email})")

    del otps[req.otp_id]

    # Generate JWT
    token_payload = {"user": otp.user_id}
    access_token, expires_at = generate_token(
        data=token_payload,
        expires_delta=timedelta(hours=settings.auth_access_token_expires)
    )

    return VerifyOTPResponse(
        access_token=access_token,
        expires_at=expires_at,
        is_new_user=is_new_user,
    )


def verify_magic_link(req: VerifyMagicLinkRequest, candidate_users, users, otps) -> VerifyOTPResponse:
    """Verify the magic link token — no reCAPTCHA required."""
    try:
        otp = otps[req.otp_id]
    except KeyError:
        raise HTTPException(status_code=401, detail="Invalid or expired magic link")

    try:
        if otp.registration:
            user = candidate_users[otp.user_id]
        else:
            user = users[otp.user_id]
    except KeyError:
        raise HTTPException(status_code=401, detail="Invalid or expired magic link")

    if otp.otp_expires_at < datetime.now(timezone.utc):
        del otps[req.otp_id]
        raise HTTPException(status_code=401, detail="Magic link has expired")

    if not otp.magic_token:
        raise HTTPException(status_code=401, detail="Invalid magic link")

    if otp.magic_token_used:
        raise HTTPException(status_code=401, detail="Magic link has already been used")

    if otp.magic_token != req.magic_token:
        raise HTTPException(status_code=401, detail="Invalid magic link")

    # Mark token as used
    otp.magic_token_used = True
    otps[req.otp_id] = otp

    is_new_user = False

    if otp.registration:
        existing = users.get(otp.user_id)
        if existing is not None:
            raise HTTPException(status_code=422, detail="User already registered")

        users[otp.user_id] = user
        del candidate_users[otp.user_id]
        is_new_user = True

        logging.info(f"New user registered via magic link: {otp.user_id} ({user.email})")

    del otps[req.otp_id]

    token_payload = {"user": otp.user_id}
    access_token, expires_at = generate_token(
        data=token_payload,
        expires_delta=timedelta(hours=settings.auth_access_token_expires)
    )

    return VerifyOTPResponse(
        access_token=access_token,
        expires_at=expires_at,
        is_new_user=is_new_user,
    )


def setup_bot(user_id: str, req: SetupBotRequest, users, bots) -> SetupBotResponse:
    """Create a bot profile for the user. Called after registration (step 2)."""
    user = users.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.bot_id:
        raise HTTPException(status_code=400, detail="User already has a bot")

    # Generate API token
    raw_token = f"abc_sk_{secrets.token_hex(20)}"
    token_hash = hash_api_token(raw_token)

    bot_id = generate_id()
    bot = BotProfile(
        bot_id=bot_id,
        owner_id=user_id,
        name=req.bot_name,
        avatar_seed=req.avatar_seed,
        api_token_hash=token_hash,
        balance=settings.bot_starting_balance,
    )
    bots[bot_id] = bot

    # Link bot to user
    user_data = user.model_dump()
    user_data["bot_id"] = bot_id
    users[user_id] = UserInfo(**user_data)

    logging.info(f"Bot created: {bot_id} ({req.bot_name}) for user {user_id}")

    return SetupBotResponse(
        bot_id=bot_id,
        api_token=raw_token,
        mcp_url=f"{settings.frontend_url.replace('5173', '8080')}/mcp",
    )


def get_user_info(user_id: str, users) -> UserInfo:
    """Get user info by ID."""
    user = users.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
