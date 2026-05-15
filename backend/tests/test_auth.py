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
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_refresh_token_rotation(client: TestClient):
    client.post(
        "/api/auth/register",
        json={
            "name": "Refresh User",
            "email": "refresh@example.com",
            "password": "secretpass",
            "role": "user",
            "company_id": None,
        },
    )
    login = client.post(
        "/api/auth/login",
        data={"username": "refresh@example.com", "password": "secretpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200, login.text
    tokens = login.json()
    old_refresh = tokens["refresh_token"]

    r = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 200, r.text
    new_tokens = r.json()
    assert new_tokens["refresh_token"] != old_refresh
    assert new_tokens["access_token"]

    me = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "refresh@example.com"

    bad = client.post("/api/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert bad.status_code == 401
