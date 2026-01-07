import json
import os
import pandas as pd
import datetime
import re
import sqlparse
import time
import zipfile
import tempfile
import shutil
import logging
from database import get_acc_folder_path, log_acc_import, connect_to_db

from config import Config
ACC_DB = Config.ACC_DB

UUID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)

LOG_FILE = "acc_import_summary.txt"
logger = logging.getLogger(__name__)
DRY_RUN = False  # Set to True for testing without SQL execution

def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def truncate_table(cursor, table_name):
    try:
        cursor.execute(f"TRUNCATE TABLE {table_name}")
    except Exception as e:
        log(f"[WARN] Could not truncate {table_name}: {e}")

def get_table_columns(cursor, table_name):
    schema, tbl = table_name.split('.', 1)
    cursor.execute("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """, schema, tbl)
    return [row[0] for row in cursor.fetchall()]

def get_column_metadata(cursor, table_name):
    """Return dict of column metadata keyed by column name."""
    schema, tbl = table_name.split('.', 1)
    cursor.execute("""
        SELECT COLUMN_NAME, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
    """, schema, tbl)
    meta = {}
    for row in cursor.fetchall():
        meta[row[0]] = {
            "is_nullable": row[1] == "YES",
            "has_default": row[2] is not None,
        }
    return meta

