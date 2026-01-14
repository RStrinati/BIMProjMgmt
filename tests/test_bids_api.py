import pytest

flask = pytest.importorskip("flask")
from backend import flask_app as app


def _schema_ok():
    return {"bid_module_ready": True}, None


def test_create_bid_requires_name(monkeypatch):
    monkeypatch.setattr("backend.app._ensure_bid_schema_ready", lambda: _schema_ok())
    client = app.test_client()
    resp = client.post("/api/bids", json={"bid_type": "PROPOSAL", "status": "DRAFT"})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "bid_name is required"


def test_create_bid_success(monkeypatch):
    monkeypatch.setattr("backend.app._ensure_bid_schema_ready", lambda: _schema_ok())
    monkeypatch.setattr("backend.app.create_bid", lambda payload: {"bid_id": 11, "bid_name": payload["bid_name"]})
    client = app.test_client()
    resp = client.post("/api/bids", json={"bid_name": "Bid Alpha", "bid_type": "PROPOSAL", "status": "DRAFT"})
    assert resp.status_code == 201
    assert resp.get_json()["bid_id"] == 11


def test_create_bid_scope_item(monkeypatch):
    monkeypatch.setattr("backend.app._ensure_bid_schema_ready", lambda: _schema_ok())
    monkeypatch.setattr("backend.app.create_bid_scope_item", lambda bid_id, payload: 5)
    client = app.test_client()
    resp = client.post("/api/bids/2/scope-items", json={"title": "Design coordination"})
    assert resp.status_code == 201
    assert resp.get_json()["scope_item_id"] == 5


def test_award_bid(monkeypatch):
    monkeypatch.setattr("backend.app._schema_report", lambda: {"ok": True})
    monkeypatch.setattr(
        "backend.app.award_bid",
        lambda bid_id, create_new_project, project_id, project_payload: {
            "project_id": 42,
            "created_services": 2,
            "created_reviews": 3,
            "created_claims": 1,
        },
    )
    client = app.test_client()
    resp = client.post("/api/bids/7/award", json={"create_new_project": False, "project_id": 42})
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["project_id"] == 42
    assert payload["created_services"] == 2
