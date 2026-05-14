"""Тесты REST API контактов."""

import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import add_company, add_user


def test_list_contacts_requires_auth(client: TestClient):
    assert client.get("/api/contacts").status_code == 401


def test_create_and_list_contact(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    email = f"c_{uuid.uuid4().hex[:10]}@client.test"
    body = {
        "name": "Клиент",
        "email": email,
        "phone": "+7 700 111 2233",
        "company": "ACME",
        "role": "CEO",
        "status": "Active",
    }
    r = client.post("/api/contacts", json=body, headers=h)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["email"] == email
    assert data["companyId"] == sales_auth["company_id"]
    cid = data["id"]

    r2 = client.get("/api/contacts", headers=h)
    assert r2.status_code == 200
    ids = {x["id"] for x in r2.json()}
    assert cid in ids


def test_search_contact_by_phone(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    email = f"ph_{uuid.uuid4().hex[:10]}@client.test"
    client.post(
        "/api/contacts",
        json={
            "name": "P",
            "email": email,
            "phone": "+7 (701) 999-88-77",
            "status": "Active",
        },
        headers=h,
    )
    r = client.get("/api/contacts/search", params={"phone": "+77019998877"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["email"] == email


def test_search_foreign_company_contact_returns_404(client: TestClient, db_session: Session):
    """Чужой tenant: поиск по телефону маскируется как 404."""
    ca = add_company(db_session, "A")
    cb = add_company(db_session, "B")
    email_a = f"ua_{uuid.uuid4().hex[:10]}@t.local"
    email_b = f"ub_{uuid.uuid4().hex[:10]}@t.local"
    add_user(db_session, email=email_a, role="sales_representative", company_id=ca)
    add_user(db_session, email=email_b, role="sales_representative", company_id=cb)
    from app import models

    contact_b_id = str(uuid.uuid4())
    db_session.add(
        models.Contact(
            id=contact_b_id,
            name="Foreign",
            email=f"fc_{uuid.uuid4().hex[:8]}@x.test",
            phone="+7 702 000 00 01",
            companyId=cb,
            status="Active",
        )
    )
    db_session.commit()

    from tests.conftest import login_access_token

    token_a = login_access_token(client, email_a)
    h = {"Authorization": f"Bearer {token_a}"}
    r = client.get("/api/contacts/search", params={"phone": "+77020000001"}, headers=h)
    assert r.status_code == 404


def test_patch_and_delete_contact(client: TestClient, sales_auth: dict):
    h = sales_auth["headers"]
    r = client.post(
        "/api/contacts",
        json={
            "name": "ToPatch",
            "email": f"patch_{uuid.uuid4().hex[:10]}@t.test",
            "status": "Active",
        },
        headers=h,
    )
    cid = r.json()["id"]
    r2 = client.patch(f"/api/contacts/{cid}", json={"name": "PatchedName"}, headers=h)
    assert r2.status_code == 200
    assert r2.json()["name"] == "PatchedName"

    r3 = client.delete(f"/api/contacts/{cid}", headers=h)
    assert r3.status_code == 200
    assert r3.json().get("status") == "deleted"
