"""Pytest fixtures: isolated SQLite DB + dependency override."""

import os
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Force SQLite for tests so CI/local do not require PostgreSQL.
_test_db_path = Path(__file__).resolve().parents[1] / "pytest_tinycrm.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-characters-long")
os.environ.setdefault("APP_ENV", "development")
# Изоляция тестов от внешних сервисов (иначе lifespan поднимает polling / Sentry).
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["SENTRY_DSN"] = ""

DEFAULT_TEST_PASSWORD = "TestPass123!zz"


def login_access_token(client: TestClient, email: str, password: str = DEFAULT_TEST_PASSWORD) -> str:
    r = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def add_company(db_session: Session, name: str | None = None) -> str:
    from app import models

    cid = str(uuid.uuid4())
    db_session.add(
        models.Company(
            id=cid,
            name=name or f"Co_{cid[:8]}",
            created_at="2024-01-01T00:00:00",
        )
    )
    db_session.commit()
    return cid


def add_user(
    db_session: Session,
    *,
    email: str,
    role: str,
    company_id: str | None,
    password: str = DEFAULT_TEST_PASSWORD,
) -> str:
    from app import auth, models

    uid = str(uuid.uuid4())
    db_session.add(
        models.User(
            id=uid,
            name="Tester",
            email=email,
            hashed_password=auth.get_password_hash(password),
            role=role,
            company_id=company_id,
            is_active=1,
        )
    )
    db_session.commit()
    return uid


@pytest.fixture(scope="function")
def db_session():
    from app.models import Base

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    from app.main import app
    from app.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sales_auth(client: TestClient, db_session: Session) -> dict[str, Any]:
    cid = add_company(db_session)
    email = f"sales_{uuid.uuid4().hex[:12]}@test.local"
    uid = add_user(db_session, email=email, role="sales_representative", company_id=cid)
    token = login_access_token(client, email)
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "company_id": cid,
        "user_id": uid,
        "email": email,
    }


@pytest.fixture
def super_admin_auth(client: TestClient, db_session: Session) -> dict[str, Any]:
    email = f"sa_{uuid.uuid4().hex[:12]}@test.local"
    uid = add_user(db_session, email=email, role="super_admin", company_id=None)
    token = login_access_token(client, email)
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "company_id": None,
        "user_id": uid,
        "email": email,
    }


@pytest.fixture
def company_admin_auth(client: TestClient, db_session: Session) -> dict[str, Any]:
    cid = add_company(db_session)
    email = f"admin_{uuid.uuid4().hex[:12]}@test.local"
    uid = add_user(db_session, email=email, role="admin", company_id=cid)
    token = login_access_token(client, email)
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "company_id": cid,
        "user_id": uid,
        "email": email,
    }
