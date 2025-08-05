#!/usr/bin/env python3
"""
Verify that all constants in schema.py match the actual SQL Server schema.
Reports missing or extra tables/columns.

Usage:
    python verify_schema.py
"""
import pyodbc
import inspect
from config import Config
from constants import schema as S

def connect():
    """Connect to SQL Server."""
    conn_str = (
        f"DRIVER={{{Config.DB_DRIVER}}};"
        f"SERVER={Config.DB_SERVER};"
        f"DATABASE={Config.PROJECT_MGMT_DB};"
        f"UID={Config.DB_USER};"
        f"PWD={Config.DB_PASSWORD}"
    )
    return pyodbc.connect(conn_str)

def fetch_existing_schema(cursor):
    """Return mapping of tables -> list of columns from DB."""
    existing = {}
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
    for row in cursor.fetchall():
        table = row.TABLE_NAME
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?", table)
        existing[table] = [r.COLUMN_NAME for r in cursor.fetchall()]
    return existing

def load_schema_from_constants():
    """Return mapping of table -> columns defined in schema.py."""
    tables = {}
    for name, obj in inspect.getmembers(S):
        if inspect.isclass(obj) and hasattr(obj, "TABLE"):
            table = getattr(obj, "TABLE")
            cols = [v for k, v in obj.__dict__.items() if k.isupper() and k != "TABLE"]
            tables[table] = cols
    return tables

def verify_schema():
    conn = connect()
    cursor = conn.cursor()

    db_schema = fetch_existing_schema(cursor)
    const_schema = load_schema_from_constants()

    print("🔍 **Schema Verification Report**")
    print("=" * 40)

    # Check missing tables
    for table in const_schema:
        if table not in db_schema:
            print(f"❌ Missing table in DB: {table}")
        else:
            db_cols = set(col.lower() for col in db_schema[table])
            const_cols = set(col.lower() for col in const_schema[table])

            missing_cols = const_cols - db_cols
            extra_cols = db_cols - const_cols

            if missing_cols:
                print(f"  ❌ Missing columns in {table}: {', '.join(missing_cols)}")
            if extra_cols:
                print(f"  ⚠ Extra columns in DB (not in schema.py) for {table}: {', '.join(extra_cols)}")

    # Check tables in DB but not in schema.py
    for table in db_schema:
        if table not in const_schema:
            print(f"⚠ Table in DB but not in schema.py: {table}")

    print("=" * 40)
    print("✅ Verification complete.")

if __name__ == "__main__":
    verify_schema()
