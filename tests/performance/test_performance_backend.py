import sys
import types

import pytest

if "pyodbc" not in sys.modules:
    pyodbc_stub = types.SimpleNamespace()

    class PyodbcError(Exception):
        pass

    class PyodbcOperationalError(PyodbcError):
        pass

    class PyodbcInterfaceError(PyodbcError):
        pass

    pyodbc_stub.Error = PyodbcError
    pyodbc_stub.OperationalError = PyodbcOperationalError
    pyodbc_stub.InterfaceError = PyodbcInterfaceError
    pyodbc_stub.Connection = object
    pyodbc_stub.connect = lambda *_args, **_kwargs: None
    sys.modules["pyodbc"] = pyodbc_stub

import database


class FakeCursor:
    def __init__(self, results):
        self._results = list(results)
        self.execute_calls = []

    def execute(self, sql, params=None):
        self.execute_calls.append((sql, params))
        return self

    def fetchall(self):
        if not self._results:
            return []
        return self._results.pop(0)


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def rollback(self):
        pass


class _FakeConnectionContext:
    def __init__(self, conn):
        self._conn = conn

    def __enter__(self):
        return self._conn

    def __exit__(self, _exc_type, _exc, _tb):
        return False


@pytest.mark.performance
def test_get_project_services_query_count(monkeypatch):
    service_row = (
        1,  # service_id
        10,  # project_id
        None,  # phase
        "SVC-1",  # service_code
        "Service One",  # service_name
        "review",  # unit_type
        None,  # unit_qty
        None,  # unit_rate
        None,  # lump_sum_fee
        0.0,  # agreed_fee
        None,  # bill_rule
        None,  # notes
        None,  # created_at
        None,  # updated_at
        "planned",  # status
        0.0,  # progress_pct
        0.0,  # claimed_to_date
        None,  # assigned_user_id
        None,  # assigned_user_name
    )

    results = [
        [service_row],  # services
        [],  # review status counts
        [],  # review billing counts
        [],  # item status counts
        [],  # item billing counts
    ]

    cursor = FakeCursor(results)
    conn = FakeConnection(cursor)
    monkeypatch.setattr(
        database,
        "get_db_connection",
        lambda *_args, **_kwargs: _FakeConnectionContext(conn),
    )

    services = database.get_project_services(10)

    assert len(services) == 1
    assert len(cursor.execute_calls) == 5


@pytest.mark.performance
def test_warehouse_metrics_cache_hit(monkeypatch):
    call_count = {"count": 0}

    def fake_calculate(_project_ids, _client_ids, _project_type_ids):
        call_count["count"] += 1
        return {"ok": True}

    times = {"now": 1000.0}

    def fake_time():
        return times["now"]

    monkeypatch.setattr(database, "_calculate_warehouse_dashboard_metrics", fake_calculate)
    monkeypatch.setattr(database, "time", fake_time)
    database._WAREHOUSE_METRICS_CACHE.clear()

    first = database.get_warehouse_dashboard_metrics(project_ids=[1])
    second = database.get_warehouse_dashboard_metrics(project_ids=[1])

    assert first == {"ok": True}
    assert second == {"ok": True}
    assert call_count["count"] == 1
