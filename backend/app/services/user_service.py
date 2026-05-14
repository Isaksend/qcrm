"""Пользователи и RBAC для управления учётками."""

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import crud, models, schemas, roles


class UserService:
    def get_by_id_for_viewer(self, db: Session, current_user: models.User, user_id: str) -> models.User:
        target = crud.get_user(db, user_id)
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        if roles.is_super_admin(current_user.role):
            return target
        if current_user.id == target.id:
            return target
        if not current_user.company_id or target.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not permitted to view this user")
        return target

    def list_colleagues(self, db: Session, current_user: models.User, skip: int, limit: int):
        if roles.is_super_admin(current_user.role):
            comp_id = None
        elif current_user.company_id:
            comp_id = current_user.company_id
        else:
            return []
        return crud.get_users(db, skip=skip, limit=limit, company_id=comp_id)

    def create_managed_user(self, db: Session, current_user: models.User, user: schemas.UserCreate) -> models.User:
        if user.role == "user":
            user = user.model_copy(update={"role": "sales_representative"})

        if current_user.role == "manager":
            if user.role != "sales_representative":
                raise HTTPException(status_code=403, detail="Managers may only create sales representative accounts")
            user = user.model_copy(update={"company_id": current_user.company_id})
            return crud.create_user(db=db, user=user)

        if current_user.role == "super_admin":
            allowed_roles = ("super_admin", "admin", "manager", "sales_representative")
            if user.role not in allowed_roles:
                raise HTTPException(status_code=400, detail=f"role must be one of {allowed_roles}")
            return crud.create_user(db=db, user=user)

        if user.role == "super_admin":
            raise HTTPException(status_code=403, detail="Cannot create super admin")
        if user.role == "admin":
            raise HTTPException(status_code=403, detail="Only super administrators can create company administrators")
        if user.role not in ("manager", "sales_representative"):
            raise HTTPException(status_code=403, detail="Invalid role for company administrator")
        user = user.model_copy(update={"company_id": current_user.company_id})
        return crud.create_user(db=db, user=user)

    def delete_user(self, db: Session, current_user: models.User, user_id: str) -> dict:
        target_user = crud.get_user(db, user_id=user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        if current_user.role != "super_admin" and target_user.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Not permitted to delete users outside your company")
        crud.delete_user(db, user_id=user_id)
        return {"status": "deleted"}

    def update_as_super_admin(
        self,
        db: Session,
        current_user: models.User,
        user_id: str,
        body: schemas.UserAdminUpdate,
    ) -> models.User:
        if not roles.is_super_admin(current_user.role):
            raise HTTPException(status_code=403, detail="Requires super admin privileges")
        if current_user.id == user_id and body.role is not None and body.role != "super_admin":
            raise HTTPException(status_code=400, detail="Cannot change your own role away from super_admin")
        target = crud.get_user(db, user_id)
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        payload = body.model_dump(exclude_unset=True)
        if "role" in payload and payload["role"] is not None:
            allowed = ("super_admin", "admin", "manager", "sales_representative", "user")
            if payload["role"] not in allowed:
                raise HTTPException(status_code=400, detail=f"role must be one of {allowed}")
        if "company_id" in payload:
            cid = payload["company_id"]
            if cid is not None and not crud.get_company(db, cid):
                raise HTTPException(status_code=400, detail="company_id does not reference an existing company")
        updated = crud.update_user_admin(db, user_id, body)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        return updated


user_service = UserService()