def get_primary_keys(cursor, table_name):
    schema, tbl = table_name.split('.', 1)
    cursor.execute("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + QUOTENAME(CONSTRAINT_NAME)), 'IsPrimaryKey') = 1
        AND TABLE_SCHEMA = ? AND TABLE_NAME = ?
    """, schema, tbl)
    return [row[0] for row in cursor.fetchall()]

def get_column_sizes(cursor, table_name):
    """Return a dict mapping column names to CHARACTER_MAXIMUM_LENGTH."""
    schema, tbl = table_name.split('.', 1)
    cursor.execute("""
        SELECT COLUMN_NAME, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
    """, schema, tbl)
    return {row[0]: row[1] for row in cursor.fetchall()}

def log(message):
    """Log to standard logger and persist to the ACC summary file with a timestamp."""
    logger.info(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp()}] {message}\n")
        
def parse_excel_like_time(val):
    # Try Excel-style time parsing (e.g. "32:21.0" = 32 minutes 21 seconds)
    try:
        minutes, seconds = val.strip().split(":")
        seconds = float(seconds)
        base = datetime.datetime(2000, 1, 1)
        return base + datetime.timedelta(minutes=int(minutes), seconds=seconds)
    except Exception:
        return None

def parse_custom_datetime(val, col_name):
    val = val.strip()

    # Accept known good formats
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.datetime.strptime(val, fmt)
        except ValueError:
            continue

    # Handle odd time-only formats like "32:21.0"
    if re.match(r"^\d{1,2}:\d{2}(\.\d+)?$", val):
        try:
            minutes, rest = val.split(":")
            seconds = float(rest)
            base = datetime.datetime(2000, 1, 1)
            return base + datetime.timedelta(minutes=int(minutes), seconds=seconds)
        except Exception:
            log(f"[WARN] Could not parse weird time '{val}' in column {col_name}")
            return None

    # As last resort: log it
    log(f"[WARN] Unrecognized datetime format '{val}' in column {col_name}")
    return None

def convert_to_sql_compatible(val, col=None):
    if val is None or val == "":
        return None
    v = val.strip()

    # Special patch for the known DD/MM/YYYY HH:MM format in this dataset
    if re.match(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}$", v):
        try:
            return datetime.datetime.strptime(v, "%d/%m/%Y %H:%M")
        except ValueError:
            log(f"[WARN] Invalid datetime format '{v}' in column {col}. Using fallback.")
            return None

    if col and col.lower() == "last_sign_in" and v.endswith(" UTC"):
        v = v.replace(" UTC", "")  # patch for '2023-05-11 11:56:56 UTC'

    if col and col.lower() == "phone" and v.startswith("{"):
        try:
            return json.loads(v)['number']
        except Exception:
            return None


    if v.lower() in ("t", "true"):
        return 1
    if v.lower() in ("f", "false"):
        return 0
    if v.isdigit():
        return int(v)
    try:
        return float(v)
    except ValueError:
        pass
    
    if col and col.lower() in ("created_at", "updated_at"):
        result = parse_custom_datetime(v, col)
        if result is not None:
            return result

        result = parse_excel_like_time(v)
        if result is not None:
            return result


    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%H:%M:%S"):
        try:
            return datetime.datetime.strptime(v, fmt)
        except ValueError:
            pass


    return v  # Fallback for nvarchar fields


def import_csv_to_sql(cursor, conn, file_path, table_name, truncate=True):
    log(f"Importing {file_path} → {table_name} ...")
    schema, tbl = table_name.split('.', 1)
    cursor.execute("SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?", schema, tbl)
    if not cursor.fetchone():
        log(f"[SKIP] No such table: {table_name}")
        return None

    try:
        df = pd.read_csv(file_path, dtype=str).fillna("")
        db_cols = get_table_columns(cursor, table_name)
        col_meta = get_column_metadata(cursor, table_name)
        missing_in_csv = set(db_cols) - set(df.columns)
        extra_in_csv = set(df.columns) - set(db_cols)
        if extra_in_csv:
            log(f"[ERROR] Column mismatch in {table_name}")
            log(f"Extra in CSV: {extra_in_csv}")
            raise ValueError(f"Column mismatch in {table_name}")
        if missing_in_csv:
            required_missing = [
                col for col in missing_in_csv
                if col_meta.get(col, {}).get("is_nullable") is False
                and col_meta.get(col, {}).get("has_default") is False
            ]
            if required_missing:
                log(f"[ERROR] Column mismatch in {table_name}")
                log(f"Missing required in CSV: {required_missing}")
                raise ValueError(f"Column mismatch in {table_name}")
            log(f"[INFO] CSV missing optional/defaulted columns in {table_name}: {sorted(missing_in_csv)}")

        pk_cols = get_primary_keys(cursor, table_name)
        missing_pk_cols = [col for col in pk_cols if col not in df.columns]
        if missing_pk_cols:
            log(f"[ERROR] CSV missing primary key columns for {table_name}: {missing_pk_cols}")
            raise ValueError(f"Missing PK columns in {table_name}")
        null_pks = df[pk_cols].isnull().any(axis=1).sum()
        if null_pks > 0:
            log(f"[WARN] {null_pks} rows have NULLs in primary key columns for {table_name}")
            log(f"[DEBUG] Example rows with NULL PKs for {table_name}:")
            log(df[df[pk_cols].isnull().any(axis=1)].head(5).to_string())

        if truncate and not DRY_RUN:
            truncate_table(cursor, table_name)

        col_sizes = get_column_sizes(cursor, table_name)

        cols = ", ".join(f"[{col}]" for col in df.columns)
        placeholders = ", ".join("?" for _ in df.columns)
        sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"

        valid_rows = skipped_rows = error_rows = 0
        params = []
        for index, row in df.iterrows():
            try:
                converted_row = []
                for col in df.columns:
                    val = convert_to_sql_compatible(row[col], col)
                    max_len = col_sizes.get(col)
                    if isinstance(val, str) and max_len and max_len > 0 and len(val) > max_len:
                        log(f"[WARN] Truncating {table_name}.{col} to {max_len} chars")
                        val = val[:max_len]
                    converted_row.append(val)

                params.append(tuple(converted_row))
                valid_rows += 1
            except Exception as e:
                log(f"[ROW ERROR] Row {index} in {table_name}: {e}")
                log(row.to_string())
                error_rows += 1

        if params:
            log(f"[DEBUG] First insert into {table_name}: {params[0]}")

        if params and not DRY_RUN:
            cursor.executemany(sql, params)
            conn.commit()

        return {
            "table": table_name,
            "file": os.path.basename(file_path),
            "rows_total": len(df),
            "rows_valid": valid_rows,
            "rows_skipped": skipped_rows,
            "rows_errors": error_rows,
        }
    except Exception as e:
        log(f"[FAIL] {file_path} import failed: {e}")
        return {
            "table": table_name,
            "file": os.path.basename(file_path),
            "rows_total": 0,
            "rows_valid": 0,
            "rows_skipped": 0,
            "rows_errors": 1
        }

def run_merge_script(cursor, conn, script_filename, merge_dir="sql"):
    script_path = os.path.join(merge_dir, script_filename)
    if not os.path.exists(script_path):
        log(f"[WARN] Merge script missing: {script_path}")
        return
    with open(script_path, "r", encoding="utf-8") as f:
        merge_sql = f.read()
    for stmt in sqlparse.split(merge_sql):
        if stmt.strip():
            try:
                if not DRY_RUN:
                    cursor.execute(stmt)
            except Exception as e:
                log(f"[SQL ERROR] in {script_filename}: {e}\n{stmt}")
    if not DRY_RUN:
        conn.commit()

def import_acc_data(folder_path, db=None, merge_dir="sql", show_skip_summary=True):
    """Import ACC CSV data and merge into SQL tables."""
    summary = []
    skipped = []

    # Clear previous log file contents
    with open(LOG_FILE, "w"):
        pass

    # Resolve merge_dir to absolute path if it's relative
    # This ensures the path works regardless of current working directory
    if not os.path.isabs(merge_dir):
        # handlers/acc_handler.py is one level down from project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        merge_dir = os.path.join(project_root, merge_dir)

    temp_dir = None

    # Handle zipped exports
    if os.path.isfile(folder_path) and folder_path.lower().endswith(".zip"):
        temp_dir = tempfile.mkdtemp()
        try:
            with zipfile.ZipFile(folder_path, "r") as zf:
                zf.extractall(temp_dir)
            folder_path = temp_dir
        except Exception:
            shutil.rmtree(temp_dir)
            raise

    elif os.path.isdir(folder_path):
        zip_files = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.lower().endswith(".zip")
        ]
        if zip_files:
            latest_zip = max(zip_files, key=os.path.getmtime)
            log(f"[INFO] Extracting {os.path.basename(latest_zip)}")
            temp_dir = tempfile.mkdtemp(prefix="acc_")
            with zipfile.ZipFile(latest_zip, "r") as zf:
                zf.extractall(temp_dir)
            folder_path = temp_dir

    # Use default DB from config if not provided
    if db is None:
        db = ACC_DB

    from database_pool import get_db_connection
    
    with get_db_connection(db) as conn:
        cursor = conn.cursor()
        cursor.fast_executemany = True

        csv_bases = {f.replace(".csv", "") for f in os.listdir(folder_path) if f.endswith(".csv")}
        sql_bases = {
            f.replace("merge_", "").replace(".sql", "")
            for f in os.listdir(merge_dir)
            if f.startswith("merge_") and f.endswith(".sql")
        }
        all_bases = sorted(csv_bases | sql_bases)

        for base in all_bases:
            csv_file = os.path.join(folder_path, f"{base}.csv")
            merge_sql_file = f"merge_{base}.sql"
            merge_sql_path = os.path.join(merge_dir, merge_sql_file)
            table_name = f"staging.{base}"

            csv_exists = os.path.exists(csv_file)
            merge_exists = os.path.exists(merge_sql_path)

            if csv_exists and merge_exists:
                start = time.time()
                result = import_csv_to_sql(cursor, conn, csv_file, table_name)
                if result:
                    summary.append(result)
                    run_merge_script(cursor, conn, merge_sql_file, merge_dir=merge_dir)
                log(f"[DONE] Processed {base} in {round(time.time() - start, 2)}s")
            else:
                missing = []
                if not csv_exists:
                    missing.append("CSV")
                if not merge_exists:
                    missing.append("merge SQL")
                reason = " and ".join(missing)
                log(f"[SKIP] {base}: missing {reason}")
                skipped.append((base, reason))

        if show_skip_summary and skipped:
            log("Skipped table summary:")
            for base, reason in skipped:
                log(f" - {base}: missing {reason}")

    if temp_dir:
        shutil.rmtree(temp_dir)

    return summary
