from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, UserRead, UserUpdate,
)
from ..auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, get_current_user,
)
from ..config import settings
from ..services.email import send_welcome_email, send_verification_email, send_password_reset, is_email_available
from jose import jwt as jose_jwt

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _create_verification_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    return jose_jwt.encode(
        {"sub": user_id, "exp": expire, "type": "verify_email"},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def _create_password_reset_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    return jose_jwt.encode(
        {"sub": user_id, "exp": expire, "type": "password_reset"},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


@router.post("/register", response_model=UserRead, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=body.email.lower().strip(),
        hashed_password=hash_password(body.password),
        full_name=body.full_name.strip(),
        role="user",
        is_verified=True if settings.DEBUG else False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Send welcome email with verification link
    token = _create_verification_token(user.id)
    send_welcome_email(user.email, user.full_name, token)

    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserRead)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserRead)
def update_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.full_name is not None:
        user.full_name = body.full_name.strip()
    if body.email is not None:
        new_email = body.email.lower().strip()
        if new_email != user.email:
            existing = db.query(User).filter(
                User.email == new_email,
                User.id != user.id,
            ).first()
            if existing:
                raise HTTPException(status_code=409, detail="Email already in use")
            user.email = new_email
            user.is_verified = False
            # Send verification for new email
            token = _create_verification_token(user.id)
            send_verification_email(user.email, user.full_name, token)
    db.commit()
    db.refresh(user)
    return user


@router.post("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    if payload.get("type") != "verify_email":
        raise HTTPException(status_code=400, detail="Invalid token type")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    db.commit()
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
def resend_verification(user: User = Depends(get_current_user)):
    if user.is_verified:
        return {"message": "Email already verified"}

    token = _create_verification_token(user.id)
    sent = send_verification_email(user.email, user.full_name, token)
    if not sent:
        raise HTTPException(status_code=503, detail="Email service unavailable")
    return {"message": "Verification email sent"}


@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    # Always return success to prevent email enumeration
    if user:
        token = _create_password_reset_token(user.id)
        send_password_reset(user.email, user.full_name, token)
    return {"message": "If that email exists, a reset link has been sent"}


@router.post("/reset-password")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    try:
        payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    if payload.get("type") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid token type")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user.hashed_password = hash_password(new_password)
    db.commit()
    return {"message": "Password reset successfully"}


@router.get("/email-status")
def email_status():
    return {"email_available": is_email_available()}
