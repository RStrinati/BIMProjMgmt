import contextlib
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

import database_pool as dp


class DummyCursor:
    def execute(self, _sql):
        return self

    def close(self):
        pass


class DummyConnection:
    def __init__(self):
        self.autocommit = False
        self.closed = False
        self.rollback_called = False

    def cursor(self):
        return DummyCursor()

    def rollback(self):
        self.rollback_called = True

    def close(self):
        self.closed = True


def test_connection_pool_exhaustion(monkeypatch):
    created = []

    def fake_connect(_conn_string, timeout=10):
        conn = DummyConnection()
        created.append(conn)
        return conn

    monkeypatch.setattr(dp.pyodbc, "connect", fake_connect)
    pool = dp.ConnectionPool("TestDB", min_size=0, max_size=1)
    monkeypatch.setattr(pool, "_is_connection_alive", lambda _conn: True)

    conn = pool.get_connection(timeout=0)

    with pytest.raises(Exception) as excinfo:
        pool.get_connection(timeout=0)

    assert "pool exhausted" in str(excinfo.value).lower()
    pool.return_connection(conn)


def test_return_connection_discards_dead(monkeypatch):
    pool = dp.ConnectionPool("TestDB", min_size=0, max_size=1)
    conn = DummyConnection()
    pool._created_connections = 1

    monkeypatch.setattr(pool, "_is_connection_alive", lambda _conn: False)
    pool.return_connection(conn)

    assert conn.closed is True
    assert conn.rollback_called is True
    assert pool._created_connections == 0


def test_execute_with_retry_backoff(monkeypatch):
    manager = dp.DatabaseManager()

    @contextlib.contextmanager
    def fake_connection():
        yield DummyConnection()

    monkeypatch.setattr(manager, "get_connection", lambda *_args, **_kwargs: fake_connection())

    sleeps = []
    monkeypatch.setattr(dp.time, "sleep", lambda seconds: sleeps.append(seconds))

    attempts = {"count": 0}

    def flaky_operation(_conn):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise dp.pyodbc.OperationalError("transient")
        return "ok"

    result = manager.execute_with_retry(flaky_operation, max_retries=3, retry_delay=1.0)

    assert result == "ok"
    assert sleeps == [1.0, 2.0]
