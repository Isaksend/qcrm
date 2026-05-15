from datetime import datetime, timedelta, timezone
import uuid
from typing import Optional
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import database, models
from .config import get_secret_key, get_settings

ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=15)
    to_encode.update({"exp": expire, "iat": now, "jti": str(uuid.uuid4()), "typ": TOKEN_TYPE_ACCESS})
    return jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=30)
    to_encode.update({"exp": expire, "iat": now, "jti": str(uuid.uuid4()), "typ": TOKEN_TYPE_REFRESH})
    return jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)


def decode_token(token: str, *, expected_type: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise credentials_exception from None
    if payload.get("typ") != expected_type:
        raise credentials_exception
    if not payload.get("sub"):
        raise credentials_exception
    return payload


def create_token_pair(email: str) -> dict:
    access_token = create_access_token(
        data={"sub": email},
        expires_delta=access_token_expires_delta(),
    )
    refresh_token = create_refresh_token(
        data={"sub": email},
        expires_delta=refresh_token_expires_delta(),
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token, expected_type=TOKEN_TYPE_ACCESS)
        email: str = payload.get("sub")
    except HTTPException:
        raise credentials_exception from None
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_admin(current_user: models.User = Depends(get_current_active_user)):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user


def get_current_admin_or_manager(current_user: models.User = Depends(get_current_active_user)):
    if current_user.role not in ("admin", "super_admin", "manager"):
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

def get_current_super_admin(current_user: models.User = Depends(get_current_active_user)):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Requires super admin privileges")
    return current_user


def access_token_expires_delta() -> timedelta:
    return timedelta(minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES)


def refresh_token_expires_delta() -> timedelta:
    return timedelta(days=get_settings().REFRESH_TOKEN_EXPIRE_DAYS)
