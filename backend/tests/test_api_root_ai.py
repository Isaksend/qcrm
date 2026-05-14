"""Корень приложения и защита AI-эндпоинтов."""

from fastapi.testclient import TestClient


def test_root(client: TestClient):
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()


def test_ai_score_lead_requires_auth(client: TestClient):
    r = client.post(
        "/api/v1/ai/score-lead",
        json={
            "activity_count_30d": 1,
            "days_since_last_contact": 2,
            "total_deal_value": 100.0,
            "interaction_score": 0.5,
        },
    )
    assert r.status_code == 401
