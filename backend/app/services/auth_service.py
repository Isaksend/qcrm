"""Регистрация и выдача токена."""

from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app import crud, schemas, auth, models


class AuthService:
    def register(self, db: Session, user: schemas.UserCreate) -> models.User:
        db_user = crud.get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        safe = user.model_copy(update={"role": "sales_representative"})
        return crud.create_user(db=db, user=safe)

    def login(self, db: Session, form_data: OAuth2PasswordRequestForm) -> dict:
        user = crud.get_user_by_email(db, email=form_data.username)
        if not user or not auth.verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        access_token_expires = auth.access_token_expires_delta()
        access_token = auth.create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires,
        )
        return {"access_token": access_token, "token_type": "bearer"}


auth_service = AuthService()
