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


def test_manager_sees_only_assigned_deals(client: TestClient, db_session, manager_auth: dict):
    from app import models

    cid = manager_auth["company_id"]
    mgr = manager_auth["user_id"]
    peer = add_user(
        db_session,
        email=f"s_{uuid.uuid4().hex[:10]}@t.local",
        role="sales_representative",
        company_id=cid,
    )
    d_peer = str(uuid.uuid4())
    d_mgr = str(uuid.uuid4())
    db_session.add_all(
        [
            models.Deal(
                id=d_peer,
                title="Peer",
                value=1.0,
                stage="Discovery",
                userId=peer,
                companyId=cid,
            ),
            models.Deal(
                id=d_mgr,
                title="Mine",
                value=2.0,
                stage="Discovery",
                userId=mgr,
                companyId=cid,
            ),
        ]
    )
    db_session.commit()

    r = client.get("/api/deals", headers=manager_auth["headers"])
    assert r.status_code == 200
    ids = {x["id"] for x in r.json()}
    assert d_mgr in ids and d_peer not in ids


def test_admin_can_reassign_deal_owner(client: TestClient, db_session, company_admin_auth: dict):
    cid = company_admin_auth["company_id"]
    admin_h = company_admin_auth["headers"]
    sales_a = add_user(
        db_session,
        email=f"a_{uuid.uuid4().hex[:8]}@t.local",
        role="sales_representative",
        company_id=cid,
    )
    sales_b = add_user(
        db_session,
        email=f"b_{uuid.uuid4().hex[:8]}@t.local",
        role="sales_representative",
        company_id=cid,
    )
    r = client.post(
        "/api/deals",
        json={
            "title": "Handoff",
            "stage": "Discovery",
            "value": 10,
            "currency": "KTZ",
            "userId": sales_a,
        },
        headers=admin_h,
    )
    assert r.status_code == 200, r.text
    did = r.json()["id"]
    assert r.json()["userId"] == sales_a

    r2 = client.patch(f"/api/deals/{did}", json={"userId": sales_b}, headers=admin_h)
    assert r2.status_code == 200, r2.text
    assert r2.json()["userId"] == sales_b


def test_manager_cannot_reassign_deal_owner(client: TestClient, db_session, manager_auth: dict):
    cid = manager_auth["company_id"]
    mgr = manager_auth["user_id"]
    peer = add_user(
        db_session,
        email=f"p_{uuid.uuid4().hex[:8]}@t.local",
        role="sales_representative",
        company_id=cid,
    )
    from app import models

    did = str(uuid.uuid4())
    db_session.add(
        models.Deal(
            id=did,
            title="Mgr deal",
            value=1.0,
            stage="Discovery",
            userId=mgr,
            companyId=cid,
        )
    )
    db_session.commit()

    r = client.patch(
        f"/api/deals/{did}",
        json={"userId": peer},
        headers=manager_auth["headers"],
    )
    assert r.status_code == 403


