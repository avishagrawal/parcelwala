from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..config import settings
from ..dependencies import get_current_user
from ..models import RefreshToken, Role, User
from ..schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from ..security import create_token, decode_token, hash_password, verify_password
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])
DEFAULT_ROLE = "CUSTOMER"

def tokens_for(user: User, db: Session) -> TokenResponse:
    access, _ = create_token(user.id, "access", timedelta(minutes=settings.access_token_expire_minutes))
    refresh, token_id = create_token(user.id, "refresh", timedelta(days=settings.refresh_token_expire_days))
    db.add(RefreshToken(user_id=user.id, token_id=token_id, expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)))
    db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)

def user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, full_name=user.full_name, is_active=user.is_active, roles=[r.name for r in user.roles])

@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == data.email.lower())):
        raise HTTPException(409, "Email is already registered")
    role = db.scalar(select(Role).where(Role.name == DEFAULT_ROLE))
    if not role:
        raise HTTPException(500, "Default role is not configured")
    user = User(email=data.email.lower(), full_name=data.full_name.strip(), password_hash=hash_password(data.password), roles=[role])
    db.add(user); db.commit(); db.refresh(user)
    return user_response(user)

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.password_hash) or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return tokens_for(user, db)

@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh": raise ValueError
    except (JWTError, ValueError):
        raise HTTPException(401, "Invalid or expired refresh token")
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_id == payload.get("jti"), RefreshToken.revoked.is_(False)))
    if not stored or stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(401, "Refresh token has been revoked or expired")
    stored.revoked = True
    user = db.get(User, payload.get("sub"))
    if not user or not user.is_active: raise HTTPException(401, "User is inactive")
    return tokens_for(user, db)

@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user_response(user)
