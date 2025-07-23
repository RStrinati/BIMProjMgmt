import datetime
import os
import sys
import types

dummy = types.ModuleType("dummy")
for mod in ["pandas", "pyodbc", "sqlparse"]:
    sys.modules.setdefault(mod, dummy)

tk_mod = types.ModuleType("tkinter")
tk_mod.ttk = types.ModuleType("ttk")
tk_mod.messagebox = types.ModuleType("messagebox")
sys.modules.setdefault("tkinter", tk_mod)
sys.modules.setdefault("tkinter.ttk", tk_mod.ttk)
sys.modules.setdefault("tkinter.messagebox", tk_mod.messagebox)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from acc_handler import parse_custom_datetime, convert_to_sql_compatible  # noqa: E402


def test_parse_custom_datetime_microseconds():
    dt_str = "2025-07-01 04:24:43.189"
    parsed = parse_custom_datetime(dt_str, "created_at")
    assert parsed == datetime.datetime(2025, 7, 1, 4, 24, 43, 189000)


def test_convert_to_sql_compatible_numbers():
    assert convert_to_sql_compatible("42") == 42
    assert convert_to_sql_compatible("3.14") == 3.14
