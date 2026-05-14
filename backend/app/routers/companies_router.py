from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db
from app.services.company_service import company_service

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.post("", response_model=schemas.CompanyResponse)
def create_company(
    company: schemas.CompanyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_super_admin),
):
    return company_service.create(db, company)


@router.get("", response_model=List[schemas.CompanyResponse])
def get_companies_list(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return company_service.list_for_user(db, current_user, skip, limit)


@router.patch("/{company_id}", response_model=schemas.CompanyResponse)
def patch_company(
    company_id: str,
    body: schemas.CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return company_service.update(db, current_user, company_id, body)


@router.delete("/{company_id}")
def remove_company(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_super_admin),
):
    return company_service.delete(db, company_id)
