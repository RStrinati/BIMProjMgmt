import sys
import types

import pytest

flask = pytest.importorskip("flask")
from backend import flask_app as app


_dummy = types.ModuleType("dummy")
sys.modules.setdefault("pyodbc", _dummy)


def test_get_revizto_project_mappings_active_only_false(monkeypatch):
    called = {}

    def fake_get_mappings(active_only=True):
        called["active_only"] = active_only
        return [{"revizto_project_uuid": "abc", "pm_project_id": 1}]

    monkeypatch.setattr("backend.app.get_revizto_project_mappings", fake_get_mappings)
    client = app.test_client()
    resp = client.get("/api/mappings/revizto-projects?active_only=false")

    assert resp.status_code == 200
    assert called["active_only"] is False
    assert resp.get_json() == [{"revizto_project_uuid": "abc", "pm_project_id": 1}]


def test_upsert_revizto_project_mapping_requires_uuid():
    client = app.test_client()
    resp = client.post("/api/mappings/revizto-projects", json={})

    assert resp.status_code == 400
    assert "revizto_project_uuid is required" in resp.get_json()["error"]


def test_create_issue_attribute_mapping_missing_fields():
    client = app.test_client()
    resp = client.post("/api/mappings/issue-attributes", json={"source_system": "acc"})

    assert resp.status_code == 400
    assert "Missing fields" in resp.get_json()["error"]


def test_issue_reliability_report_failure(monkeypatch):
    def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr("backend.app.get_issue_reliability_report", boom)
    client = app.test_client()
    resp = client.get("/api/settings/issue-reliability")

    assert resp.status_code == 500
    assert "boom" in resp.get_json()["error"]


def test_dashboard_warehouse_metrics_includes_filters(monkeypatch):
    called = {}

    def fake_metrics(project_ids=None, client_ids=None, project_type_ids=None):
        called["project_ids"] = project_ids
        called["client_ids"] = client_ids
        called["project_type_ids"] = project_type_ids
        return {"total": 1}

    monkeypatch.setattr("backend.app.get_warehouse_dashboard_metrics", fake_metrics)
    client = app.test_client()
    resp = client.get("/api/dashboard/warehouse-metrics?project_ids=1,2&client_ids=3&type_ids=4")

    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["total"] == 1
    assert payload["filters"]["project_ids"] == [1, 2]
    assert payload["filters"]["client_ids"] == [3]
    assert payload["filters"]["type_ids"] == [4]
    assert called == {"project_ids": [1, 2], "client_ids": [3], "project_type_ids": [4]}