def test_deal_change_history_create_and_patch(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    r = client.post(
        "/api/deals",
        json={"title": "Hist", "stage": "Discovery", "value": 100.0, "currency": "KTZ"},
        headers=h,
    )
    assert r.status_code == 200
    did = r.json()["id"]

    h0 = client.get(f"/api/deals/{did}/history", headers=h)
    assert h0.status_code == 200
    rows0 = h0.json()
    assert len(rows0) >= 1
    assert rows0[0]["field"] == "deal_created"

    r2 = client.patch(f"/api/deals/{did}", json={"title": "Hist Renamed"}, headers=h)
    assert r2.status_code == 200

    h1 = client.get(f"/api/deals/{did}/history", headers=h)
    assert h1.status_code == 200
    rows = h1.json()
    titles = [x for x in rows if x["field"] == "title"]
    assert titles
    assert titles[0]["old_value"] == "Hist"
    assert titles[0]["new_value"] == "Hist Renamed"


def test_deal_tasks_crud(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    r = client.post(
        "/api/deals",
        json={"title": "TTasks", "stage": "Discovery", "value": 0, "currency": "KTZ"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    did = r.json()["id"]

    assert client.get(f"/api/deals/{did}/tasks", headers=h).json() == []

    r2 = client.post(f"/api/deals/{did}/tasks", json={"title": "  Call client  "}, headers=h)
    assert r2.status_code == 200, r2.text
    j = r2.json()
    assert j["title"] == "Call client"
    assert j["isDone"] == 0
    assert j.get("assignedUserId") == sales_auth["user_id"]
    tid = j["id"]

    r3 = client.get(f"/api/deals/{did}/tasks", headers=h)
    assert r3.status_code == 200
    assert len(r3.json()) == 1

    r4 = client.patch(f"/api/deals/{did}/tasks/{tid}", json={"isDone": 1}, headers=h)
    assert r4.status_code == 200
    assert r4.json()["isDone"] == 1

    r5 = client.delete(f"/api/deals/{did}/tasks/{tid}", headers=h)
    assert r5.status_code == 200
    assert client.get(f"/api/deals/{did}/tasks", headers=h).json() == []


def test_deal_tasks_patch_wrong_deal(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    d1 = client.post(
        "/api/deals",
        json={"title": "D1", "stage": "Discovery", "value": 0, "currency": "KTZ"},
        headers=h,
    ).json()["id"]
    d2 = client.post(
        "/api/deals",
        json={"title": "D2", "stage": "Discovery", "value": 0, "currency": "KTZ"},
        headers=h,
    ).json()["id"]
    tid = client.post(f"/api/deals/{d1}/tasks", json={"title": "Only on D1"}, headers=h).json()["id"]
    r = client.patch(f"/api/deals/{d2}/tasks/{tid}", json={"isDone": 1}, headers=h)
    assert r.status_code == 404


def test_sales_cannot_access_peer_deal_tasks(client: TestClient, db_session):
    cid = add_company(db_session, "CoTasks")
    e1 = f"t1_{uuid.uuid4().hex[:8]}@t.local"
    e2 = f"t2_{uuid.uuid4().hex[:8]}@t.local"
    uid1 = add_user(db_session, email=e1, role="sales_representative", company_id=cid)
    add_user(db_session, email=e2, role="sales_representative", company_id=cid)

    from app import models

    did = str(uuid.uuid4())
    db_session.add(
        models.Deal(
            id=did,
            title="Peer tasks",
            value=1.0,
            stage="Discovery",
            userId=uid1,
            companyId=cid,
        )
    )
    db_session.commit()

    token2 = login_access_token(client, e2)
    h2 = {"Authorization": f"Bearer {token2}"}
    assert client.get(f"/api/deals/{did}/tasks", headers=h2).status_code == 403
    assert (
        client.post(f"/api/deals/{did}/tasks", json={"title": "X"}, headers=h2).status_code == 403
    )


def test_me_deal_tasks_open_assigned(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    uid = sales_auth["user_id"]
    did = client.post(
        "/api/deals",
        json={"title": "MineMe", "stage": "Discovery", "value": 0, "currency": "KTZ"},
        headers=h,
    ).json()["id"]
    client.post(f"/api/deals/{did}/tasks", json={"title": "Do it", "assignedUserId": uid}, headers=h)
    m = client.get("/api/users/me/deal-tasks", headers=h)
    assert m.status_code == 200
    body = m.json()
    assert body["openCount"] >= 1
    assert any(x["dealId"] == did for x in body["items"])


def test_me_deal_tasks_excludes_done(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    uid = sales_auth["user_id"]
    did = client.post(
        "/api/deals",
        json={"title": "DoneC", "stage": "Discovery", "value": 0, "currency": "KTZ"},
        headers=h,
    ).json()["id"]
    tid = client.post(
        f"/api/deals/{did}/tasks", json={"title": "X", "assignedUserId": uid}, headers=h
    ).json()["id"]
    client.patch(f"/api/deals/{did}/tasks/{tid}", json={"isDone": 1}, headers=h)
    m = client.get("/api/users/me/deal-tasks", headers=h)
    assert m.status_code == 200
    ids = [x["id"] for x in m.json()["items"]]
    assert tid not in ids


def test_admin_assigns_task_to_sales_user(client: TestClient, db_session, company_admin_auth: dict):
    cid = company_admin_auth["company_id"]
    admin_h = company_admin_auth["headers"]
    sales_uid = add_user(
        db_session,
        email=f"s_{uuid.uuid4().hex[:10]}@t.local",
        role="sales_representative",
        company_id=cid,
    )
    r = client.post(
        "/api/deals",
        json={
            "title": "TeamDeal",
            "stage": "Discovery",
            "value": 1,
            "currency": "KTZ",
            "userId": sales_uid,
        },
        headers=admin_h,
    )
    assert r.status_code == 200, r.text
    did = r.json()["id"]
    r2 = client.post(
        f"/api/deals/{did}/tasks",
        json={"title": "For sales", "assignedUserId": sales_uid},
        headers=admin_h,
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["assignedUserId"] == sales_uid


def test_sales_task_assignee_coerced_to_self(client: TestClient, sales_auth: dict, db_session):
    cid = sales_auth["company_id"]
    admin_uid = add_user(
        db_session,
        email=f"a_{uuid.uuid4().hex[:10]}@t.local",
        role="admin",
        company_id=cid,
    )
    h = sales_auth["headers"]
    did = client.post(
        "/api/deals",
        json={"title": "SDeal", "stage": "Discovery", "value": 0, "currency": "KTZ"},
        headers=h,
    ).json()["id"]
    r = client.post(
        f"/api/deals/{did}/tasks",
        json={"title": "Try delegate", "assignedUserId": admin_uid},
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert r.json()["assignedUserId"] == sales_auth["user_id"]


def test_sales_cannot_patch_task_assignee_to_other(client: TestClient, sales_auth: dict, db_session):
    cid = sales_auth["company_id"]
    admin_uid = add_user(
        db_session,
        email=f"a2_{uuid.uuid4().hex[:10]}@t.local",
        role="admin",
        company_id=cid,
    )
    h = sales_auth["headers"]
    did = client.post(
        "/api/deals",
        json={"title": "SDeal2", "stage": "Discovery", "value": 0, "currency": "KTZ"},
        headers=h,
    ).json()["id"]
    tid = client.post(f"/api/deals/{did}/tasks", json={"title": "T"}, headers=h).json()["id"]
    r = client.patch(f"/api/deals/{did}/tasks/{tid}", json={"assignedUserId": admin_uid}, headers=h)
    assert r.status_code == 403
