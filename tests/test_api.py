import sys
import types
import pytest

flask = pytest.importorskip("flask")
from backend.app import app

# Mock heavy dependencies
_dummy = types.ModuleType("dummy")
for mod in ["pyodbc"]:
    sys.modules.setdefault(mod, _dummy)


def test_get_projects_endpoint(monkeypatch):
    monkeypatch.setattr('backend.app.get_projects', lambda: [(1, 'A')])
    client = app.test_client()
    resp = client.get('/api/projects')
    assert resp.status_code == 200
    assert resp.get_json() == [{'project_id': 1, 'project_name': 'A'}]


def test_patch_review_task(monkeypatch):
    called = {}
    def fake_update(schedule_id, user_id):
        called['schedule_id'] = schedule_id
        called['user_id'] = user_id
        return True
    monkeypatch.setattr('backend.app.update_review_task_assignee', fake_update)
    client = app.test_client()
    resp = client.patch('/api/review_task/5', json={'user_id': 8})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
    assert called == {'schedule_id': 5, 'user_id': 8}
