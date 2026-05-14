"""Тесты REST API сделок и заметок."""

import uuid

from fastapi.testclient import TestClient

from tests.conftest import add_company, add_user, login_access_token


def test_deals_require_auth(client: TestClient):
    assert client.get("/api/deals").status_code == 401


def test_create_list_get_deal(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    payload = {
        "title": "Сделка тест",
        "stage": "Discovery",
        "value": 1000.0,
        "currency": "KTZ",
    }
    r = client.post("/api/deals", json=payload, headers=h)
    assert r.status_code == 200, r.text
    deal = r.json()
    assert deal["title"] == "Сделка тест"
    assert deal["userId"] == sales_auth["user_id"]
    did = deal["id"]

    r2 = client.get("/api/deals", headers=h)
    assert r2.status_code == 200
    assert any(d["id"] == did for d in r2.json())

    r3 = client.get(f"/api/deals/{did}", headers=h)
    assert r3.status_code == 200
    assert r3.json()["id"] == did


def test_update_stage_and_patch_deal(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    r = client.post(
        "/api/deals",
        json={"title": "StageDeal", "stage": "Discovery", "value": 0},
        headers=h,
    )
    did = r.json()["id"]

    r2 = client.patch(f"/api/deals/{did}/stage", params={"stage": "Proposal"}, headers=h)
    assert r2.status_code == 200, r2.text
    assert r2.json()["stage"] == "Proposal"

    r3 = client.patch(f"/api/deals/{did}", json={"notes": "Заметка"}, headers=h)
    assert r3.status_code == 200
    assert r3.json()["notes"] == "Заметка"


def test_deal_notes(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    r = client.post(
        "/api/deals",
        json={"title": "WithNotes", "stage": "Discovery", "value": 0},
        headers=h,
    )
    did = r.json()["id"]

    r0 = client.get(f"/api/deals/{did}/notes", headers=h)
    assert r0.status_code == 200
    assert r0.json() == []

    r2 = client.post(
        f"/api/deals/{did}/notes",
        json={"dealId": did, "content": "Первый комментарий"},
        headers=h,
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["content"] == "Первый комментарий"

    r3 = client.get(f"/api/deals/{did}/notes", headers=h)
    assert r3.status_code == 200
    assert len(r3.json()) == 1


def test_delete_deal(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    r = client.post(
        "/api/deals",
        json={"title": "ToDelete", "stage": "Discovery", "value": 0},
        headers=h,
    )
    did = r.json()["id"]
    r2 = client.delete(f"/api/deals/{did}", headers=h)
    assert r2.status_code == 200
    assert client.get(f"/api/deals/{did}", headers=h).status_code == 404


def test_sales_cannot_read_peer_deal(client: TestClient, db_session):
    """Сделка коллеги (другой userId в той же компании) недоступна sales_representative."""
    cid = add_company(db_session, "SharedCo")
    e1 = f"u1_{uuid.uuid4().hex[:8]}@t.local"
    e2 = f"u2_{uuid.uuid4().hex[:8]}@t.local"
    uid1 = add_user(db_session, email=e1, role="sales_representative", company_id=cid)
    add_user(db_session, email=e2, role="sales_representative", company_id=cid)

    from app import models

    did = str(uuid.uuid4())
    db_session.add(
        models.Deal(
            id=did,
            title="Peer deal",
            value=1.0,
            stage="Discovery",
            userId=uid1,
            companyId=cid,
        )
    )
    db_session.commit()

    token2 = login_access_token(client, e2)
    h2 = {"Authorization": f"Bearer {token2}"}
    r = client.get(f"/api/deals/{did}", headers=h2)
    assert r.status_code == 403
