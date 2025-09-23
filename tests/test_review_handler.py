import datetime
import os
import sys
import types
from unittest.mock import patch

# Mock heavy dependencies that aren't installed
_dummy = types.ModuleType("dummy")
for mod in ["pandas", "pyodbc", "sqlparse"]:
    sys.modules.setdefault(mod, _dummy)

# dateutil stub
_rel = types.ModuleType("relativedelta")
_rel.relativedelta = object()
_dateutil = types.ModuleType("dateutil")
_dateutil.relativedelta = _rel
sys.modules.setdefault("dateutil", _dateutil)
sys.modules.setdefault("dateutil.relativedelta", _rel)

# Minimal tkinter mocks
_tk = types.ModuleType("tkinter")
_tk.ttk = types.ModuleType("ttk")
_tk.messagebox = types.ModuleType("messagebox")
sys.modules.setdefault("tkinter", _tk)
sys.modules.setdefault("tkinter.ttk", _tk.ttk)
sys.modules.setdefault("tkinter.messagebox", _tk.messagebox)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from handlers.review_handler import generate_stage_review_schedule, update_review_date  # noqa: E402


class FakeCursor:
    def __init__(self):
        self.executed = []
        self.fetchone_results = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params or ()))

    def fetchone(self):
        return self.fetchone_results.pop(0) if self.fetchone_results else None

    def fetchall(self):
        return []


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_generate_stage_review_schedule_creates_expected_records():
    cursor = FakeCursor()
    cursor.fetchone_results.append((1,))
    conn = FakeConnection(cursor)
    stages = [
        {
            "stage_name": "Design",
            "start_date": datetime.date(2024, 1, 1),
            "end_date": datetime.date(2024, 1, 10),
            "num_reviews": 3,
        }
    ]

    with patch("review_handler.connect_to_db", return_value=conn), \
         patch("review_handler.insert_review_cycle_details") as mock_insert, \
         patch("review_handler.upsert_project_review_progress") as mock_upsert:
        result = generate_stage_review_schedule(42, stages)

    assert result is True
    # ensure commit happened and connection closed
    assert conn.committed
    assert conn.closed

    # verify ReviewSchedule inserts
    inserts = [q for q in cursor.executed if q[0].startswith("INSERT INTO ReviewSchedule")]
    assert len(inserts) == 3
    dates = [params[2] for _, params in inserts]
    assert dates == ["2024-01-01", "2024-01-04", "2024-01-07"]

    mock_insert.assert_called_once()
    mock_upsert.assert_called_once_with(42, 1, 3, 0)


def test_generate_stage_review_schedule_no_connection():
    with patch("review_handler.connect_to_db", return_value=None):
        result = generate_stage_review_schedule(1, [])
    assert result is False


def test_update_review_date_sets_manual_override():
    cursor = FakeCursor()
    conn = FakeConnection(cursor)

    with patch("review_handler.connect_to_db", return_value=conn):
        update_review_date(5, "2024-05-01")

    assert conn.committed
    assert ("manual_override = 1" in cursor.executed[0][0])
    assert cursor.executed[0][1] == ("2024-05-01", 5)
