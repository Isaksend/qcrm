from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import auth, schemas
from app.database import get_db
from app.services.auth_service import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return auth_service.register(db, user)


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return auth_service.login(db, form_data)


@router.post("/refresh", response_model=schemas.Token)
def refresh_tokens(body: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    return auth_service.refresh(db, body)
