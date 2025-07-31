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


def test_get_project_details(monkeypatch):
    monkeypatch.setattr('backend.app.get_project_details', lambda pid: {'project_name': 'P', 'start_date': '2024-01-01', 'end_date': '2024-12-31', 'status': 'Active', 'priority': 'High'})
    client = app.test_client()
    resp = client.get('/api/project/1')
    assert resp.status_code == 200
    assert resp.get_json()['project_name'] == 'P'


def test_review_summary(monkeypatch):
    monkeypatch.setattr('backend.app.get_review_summary', lambda p, c: {'cycle_id': c, 'scoped_reviews': 5})
    client = app.test_client()
    resp = client.get('/api/review_summary?project_id=1&cycle_id=2')
    assert resp.status_code == 200
    assert resp.get_json()['cycle_id'] == '2'


def test_contractual_links(monkeypatch):
    monkeypatch.setattr('backend.app.get_contractual_links', lambda p, c=None: [('clause', 'event', 100, 'Pending')])
    client = app.test_client()
    resp = client.get('/api/contractual_links?project_id=1&cycle_id=2')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data[0]['bep_clause'] == 'clause'


def test_cycle_ids(monkeypatch):
    monkeypatch.setattr('backend.app.get_cycle_ids', lambda pid: ['1', '2'])
    client = app.test_client()
    resp = client.get('/api/cycle_ids/1')
    assert resp.status_code == 200
    assert resp.get_json() == ['1', '2']


def test_project_folders_get(monkeypatch):
    monkeypatch.setattr('backend.app.get_project_folders', lambda pid: ('A', 'B'))
    client = app.test_client()
    resp = client.get('/api/project/1/folders')
    assert resp.status_code == 200
    assert resp.get_json()['model_path'] == 'A'


def test_project_folders_patch(monkeypatch):
    called = {}

    def fake_update(pid, m, d, i):
        called.update({'pid': pid, 'm': m, 'd': d, 'i': i})
        return True

    monkeypatch.setattr('backend.app.update_project_folders', fake_update)
    client = app.test_client()
    resp = client.patch('/api/project/2/folders', json={'model_path': 'X'})
    assert resp.status_code == 200
    assert called == {'pid': 2, 'm': 'X', 'd': None, 'i': None}


def test_update_project_details(monkeypatch):
    called = {}

    def fake_update(pid, start, end, status, priority):
        called.update({'pid': pid, 'start': start, 'end': end, 'status': status, 'priority': priority})
        return True

    monkeypatch.setattr('backend.app.update_project_details', fake_update)
    client = app.test_client()
    resp = client.patch('/api/project/3', json={'status': 'A'})
    assert resp.status_code == 200
    assert called['pid'] == 3


def test_create_project(monkeypatch):
    monkeypatch.setattr('backend.app.insert_project', lambda n, f, i: True)
    client = app.test_client()
    resp = client.post('/api/project', json={'project_name': 'New'})
    assert resp.status_code == 201
    assert resp.get_json()['success'] is True


def test_extract_files(monkeypatch):
    monkeypatch.setattr('backend.app.get_project_folders', lambda pid: ('p', None))
    monkeypatch.setattr('backend.app.insert_files_into_tblACCDocs', lambda pid, p: True)
    client = app.test_client()
    resp = client.post('/api/extract_files', json={'project_id': 4})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True


def test_projects_full(monkeypatch):
    monkeypatch.setattr(
        'backend.app.get_projects_full',
        lambda: [{'project_id': 1, 'project_name': 'P'}],
    )
    client = app.test_client()
    resp = client.get('/api/projects_full')
    assert resp.status_code == 200
    assert resp.get_json()[0]['project_name'] == 'P'


def test_update_full_project(monkeypatch):
    called = {}

    def fake_fin(pid, cv, pt):
        called['fin'] = (pid, cv, pt)
        return True

    def fake_client(pid, cc, ce):
        called['cli'] = (pid, cc, ce)
        return True

    monkeypatch.setattr('backend.app.update_project_financials', fake_fin)
    monkeypatch.setattr('backend.app.update_client_info', fake_client)
    client = app.test_client()
    resp = client.put('/api/projects/5', json={'contract_value': 10})
    assert resp.status_code == 200
    assert called['fin'] == (5, 10, None)

