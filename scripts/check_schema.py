
from __future__ import annotations
#!/usr/bin/env python3
"""Schema checker for the Project Management database.

This script compares the expected schema defined in ``constants/schema.py``
with the actual schema in a SQL Server database. It can optionally create
missing tables/columns and update ``constants/schema.py`` when the database
contains tables or columns not yet described in the constants file.

Usage::

    python check_schema.py [--autofix] [--update-constants]

Environment variables from :mod:`config` are used to establish the database
connection.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import inspect
import re
from pathlib import Path
from typing import Dict, List

import pyodbc
from pyparsing import col

from config import Config
from constants import schema as S


# ---------------------------------------------------------------------------
# Schema Introspection
# ---------------------------------------------------------------------------

def load_required_schema() -> Dict[str, List[str]]:
    """Return mapping of required tables to column lists defined in constants."""
    tables: Dict[str, List[str]] = {}
    for _name, obj in inspect.getmembers(S):
        if inspect.isclass(obj) and hasattr(obj, "TABLE"):
            table = getattr(obj, "TABLE")
            cols = [v for k, v in obj.__dict__.items() if k.isupper() and k != "TABLE"]
            tables[table] = cols
    return tables


def table_to_class(table: str) -> str:
    """Convert a table name to a Python class name.

    ``str.capitalize`` would lowercase the remainder of the string which breaks
    acronyms such as ``ACCDocs``.  Instead we only uppercase the first
    character of each component and keep the rest as-is.
    """
    name = re.sub(r"^tbl", "", table, flags=re.IGNORECASE)
    parts = re.split(r"[_\s]+", name)
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def column_to_const(column: str) -> str:
    """Convert a column name to a valid constant name."""
    return re.sub(r"[^A-Za-z0-9]", "_", column).upper()


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

def connect() -> pyodbc.Connection:
    """Return a pyodbc connection using configuration values."""
    conn_str = (
        f"DRIVER={{{Config.DB_DRIVER}}};SERVER={Config.DB_SERVER};"
        f"DATABASE={Config.PROJECT_MGMT_DB};UID={Config.DB_USER};PWD={Config.DB_PASSWORD}"
    )
    return pyodbc.connect(conn_str)


def fetch_existing_schema(cursor: pyodbc.Cursor) -> Dict[str, List[str]]:
    """Return mapping of existing tables to their column lists."""
    existing: Dict[str, List[str]] = {}
    cursor.execute(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"
    )
    for row in cursor.fetchall():
        table = row.TABLE_NAME
        cursor.execute(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?",
            table,
        )
        cols = [r.COLUMN_NAME for r in cursor.fetchall()]
        existing[table] = cols
    return existing


def generate_create_table_sql(table: str, columns: List[str]) -> str:
    """Generate a simple ``CREATE TABLE`` statement."""
    col_defs = ",\n    ".join(f"[{c}] NVARCHAR(MAX)" for c in columns)
    return f"CREATE TABLE [{table}] (\n    {col_defs}\n);"


def generate_add_column_sql(table: str, columns: List[str]) -> List[str]:
    """Generate ``ALTER TABLE ... ADD`` statements for columns."""
    return [f"ALTER TABLE [{table}] ADD [{c}] NVARCHAR(MAX);" for c in columns]


# ---------------------------------------------------------------------------
# Constants file updater
# ---------------------------------------------------------------------------

def update_constants_file(missing: Dict[str, List[str]]) -> None:
    """Append missing table/column constants to ``constants/schema.py``."""
    path = Path(__file__).resolve().parent.parent / "constants" / "schema.py"
    lines = path.read_text().splitlines()
    for table, columns in missing.items():
        class_name = table_to_class(table)
        class_def = f"class {class_name}:"
        if class_def in lines:
            idx = lines.index(class_def) + 1
            # Find insertion point: before next class or EOF
            while idx < len(lines) and not lines[idx].startswith("class "):
                idx += 1
            insert_at = idx
            for col in columns:
                const_name = column_to_const(col)
                lines.insert(insert_at, f"    {const_name} = \"{col}\"")
                insert_at += 1
        else:
            new_lines = ["", class_def, f"    TABLE = \"{table}\""]
            new_lines.extend(f"    {column_to_const(c)} = \"{c}\"" for c in columns)
            lines.extend(new_lines)
    path.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Main command-line interface
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check SQL Server schema")
    parser.add_argument("--autofix", action="store_true", help="Create missing tables/columns")
    parser.add_argument(
        "--update-constants",
        action="store_true",
        help="Update constants/schema.py with tables/columns found in the DB",
    )
    args = parser.parse_args(argv)

    required = load_required_schema()
    try:
        with connect() as conn:
            cursor = conn.cursor()
            existing = fetch_existing_schema(cursor)
    except Exception as exc:  # pragma: no cover - connection failures
        print(f"Could not connect to database: {exc}")
        return 1

    missing_tables: Dict[str, List[str]] = {}
    missing_cols: Dict[str, List[str]] = {}
    # Create a lowercased version of existing for case-insensitive comparison
    existing_lower = {k.lower(): [col.lower() for col in v] for k, v in existing.items()}
    for table, cols in required.items():
        table_lower = table.lower()
        if table_lower not in existing_lower:
            missing_tables[table] = cols
        else:
            missing = [c for c in cols if c.lower() not in existing_lower[table_lower]]
            if missing:
                missing_cols[table] = missing

    if missing_tables or missing_cols:
        print("Schema issues detected.")
        for table, cols in missing_tables.items():
            if table not in existing:
                sql = generate_create_table_sql(table, cols)
                print(f"\n-- Creating missing table: {table}\n{sql}")
                if args.autofix:
                    try:
                        cursor.execute(sql)
                        print(f"✅ Created table {table} with columns: {', '.join(cols)}")
                    except pyodbc.ProgrammingError as e:
                        print(f"❌ Could not create table {table}: {e}")

        for table, cols in missing_cols.items():
            print(f"\n-- Missing columns in {table}: {', '.join(cols)}")
            for col in cols:
                stmt = f"ALTER TABLE [{table}] ADD [{col}] NVARCHAR(MAX);"
                print(stmt)
                if args.autofix:
                    try:
                        cursor.execute(stmt)
                        print(f"✅ Added column [{col}] to [{table}]")
                    except pyodbc.ProgrammingError as e:
                        print(f"❌ Failed to add column [{col}] to [{table}]: {e}")

        if args.autofix:
            conn.commit()
            print("\n✅ Schema autofix completed. All changes committed.")

    else:
        print("Database schema is up to date.")

    if args.update_constants:
        to_add: Dict[str, List[str]] = {}
        for table, cols in existing.items():
            if table not in required:
                to_add[table] = cols
            else:
                extra = [c for c in cols if c not in required[table]]
                if extra:
                    to_add.setdefault(table, []).extend(extra)
        if to_add:
            update_constants_file(to_add)
            print("Updated constants/schema.py with missing entries.")
        else:
            print("No updates to constants/schema.py needed.")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
