import os
import sys
from pathlib import Path

import pytest

from config import Config

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


def pytest_ignore_collect(collection_path, config):
    path = Path(str(collection_path))
    if path.suffix != ".py" or not path.name.startswith("test_"):
        return False

    parts = set(path.parts)
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


def _set_env_default(key, value):
    if os.getenv(key) is None and value is not None:
        os.environ[key] = str(value)


def pytest_configure():
    # Ensure tests that read env vars directly get Config defaults unless overridden.
    env_keys = (
        "DB_DRIVER",
        "DB_SERVER",
        "DB_USER",
        "DB_PASSWORD",
        "PROJECT_MGMT_DB",
        "WAREHOUSE_DB",
        "ACC_DB",
        "REVIT_HEALTH_DB",
        "REVIZTO_DB",
        "ACC_SERVICE_URL",
        "REVIZTO_SERVICE_URL",
        "APS_AUTH_SERVICE_URL",
        "APS_AUTH_LOGIN_PATH",
        "ACC_SERVICE_TOKEN",
        "REVIZTO_SERVICE_TOKEN",
    )
    for key in env_keys:
        _set_env_default(key, getattr(Config, key, None))
