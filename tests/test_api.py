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


def test_review_cycles_get(monkeypatch):
    monkeypatch.setattr('backend.app.get_review_cycles', lambda pid: [(1, 2, '2024-01-01', '2024-02-01', 3)])
    client = app.test_client()
    resp = client.get('/api/reviews/1')
    assert resp.status_code == 200
    assert resp.get_json()[0]['review_cycle_id'] == 1


def test_create_review_cycle(monkeypatch):
    monkeypatch.setattr('backend.app.create_review_cycle', lambda *a: 5)
    client = app.test_client()
    payload = {'project_id': 1, 'stage_id': 2, 'start_date': '2024-01-01', 'end_date': '2024-02-01', 'num_reviews': 3, 'created_by': 9}
    resp = client.post('/api/reviews', json=payload)
    assert resp.status_code == 201
    assert resp.get_json()['id'] == 5


def test_update_review_cycle(monkeypatch):
    called = {}
    def fake_update(cid, s, e, n, stage):
        called.update({'cid': cid, 's': s, 'e': e, 'n': n, 'stage': stage})
        return True
    monkeypatch.setattr('backend.app.update_review_cycle', fake_update)
    client = app.test_client()
    resp = client.put('/api/reviews/3', json={'num_reviews': 4})
    assert resp.status_code == 200
    assert called['cid'] == 3


def test_delete_review_cycle(monkeypatch):
    monkeypatch.setattr('backend.app.delete_review_cycle', lambda cid: True)
    client = app.test_client()
    resp = client.delete('/api/reviews/7')
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True


def test_review_cycle_tasks_get(monkeypatch):
    monkeypatch.setattr('backend.app.get_review_cycle_tasks', lambda sid: [(1, 5, 2, 'Pending')])
    client = app.test_client()
    resp = client.get('/api/review_tasks/10')
    assert resp.status_code == 200
    assert resp.get_json()[0]['review_task_id'] == 1


def test_update_review_cycle_task(monkeypatch):
    called = {}
    def fake_upd(tid, a, st):
        called.update({'tid': tid, 'a': a, 'st': st})
        return True
    monkeypatch.setattr('backend.app.update_review_cycle_task', fake_upd)
    client = app.test_client()
    resp = client.put('/api/review_tasks/4', json={'status': 'Done'})
    assert resp.status_code == 200
    assert called['tid'] == 4


def test_bep_get(monkeypatch):
    monkeypatch.setattr('backend.app.get_bep_matrix', lambda pid: [(1, 'Sec', 2, 'Draft', '')])
    client = app.test_client()
    resp = client.get('/api/bep/1')
    assert resp.status_code == 200
    assert resp.get_json()[0]['section_id'] == 1


def test_bep_section_post(monkeypatch):
    monkeypatch.setattr('backend.app.upsert_bep_section', lambda *a: True)
    client = app.test_client()
    payload = {'project_id': 1, 'section_id': 2}
    resp = client.post('/api/bep/section', json=payload)
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True


def test_bep_status_put(monkeypatch):
    called = {}
    def fake_upd(pid, sid, status):
        called.update({'pid': pid, 'sid': sid, 'status': status})
        return True
    monkeypatch.setattr('backend.app.update_bep_status', fake_upd)
    client = app.test_client()
    resp = client.put('/api/bep/status', json={'project_id':1,'section_id':2,'status':'Draft'})
    assert resp.status_code == 200
    assert called['sid'] == 2

