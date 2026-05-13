from fastapi.testclient import TestClient


def test_healthz_no_db():
    from app.main import app

    with TestClient(app) as client:
        r = client.get("/healthz")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_readyz_with_db(client: TestClient):
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json().get("database") == "ok"
