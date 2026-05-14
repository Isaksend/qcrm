"""Супер-админ: создание сделок с явным companyId и PATCH пользователей."""

import uuid

from fastapi.testclient import TestClient

from tests.conftest import add_company, add_user


def test_super_admin_create_deal_requires_company_id(client: TestClient, super_admin_auth: dict):
    h = super_admin_auth["headers"]
    r = client.post(
        "/api/deals",
        json={"title": "Без компании", "stage": "Discovery", "value": 0},
        headers=h,
    )
    assert r.status_code == 400
    assert "companyid" in r.json().get("detail", "").lower()


def test_super_admin_create_deal_with_company_id(client: TestClient, db_session, super_admin_auth: dict):
    h = super_admin_auth["headers"]
    cid = add_company(db_session, "CoForDeal")
    r = client.post(
        "/api/deals",
        json={
            "title": "Сделка супер-админа",
            "stage": "Proposal",
            "value": 5000,
            "companyId": cid,
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["companyId"] == cid
    assert data["createdById"] == super_admin_auth["user_id"]


def test_company_admin_cannot_patch_users(client: TestClient, company_admin_auth: dict):
    r = client.patch(
        f"/api/users/{company_admin_auth['user_id']}",
        json={"name": "Hacked"},
        headers=company_admin_auth["headers"],
    )
    assert r.status_code == 403


def test_super_admin_patch_user_company_and_role(client: TestClient, db_session, super_admin_auth: dict):
    h = super_admin_auth["headers"]
    ca = add_company(db_session, "TenantA")
    cb = add_company(db_session, "TenantB")
    email = f"mobile_{uuid.uuid4().hex[:10]}@t.local"
    uid = add_user(db_session, email=email, role="sales_representative", company_id=ca)

    r = client.patch(
        f"/api/users/{uid}",
        json={"company_id": cb, "name": "Перенесён"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["company_id"] == cb
    assert body["name"] == "Перенесён"

    r2 = client.patch(f"/api/users/{uid}", json={"role": "manager"}, headers=h)
    assert r2.status_code == 200
    assert r2.json()["role"] == "manager"


def test_super_admin_patch_user_invalid_company(client: TestClient, db_session, super_admin_auth: dict):
    h = super_admin_auth["headers"]
    email = f"u_{uuid.uuid4().hex[:10]}@t.local"
    uid = add_user(db_session, email=email, role="sales_representative", company_id=add_company(db_session, "Cx"))
    r = client.patch(
        f"/api/users/{uid}",
        json={"company_id": str(uuid.uuid4())},
        headers=h,
    )
    assert r.status_code == 400
    assert "company" in r.json().get("detail", "").lower()


def test_super_admin_patch_is_active(client: TestClient, db_session, super_admin_auth: dict):
    h = super_admin_auth["headers"]
    cid = add_company(db_session, "CActive")
    email = f"act_{uuid.uuid4().hex[:10]}@t.local"
    uid = add_user(db_session, email=email, role="sales_representative", company_id=cid)

    r = client.patch(f"/api/users/{uid}", json={"is_active": 0}, headers=h)
    assert r.status_code == 200
    assert r.json()["is_active"] == 0

    r2 = client.patch(f"/api/users/{uid}", json={"is_active": 1}, headers=h)
    assert r2.status_code == 200
    assert r2.json()["is_active"] == 1


def test_super_admin_list_companies(client: TestClient, db_session, super_admin_auth: dict):
    add_company(db_session, "ExtraListCo")
    r = client.get("/api/companies", headers=super_admin_auth["headers"])
    assert r.status_code == 200
    assert len(r.json()) >= 1
