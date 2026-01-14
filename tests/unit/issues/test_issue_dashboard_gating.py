import contextlib

import database


class DummyCursor:
    def execute(self, _sql, _params=None):
        return self

    def fetchone(self):
        return None

    def fetchall(self):
        return []


class DummyConnection:
    def cursor(self):
        return DummyCursor()


@contextlib.contextmanager
def fake_connection():
    yield DummyConnection()


def test_dashboard_kpis_no_successful_run(monkeypatch):
    monkeypatch.setattr(database, "_get_latest_successful_issue_run", lambda _cursor: (None, None))
    monkeypatch.setattr(database, "get_db_connection", lambda *_args, **_kwargs: fake_connection())

    result = database.get_dashboard_issues_kpis()

    assert result["total_issues"] == 0
    assert result["active_issues"] == 0
    assert result["over_30_days"] == 0
    assert result["closed_since_review"] == 0
    assert result["as_of"] is None


def test_dashboard_charts_no_successful_run(monkeypatch):
    monkeypatch.setattr(database, "_get_latest_successful_issue_run", lambda _cursor: (None, None))
    monkeypatch.setattr(database, "get_db_connection", lambda *_args, **_kwargs: fake_connection())

    result = database.get_dashboard_issues_charts()

    assert result["status"] == []
    assert result["priority"] == []
    assert result["discipline"] == []
    assert result["zone"] == []
    assert result["trend_90d"] == []


def test_dashboard_table_no_successful_run(monkeypatch):
    monkeypatch.setattr(database, "_get_latest_successful_issue_run", lambda _cursor: (None, None))
    monkeypatch.setattr(database, "get_db_connection", lambda *_args, **_kwargs: fake_connection())

    result = database.get_dashboard_issues_table()

    assert result["total_count"] == 0
    assert result["rows"] == []
    assert result["as_of"] is None
