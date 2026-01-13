import os
import sys
from pathlib import Path

import pytest


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

LEGACY_DIRS = {"legacy_root", "legacy_tools"}
INTEGRATION_HINTS = (
    "get_db_connection",
    "connect_to_db",
    "pyodbc",
    "requests.",
    "subprocess.",
    "Config.",
)


def _read_text(path):
    try:
        return path.read()
    except Exception:
        try:
            return Path(str(path)).read_text(errors="ignore")
        except Exception:
            return ""


def pytest_ignore_collect(path, config):
    if path.ext != ".py" or not path.basename.startswith("test_"):
        return False

    parts = set(Path(str(path)).parts)
    if parts & LEGACY_DIRS and os.getenv("PYTEST_INCLUDE_LEGACY") != "1":
        return True

    text = _read_text(path)
    if "def test_" not in text and "unittest.TestCase" not in text:
        if os.getenv("PYTEST_INCLUDE_SCRIPTS") != "1":
            return True

    return False


def pytest_collection_modifyitems(config, items):
    for item in items:
        path = Path(str(item.fspath))
        text = _read_text(item.fspath)

        if set(path.parts) & LEGACY_DIRS:
            item.add_marker(pytest.mark.legacy)
        elif any(hint in text for hint in INTEGRATION_HINTS):
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)
