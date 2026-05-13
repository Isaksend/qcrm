from fastapi.testclient import TestClient


def test_contacts_search_requires_auth():
    from app.main import app

    with TestClient(app) as client:
        r = client.get("/api/contacts/search?phone=123")
        assert r.status_code == 401


def test_register_and_login(client: TestClient):
    r = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "testuser@example.com",
            "password": "secretpass",
            "role": "user",
            "company_id": None,
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["email"] == "testuser@example.com"

    r2 = client.post(
        "/api/auth/login",
        data={"username": "testuser@example.com", "password": "secretpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert "access_token" in body
