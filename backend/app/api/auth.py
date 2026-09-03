import hashlib
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, decode_access_token, hash_password, verify_password
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import (
    EmailCodeRequest,
    ForgotPasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    MessageOut,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenOut,
    UserCreate,
    UserOut,
    UserUpdate,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
CODE_MINUTES = 10


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Please log in")
    token = authorization.split(" ", 1)[1].strip()
    try:
        user_id = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired login session")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _set_verification_code(user: User) -> str:
    code = _new_code()
    user.verification_code_hash = _hash_code(code)
    user.verification_expires_at = datetime.utcnow() + timedelta(minutes=CODE_MINUTES)
    return code


def _set_reset_code(user: User) -> str:
    code = _new_code()
    user.reset_code_hash = _hash_code(code)
    user.reset_expires_at = datetime.utcnow() + timedelta(minutes=CODE_MINUTES)
    return code


def _send_email(to_email: str, subject: str, body: str) -> None:
    """Send a real transactional email through configured SMTP."""
    mode = os.getenv("WANDORA_EMAIL_MODE", "smtp").strip().lower()
    if mode != "smtp":
        raise RuntimeError("WANDORA_EMAIL_MODE must be 'smtp' in V8")

    host = os.getenv("WANDORA_SMTP_HOST", "").strip()
    port = int(os.getenv("WANDORA_SMTP_PORT", "587"))
    username = os.getenv("WANDORA_SMTP_USERNAME", "").strip()
    password = os.getenv("WANDORA_SMTP_PASSWORD", "")
    from_email = os.getenv("WANDORA_FROM_EMAIL", username).strip()
    from_name = os.getenv("WANDORA_FROM_NAME", "Wandora").strip() or "Wandora"

    if not host or not username or not password or not from_email:
        raise RuntimeError(
            "Email service is not configured. Set WANDORA_SMTP_HOST, "
            "WANDORA_SMTP_PORT, WANDORA_SMTP_USERNAME, WANDORA_SMTP_PASSWORD "
            "and WANDORA_FROM_EMAIL."
        )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    msg.set_content(body)

    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=20) as server:
            server.login(username, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.send_message(msg)


def _send_verification(user: User, code: str) -> None:
    body = (
        f"Your Wandora verification code is: {code}\n\n"
        f"Use this 6-digit code to verify your email address. It expires in {CODE_MINUTES} minutes.\n\n"
        "If you did not create a Wandora account, you can ignore this email.\n\n"
        "— Wandora"
    )
    _send_email(user.email, "Your Wandora verification code", body)


def _send_reset(user: User, code: str) -> None:
    body = (
        f"Your Wandora password reset code is: {code}\n\n"
        f"Use this 6-digit code to reset your Wandora password. It expires in {CODE_MINUTES} minutes.\n\n"
        "If you did not request a password reset, you can ignore this email.\n\n"
        "— Wandora"
    )
    _send_email(user.email, "Your Wandora password reset code", body)


@router.post("/register", response_model=MessageOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    username = payload.username.strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email is already registered")
    if db.query(User).filter(User.username.ilike(username)).first():
        raise HTTPException(status_code=409, detail="Username is already taken")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(payload.password),
        city=payload.city.strip() or "Bengaluru",
        email_verified=False,
    )
    code = _set_verification_code(user)
    db.add(user)
    db.commit()
    db.refresh(user)
    try:
        _send_verification(user, code)
    except Exception as exc:
        db.delete(user)
        db.commit()
        raise HTTPException(status_code=503, detail=f"Could not send verification email: {exc}")
    return MessageOut(message="Account created. Check your email for the 6-digit verification code.")


@router.post("/verify-email", response_model=TokenOut)
def verify_email(payload: EmailCodeRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")
    if user.email_verified:
        return TokenOut(access_token=create_access_token(user.id), user=user)
    if not user.verification_code_hash or not user.verification_expires_at:
        raise HTTPException(status_code=400, detail="No verification code is active. Request a new code.")
    if datetime.utcnow() > user.verification_expires_at or not secrets.compare_digest(_hash_code(payload.code), user.verification_code_hash):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    user.email_verified = True
    user.verification_code_hash = None
    user.verification_expires_at = None
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id), user=user)


@router.post("/resend-verification", response_model=MessageOut)
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")
    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email is already verified")
    code = _set_verification_code(user)
    db.commit()
    try:
        _send_verification(user, code)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Could not send verification email: {exc}")
    return MessageOut(message="A new verification code was sent.")


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.email_verified and not user.google_sub:
        raise HTTPException(status_code=403, detail="EMAIL_NOT_VERIFIED")
    return TokenOut(access_token=create_access_token(user.id), user=user)


@router.post("/forgot-password", response_model=MessageOut)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Keep the public response generic to avoid account enumeration.
        return MessageOut(message="If an account exists for this email, a reset code has been sent.")
    code = _set_reset_code(user)
    db.commit()
    try:
        _send_reset(user, code)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Could not send reset email: {exc}")
    return MessageOut(message="If an account exists for this email, a reset code has been sent.")


@router.post("/reset-password", response_model=MessageOut)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.reset_code_hash or not user.reset_expires_at:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    if datetime.utcnow() > user.reset_expires_at or not secrets.compare_digest(_hash_code(payload.code), user.reset_code_hash):
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    user.password_hash = hash_password(payload.new_password)
    user.reset_code_hash = None
    user.reset_expires_at = None
    db.commit()
    return MessageOut(message="Password reset successfully. You can now log in.")


@router.post("/google", response_model=TokenOut)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests
    except ImportError:
        raise HTTPException(status_code=500, detail="Google authentication dependency is not installed")

    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID is not configured on the server")

    try:
        info = id_token.verify_oauth2_token(payload.credential, requests.Request(), client_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Google sign-in could not be verified")

    if info.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(status_code=401, detail="Invalid Google identity")

    google_sub = info.get("sub")
    email = (info.get("email") or "").strip().lower()
    if not google_sub or not email or not info.get("email_verified", False):
        raise HTTPException(status_code=401, detail="Google account email could not be verified")

    user = db.query(User).filter(User.google_sub == google_sub).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_sub = google_sub
            user.email_verified = True
            if not user.avatar_url:
                user.avatar_url = info.get("picture", "") or ""
        else:
            base = (info.get("name") or email.split("@", 1)[0]).strip()
            base = "".join(ch for ch in base if ch.isalnum() or ch in "_- ").strip().replace(" ", "_")[:35] or "traveler"
            username = base
            n = 2
            while db.query(User).filter(User.username.ilike(username)).first():
                suffix = f"_{n}"; username = base[:40-len(suffix)] + suffix; n += 1
            user = User(
                username=username,
                email=email,
                password_hash=hash_password(secrets.token_urlsafe(32)),
                city="Bengaluru",
                avatar_url=info.get("picture", "") or "",
                google_sub=google_sub,
                email_verified=True,
            )
            db.add(user)
    db.commit(); db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id), user=user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserOut)
def update_me(payload: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    username = payload.username.strip()
    existing = db.query(User).filter(User.username.ilike(username), User.id != user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username is already taken")
    user.username = username
    user.bio = payload.bio.strip(); user.interests = payload.interests.strip()
    user.city = payload.city.strip() or "Bengaluru"; user.avatar_url = payload.avatar_url.strip()
    db.commit(); db.refresh(user)
    return user
