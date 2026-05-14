"""Чат API (без реальной отправки в Telegram)."""

import uuid

from fastapi.testclient import TestClient


def test_chat_history_requires_auth(client: TestClient):
    assert client.get(f"/api/chat/{uuid.uuid4()}").status_code == 401


def test_chat_history_empty(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    r = client.post(
        "/api/contacts",
        json={
            "name": "ChatC",
            "email": f"ch_{uuid.uuid4().hex[:10]}@t.test",
            "status": "Active",
        },
        headers=h,
    )
    cid = r.json()["id"]
    r2 = client.get(f"/api/chat/{cid}", headers=h)
    assert r2.status_code == 200
    assert r2.json() == []
