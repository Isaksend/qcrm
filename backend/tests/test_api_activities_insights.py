"""Активности и AI-инсайты."""

import uuid

from fastapi.testclient import TestClient


def test_activities_require_auth(client: TestClient):
    assert client.get("/api/activities").status_code == 401


def test_create_list_patch_delete_activity(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    r = client.post(
        "/api/contacts",
        json={
            "name": "Act",
            "email": f"act_{uuid.uuid4().hex[:10]}@t.test",
            "status": "Active",
        },
        headers=h,
    )
    contact_id = r.json()["id"]

    r2 = client.post(
        "/api/activities",
        json={
            "type": "call",
            "entityType": "contact",
            "entityId": contact_id,
            "description": "Звонок",
            "timestamp": "2024-01-15T10:00:00Z",
        },
        headers=h,
    )
    assert r2.status_code == 200, r2.text
    aid = r2.json()["id"]

    r3 = client.get("/api/activities", headers=h)
    assert r3.status_code == 200
    assert any(a["id"] == aid for a in r3.json())

    r4 = client.patch(f"/api/activities/{aid}", json={"description": "Обновлено"}, headers=h)
    assert r4.status_code == 200
    assert r4.json()["description"] == "Обновлено"

    r5 = client.delete(f"/api/activities/{aid}", headers=h)
    assert r5.status_code == 200


def test_deal_stage_change_creates_system_activity(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    deal = client.post(
        "/api/deals",
        json={"title": "Stage Act Deal", "stage": "Discovery", "value": 1000},
        headers=h,
    )
    assert deal.status_code == 200, deal.text
    deal_id = deal.json()["id"]

    r2 = client.patch(f"/api/deals/{deal_id}/stage", params={"stage": "Proposal"}, headers=h)
    assert r2.status_code == 200, r2.text

    acts = client.get("/api/activities", params={"entityType": "deal", "entityId": deal_id}, headers=h)
    assert acts.status_code == 200, acts.text
    types = {a["type"] for a in acts.json()}
    assert "deal_created" in types
    assert "stage_changed" in types
    assert any(a.get("isSystem") for a in acts.json())


def test_list_activities_filters_days(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    r = client.get("/api/activities", params={"days": 30, "limit": 5}, headers=h)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_insights_list_and_create_for_contact(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    r = client.post(
        "/api/contacts",
        json={
            "name": "InsightContact",
            "email": f"ins_{uuid.uuid4().hex[:10]}@t.test",
            "status": "Active",
        },
        headers=h,
    )
    contact_id = r.json()["id"]

    r0 = client.get("/api/insights", headers=h)
    assert r0.status_code == 200

    r2 = client.post(
        "/api/insights",
        json={
            "entityType": "contact",
            "entityId": contact_id,
            "category": "note",
            "title": "T",
            "content": "C",
            "confidence": 80,
            "suggestions": [],
        },
        headers=h,
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["title"] == "T"

    r3 = client.get("/api/insights", headers=h)
    assert r3.status_code == 200
    assert any(i.get("entityId") == contact_id for i in r3.json())


def test_super_admin_insight_without_entity_id(client: TestClient, super_admin_auth: dict):
    h = super_admin_auth["headers"]
    r = client.post(
        "/api/insights",
        json={
            "entityType": "global",
            "entityId": None,
            "category": "system",
            "title": "Global",
            "content": "Text",
            "confidence": 50,
            "suggestions": [],
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
