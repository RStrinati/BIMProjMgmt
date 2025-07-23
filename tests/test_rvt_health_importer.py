import os
import sys
import types

# Mock heavy dependencies
_dummy = types.ModuleType("dummy")
for mod in ["pandas", "pyodbc", "sqlparse"]:
    sys.modules.setdefault(mod, _dummy)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from rvt_health_importer import safe_float  # noqa: E402


def test_safe_float():
    assert safe_float("10.5") == 10.5
    assert safe_float("bad") is None
    assert safe_float(None) is None
