"""Компании (tenant)."""

from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import crud, models, schemas, roles


def _parse_created_at(raw) -> datetime:
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.utcnow()


def _company_to_response(c: models.Company, src: schemas.CompanyCreate | None = None) -> schemas.CompanyResponse:
    """ORM хранит только id/name/created_at; остальные поля ответа — из запроса или значения по умолчанию."""
    if src is not None:
        return schemas.CompanyResponse(
            id=c.id,
            name=c.name,
            industry=src.industry or "",
            size=src.size if src.size is not None else 1,
            country=src.country,
            website=src.website,
            created_at=src.created_at,
        )
    return schemas.CompanyResponse(
        id=c.id,
        name=c.name or "",
        industry="",
        size=1,
        country="",
        website="",
        created_at=_parse_created_at(c.created_at),
    )


class CompanyService:
    def create(self, db: Session, company: schemas.CompanyCreate) -> schemas.CompanyResponse:
        row = crud.create_company(db=db, company=company)
        return _company_to_response(row, company)

    def list_for_user(self, db: Session, user: models.User, skip: int, limit: int) -> list[schemas.CompanyResponse]:
        if roles.is_super_admin(user.role):
            rows = crud.get_companies(db, skip=skip, limit=limit)
            return [_company_to_response(c) for c in rows]
        if roles.is_company_admin(user.role) and user.company_id:
            c = crud.get_company(db, user.company_id)
            return [_company_to_response(c)] if c else []
        raise HTTPException(status_code=403, detail="Not permitted to list companies")

    def update(self, db: Session, user: models.User, company_id: str, body: schemas.CompanyUpdate) -> schemas.CompanyResponse:
        if roles.is_super_admin(user.role):
            pass
        elif roles.is_company_admin(user.role) and user.company_id == company_id:
            pass
        else:
            raise HTTPException(status_code=403, detail="Not permitted to update this company")
        c = crud.update_company(db, company_id, body)
        if not c:
            raise HTTPException(status_code=404, detail="Company not found")
        return _company_to_response(c)

    def delete(self, db: Session, company_id: str) -> dict:
        company = crud.get_company(db, company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        if db.query(models.User).filter(models.User.company_id == company_id).count() > 0:
            raise HTTPException(status_code=400, detail="Reassign or remove users before deleting this company")
        crud.delete_company(db, company_id)
        return {"status": "deleted"}


company_service = CompanyService()
