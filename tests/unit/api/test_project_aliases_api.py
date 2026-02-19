import types
import sys

import pytest

flask = pytest.importorskip("flask")
from backend import flask_app as app


_dummy = types.ModuleType("dummy")
sys.modules.setdefault("pyodbc", _dummy)


def test_update_project_alias_rejects_blank_name(monkeypatch):
    def fake_get_alias(_alias_name):
        return {"alias_name": "Old", "project_id": 1}

    monkeypatch.setattr("backend.app._get_alias_by_name", fake_get_alias)
    client = app.test_client()
    resp = client.patch("/api/project_aliases/Old", json={"alias_name": "   "})

    assert resp.status_code == 400
    assert "alias_name is required" in resp.get_json()["error"]


def test_get_project_aliases_without_stats(monkeypatch):
    row = ("Alias A", 1, "Project A", "ACTIVE", "Manager A", None)

    def fake_fetch_rows():
        return [row]

    monkeypatch.setattr("backend.app._fetch_project_alias_rows", fake_fetch_rows)
    client = app.test_client()
    resp = client.get("/api/project_aliases?include_stats=false")

    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload[0]["alias_name"] == "Alias A"
    assert payload[0]["project_id"] == 1
    assert payload[0]["issue_summary"]["total_issues"] == 0


def test_get_unmapped_aliases_without_stats(monkeypatch):
    def fake_unmapped_names(limit=200):
        return [{"project_name": "External A"}]

    monkeypatch.setattr(
        "services.optimized_alias_service.OptimizedProjectAliasManager.discover_unmapped_names",
        fake_unmapped_names,
    )
    client = app.test_client()
    resp = client.get("/api/project_aliases/unmapped?include_stats=false&limit=10")

    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload == [{"project_name": "External A"}]
