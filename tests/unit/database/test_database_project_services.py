import contextlib
import sys
import types

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
        self.executed = []
        self.executemany_calls = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return self

    def fetchall(self):
        if not self._results:
            return []
        return self._results.pop(0)

    def executemany(self, sql, params):
        self.executemany_calls.append((sql, list(params)))


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commit_called = False
        self.rollback_called = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commit_called = True

    def rollback(self):
        self.rollback_called = True


def _fake_get_db_connection(conn):
    @contextlib.contextmanager
    def _ctx():
        yield conn

    return _ctx


def test_get_project_services_updates_status(monkeypatch):
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
        100.0,  # agreed_fee
        None,  # bill_rule
        None,  # notes
        None,  # created_at
        None,  # updated_at
        "planned",  # status
        0.0,  # progress_pct
        0.0,  # claimed_to_date
        None,  # assigned_user_id
        None,  # assigned_user_name
        None,  # start_date
        None,  # end_date
        None,  # review_anchor_date
        None,  # review_interval_days
        None,  # review_count_planned
        None,  # source_template_id
        None,  # source_template_version
        None,  # source_template_hash
        None,  # template_mode
    )

    results = [
        [service_row],  # services
        [],  # review status counts
        [],  # review billing counts
        [(1, "completed", 1)],  # item status counts
        [(1, 1, 1)],  # item billing counts
    ]

    cursor = FakeCursor(results)
    conn = FakeConnection(cursor)
    monkeypatch.setattr(database, "get_db_connection", lambda *_args, **_kwargs: _fake_get_db_connection(conn)())

    services = database.get_project_services(10)

    assert len(services) == 1
    service = services[0]
    assert service["status"] == "completed"
    assert service["progress_pct"] == 100.0
    assert service["billing_progress_pct"] == 100.0
    assert service["billed_amount"] == 100.0
    assert service["agreed_fee_remaining"] == 0.0
    assert cursor.executemany_calls
    assert conn.commit_called is True


def test_get_project_services_empty_returns_empty(monkeypatch):
    cursor = FakeCursor([[]])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(database, "get_db_connection", lambda *_args, **_kwargs: _fake_get_db_connection(conn)())

    services = database.get_project_services(999)

    assert services == []
    assert cursor.executemany_calls == []
    assert conn.commit_called is False
