from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db
from app.services.user_service import user_service

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user


@router.get("", response_model=List[schemas.UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Список коллег компании."""
    return user_service.list_colleagues(db, current_user, skip, limit)


@router.post("", response_model=schemas.UserResponse)
def create_new_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_admin_or_manager),
):
    return user_service.create_managed_user(db, current_user, user)


@router.patch("/{user_id}", response_model=schemas.UserResponse)
def patch_user_as_super_admin(
    user_id: str,
    body: schemas.UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_super_admin),
):
    """Смена компании, роли, имени, активности — только для super_admin."""
    return user_service.update_as_super_admin(db, current_user, user_id, body)


@router.get("/{user_id}", response_model=schemas.UserResponse)
def read_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Карточка пользователя по id (та же компания или super_admin)."""
    return user_service.get_by_id_for_viewer(db, current_user, user_id)


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_admin),
):
    return user_service.delete_user(db, current_user, user_id)
