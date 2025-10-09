#!/usr/bin/env python3
"""Utility to run the preparation steps for the React-ready Flask API."""
from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(REPO_ROOT))

from config import Config  # noqa: E402

try:  # pragma: no cover - import guarded for helpful error when missing dependency
    import pyodbc  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover - handled in main()
    pyodbc = None  # type: ignore
    PYODBC_IMPORT_ERROR = exc
else:
    PYODBC_IMPORT_ERROR = None

SQL_FILES: List[Path] = [
    REPO_ROOT / "sql" / "update_review_schedule_schema.sql",
    REPO_ROOT / "sql" / "add_project_fields.sql",
    REPO_ROOT / "sql" / "update_projects_view.sql",
    REPO_ROOT / "sql" / "phase1_enhancements.sql",
]

# Keys that must be set for the API and database migrations to work. The
# defaults in ``Config`` are development placeholders, so we report when they
# are still being used instead of explicit environment variables.
REQUIRED_ENV_VARS = {
    "DB_SERVER": "SQL Server host name, e.g. localhost\\\SQLEXPRESS",
    "DB_USER": "SQL Server username",
    "DB_PASSWORD": "SQL Server password",
    "DB_DRIVER": "ODBC driver name, e.g. ODBC Driver 18 for SQL Server",
    "PROJECT_MGMT_DB": "Primary Project Management database name",
    "ACC_SERVICE_URL": "Autodesk Construction Cloud proxy base URL",
    "REVIZTO_SERVICE_URL": "Revizto proxy base URL",
    "ACC_SERVICE_TOKEN": "Autodesk Construction Cloud API token",
    "REVIZTO_SERVICE_TOKEN": "Revizto API token",
}


def _split_batches(sql_text: str) -> List[str]:
    """Split SQL Server batches on ``GO`` delimiters."""
    batches: List[str] = []
    current: List[str] = []
    for line in sql_text.splitlines():
        if line.strip().upper() == "GO":
            statement = "\n".join(current).strip()
            if statement:
                batches.append(statement)
            current = []
        else:
            current.append(line)
    remainder = "\n".join(current).strip()
    if remainder:
        batches.append(remainder)
    return batches


def _connect() -> "pyodbc.Connection":
    assert pyodbc is not None  # for type-checkers
    conn_str = (
        f"DRIVER={{{Config.DB_DRIVER}}};"
        f"SERVER={Config.DB_SERVER};"
        f"DATABASE={Config.PROJECT_MGMT_DB};"
        f"UID={Config.DB_USER};"
        f"PWD={Config.DB_PASSWORD}"
    )
    connection = pyodbc.connect(conn_str)
    connection.autocommit = True
    return connection


def _execute_batches(
    cursor: "pyodbc.Cursor | None", batches: Iterable[str], *, dry_run: bool
) -> None:
    for idx, statement in enumerate(batches, start=1):
        if dry_run:
            logging.info("Dry run - batch %s (not executed):\n%s", idx, statement)
            continue
        logging.info("Executing batch %s", idx)
        logging.debug(statement)
        assert cursor is not None
        cursor.execute(statement)


def _run_sql_file(
    cursor: "pyodbc.Cursor | None", sql_path: Path, *, dry_run: bool
) -> None:
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")
    logging.info("Applying %s", sql_path.relative_to(REPO_ROOT))
    sql_text = sql_path.read_text(encoding="utf-8")
    batches = _split_batches(sql_text)
    if not batches:
        logging.warning("No SQL statements detected in %s", sql_path.name)
        return
    _execute_batches(cursor, batches, dry_run=dry_run)


def _check_env_configuration() -> None:
    logging.info("Checking environment variables")
    missing = []
    defaulted = []
    for key, description in REQUIRED_ENV_VARS.items():
        value = os.getenv(key)
        if value is None or not value.strip():
            missing.append((key, description))
            continue
        default_value = getattr(Config, key, None)
        if default_value and value == default_value:
            # Environment variable equals the Config default (likely placeholder).
            defaulted.append(key)
    if missing:
        logging.warning("Missing environment variables detected:")
        for key, description in missing:
            logging.warning("  %s – %s", key, description)
    if defaulted:
        logging.warning(
            "The following environment variables are still using the placeholder defaults "
            "from config.py: %s",
            ", ".join(defaulted),
        )
    if not missing and not defaulted:
        logging.info("All required environment variables look configured.")


def _report_frontend_status() -> None:
    frontend_env = os.getenv("FRONTEND_DIR")
    default_frontend = REPO_ROOT / "frontend"
    frontend_dir = Path(frontend_env).expanduser() if frontend_env else default_frontend
    logging.info("Checking frontend bundle in %s", frontend_dir)
    index_file = frontend_dir / "index.html"
    if not frontend_dir.exists():
        logging.warning(
            "Frontend build directory does not exist. Run your React build and set FRONTEND_DIR "
            "if you output to a different location.",
        )
        return
    if not index_file.exists():
        logging.warning(
            "Frontend directory is present but index.html is missing. Run `npm run build` (or your bundler) "
            "and copy the output into %s.",
            frontend_dir,
        )
        return
    logging.info("Found React bundle entrypoint at %s", index_file)


def _check_frontend_toolchain() -> None:
    logging.info("Checking Node.js toolchain for React builds")
    required_commands = {
        "node": "Install Node.js from https://nodejs.org/ to build the React app.",
        "npm": "npm ships with Node.js and is required for running npm scripts like `npm run build`.",
    }
    missing: List[str] = []
    for command, guidance in required_commands.items():
        command_path = shutil.which(command)
        if command_path is None:
            missing.append(f"{command} – {guidance}")
            continue
        try:
            output = subprocess.check_output(
                [command, "--version"], text=True, stderr=subprocess.STDOUT
            ).strip()
        except Exception as exc:  # pragma: no cover - informational logging only
            logging.warning("Detected %s at %s but could not determine version: %s", command, command_path, exc)
            continue
        version = output.splitlines()[-1] if output else "unknown"
        logging.info("Detected %s at %s (version %s)", command, command_path, version)
    if missing:
        logging.warning("Missing Node.js tooling required to build the React frontend:")
        for message in missing:
            logging.warning("  %s", message)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare the Flask API for the React frontend")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print SQL statements without executing them",
    )
    args = parser.parse_args(argv)

    if PYODBC_IMPORT_ERROR is not None and not args.dry_run:
        parser.error(
            "pyodbc is not installed. Run ./setup_env.sh first to create the virtual environment "
            "and install dependencies.",
        )

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    _check_env_configuration()
    _check_frontend_toolchain()

    if args.dry_run:
        if PYODBC_IMPORT_ERROR is not None:
            logging.warning(
                "pyodbc is not installed; continuing because --dry-run was requested."
            )
        logging.info("Dry run requested; skipping database connection.")
        for sql_path in SQL_FILES:
            _run_sql_file(None, sql_path, dry_run=True)
        logging.info("Dry run complete. No changes were applied.")
    else:
        logging.info(
            "Connecting to SQL Server %s / %s", Config.DB_SERVER, Config.PROJECT_MGMT_DB
        )
        try:
            with _connect() as connection:
                cursor = connection.cursor()
                for sql_path in SQL_FILES:
                    _run_sql_file(cursor, sql_path, dry_run=False)
        except Exception as exc:  # pragma: no cover - surfaced to operator for remediation
            logging.error("Database preparation failed: %s", exc)
            return 1
        logging.info("Database preparation scripts executed successfully.")

    _report_frontend_status()
    logging.info("Preparation steps finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
