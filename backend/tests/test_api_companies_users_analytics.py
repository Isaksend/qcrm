"""Компании, пользователи, аналитика."""

import uuid

from fastapi.testclient import TestClient

from tests.conftest import add_company, add_user, login_access_token


def test_companies_require_super_admin_for_create(client: TestClient, sales_auth: dict):
    r = client.post(
        "/api/companies",
        json={
            "name": "NewCo",
            "country": "KZ",
            "website": "https://example.com",
        },
        headers=sales_auth["headers"],
    )
    assert r.status_code == 403


def test_super_admin_create_company(client: TestClient, super_admin_auth: dict):
    h = super_admin_auth["headers"]
    r = client.post(
        "/api/companies",
        json={
            "name": f"Org_{uuid.uuid4().hex[:8]}",
            "country": "KZ",
            "website": "https://example.com",
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    cid = data["id"]
    assert data.get("timezone") == "UTC"

    r2 = client.get("/api/companies", headers=h)
    assert r2.status_code == 200
    assert any(c["id"] == cid for c in r2.json())

    r3 = client.patch(
        f"/api/companies/{cid}",
        json={"name": "RenamedOrg", "timezone": "Europe/Moscow"},
        headers=h,
    )
    assert r3.status_code == 200
    assert r3.json()["name"] == "RenamedOrg"
    assert r3.json()["timezone"] == "Europe/Moscow"


def test_users_me_and_list(client: TestClient, company_admin_auth: dict):
    h = company_admin_auth["headers"]
    r = client.get("/api/users/me", headers=h)
    assert r.status_code == 200
    assert r.json()["email"] == company_admin_auth["email"]

    r2 = client.get("/api/users", headers=h)
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)


def test_admin_creates_sales_user(client: TestClient, company_admin_auth: dict):
    h = company_admin_auth["headers"]
    new_email = f"new_sales_{uuid.uuid4().hex[:10]}@t.local"
    r = client.post(
        "/api/users",
        json={
            "name": "Новый менеджер",
            "email": new_email,
            "password": "AnotherPass123!x",
            "role": "sales_representative",
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert r.json()["email"] == new_email
    uid = r.json()["id"]

    r2 = client.get(f"/api/users/{uid}", headers=h)
    assert r2.status_code == 200

    r3 = client.delete(f"/api/users/{uid}", headers=h)
    assert r3.status_code == 200


def test_analytics_requires_auth(client: TestClient):
    assert client.get("/api/v1/analytics/sales-velocity").status_code == 401


def test_analytics_sales_velocity_ok(client: TestClient, sales_auth: dict):
    r = client.get("/api/v1/analytics/sales-velocity", headers=sales_auth["headers"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert "average_days_per_stage" in body
    assert "total_deals_analyzed" in body


def test_company_admin_sets_timezone(client: TestClient, company_admin_auth: dict):
    cid = company_admin_auth["company_id"]
    h = company_admin_auth["headers"]
    r = client.patch(f"/api/companies/{cid}", json={"timezone": "Asia/Almaty"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["timezone"] == "Asia/Almaty"


def test_manager_cannot_patch_company_timezone(client: TestClient, manager_auth: dict):
    cid = manager_auth["company_id"]
    h = manager_auth["headers"]
    r = client.patch(f"/api/companies/{cid}", json={"timezone": "Asia/Almaty"}, headers=h)
    assert r.status_code == 403


def test_manager_can_patch_company_name(client: TestClient, manager_auth: dict):
    cid = manager_auth["company_id"]
    h = manager_auth["headers"]
    r = client.patch(f"/api/companies/{cid}", json={"name": "RenamedByMgr"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "RenamedByMgr"


def test_invalid_company_timezone_returns_400(client: TestClient, super_admin_auth: dict):
    h = super_admin_auth["headers"]
    r = client.post(
        "/api/companies",
        json={
            "name": f"TzBad_{uuid.uuid4().hex[:8]}",
            "country": "KZ",
            "website": "https://example.com",
            "timezone": "Not/A/Realzone",
        },
        headers=h,
    )
    assert r.status_code == 400

    r2 = client.post(
        "/api/companies",
        json={
            "name": f"TzOk_{uuid.uuid4().hex[:8]}",
            "country": "KZ",
            "website": "https://example.com",
        },
        headers=h,
    )
    assert r2.status_code == 200, r2.text
    cid = r2.json()["id"]
    r3 = client.patch(f"/api/companies/{cid}", json={"timezone": "Invalid/Zone"}, headers=h)
    assert r3.status_code == 400
