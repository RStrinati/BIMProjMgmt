import json
import os
import pandas as pd
import pyodbc
import datetime
import re
import sqlparse
import time
import tkinter as tk
from tkinter import ttk, messagebox
from database import get_acc_folder_path, log_acc_import

UUID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)

LOG_FILE = "acc_import_summary.txt"
DRY_RUN = False  # Set to True for testing without SQL execution

def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def connect_to_db(server, db, user, pwd, driver="ODBC Driver 17 for SQL Server"):
    return pyodbc.connect(f"DRIVER={{{driver}}};SERVER={server};DATABASE={db};UID={user};PWD={pwd}")

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

def get_primary_keys(cursor, table_name):
    schema, tbl = table_name.split('.', 1)
    cursor.execute("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + QUOTENAME(CONSTRAINT_NAME)), 'IsPrimaryKey') = 1
        AND TABLE_SCHEMA = ? AND TABLE_NAME = ?
    """, schema, tbl)
    return [row[0] for row in cursor.fetchall()]

def log(message):
    timestamped = f"[{timestamp()}] {message}"
    print(timestamped)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(timestamped + "\n")

def convert_to_sql_compatible(val, col=None):
    if val is None or val == "": return None
    v = val.strip()

    # Special patch for the known DD/MM/YYYY HH:MM format in this dataset
    if re.match(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}$", v):
        try:
            return datetime.datetime.strptime(v, "%d/%m/%Y %H:%M")
        except ValueError:
            log(f"[WARN] Could not parse datetime '{v}' in column {col}")
            return None

    if col and col.lower() == "last_sign_in" and v.endswith(" UTC"):
        v = v.replace(" UTC", "")  # patch for '2023-05-11 11:56:56 UTC'

    if col and col.lower() == "phone" and v.startswith("{"):
        try:
            return json.loads(v)['number']
        except Exception:
            return None


    if v.lower() in ("t", "true"): return 1
    if v.lower() in ("f", "false"): return 0
    if v.isdigit(): return int(v)
    try: return float(v)
    except ValueError: pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try: return datetime.datetime.strptime(v, fmt)
        except ValueError: pass

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
        if sorted(df.columns) != sorted(db_cols):
            missing_in_csv = set(db_cols) - set(df.columns)
            extra_in_csv = set(df.columns) - set(db_cols)
            log(f"[ERROR] Column mismatch in {table_name}")
            log(f"Missing in CSV: {missing_in_csv}")
            log(f"Extra in CSV: {extra_in_csv}")
            raise ValueError(f"Column mismatch in {table_name}")

        pk_cols = get_primary_keys(cursor, table_name)
        null_pks = df[pk_cols].isnull().any(axis=1).sum()
        if null_pks > 0:
            log(f"[WARN] {null_pks} rows have NULLs in primary key columns for {table_name}")
            log(f"[DEBUG] Example rows with NULL PKs for {table_name}:")
            log(df[df[pk_cols].isnull().any(axis=1)].head(5).to_string())

        if truncate and not DRY_RUN:
            truncate_table(cursor, table_name)

        cols = ", ".join(f"[{col}]" for col in df.columns)
        placeholders = ", ".join("?" for _ in df.columns)
        sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"

        valid_rows = skipped_rows = error_rows = 0
        params = []
        for index, row in df.iterrows():
            try:
                if 'status' in row and row['status'].strip().lower() == 'deleted':
                    skipped_rows += 1
                    continue
                converted = tuple(convert_to_sql_compatible(row[col], col) for col in df.columns)
                params.append(converted)
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

def import_acc_data(folder_path, server, db, user, pwd, merge_dir="sql"):
    summary = []
    with open(LOG_FILE, "w"): pass  # clear log file

    conn = connect_to_db(server, db, user, pwd)
    cursor = conn.cursor()
    cursor.fast_executemany = True

    all_files = sorted(f.replace(".csv", "") for f in os.listdir(folder_path) if f.endswith(".csv"))
    processed = set()

    for base in all_files:
        if base in processed:
            continue
        processed.add(base)

        csv_file = os.path.join(folder_path, f"{base}.csv")
        merge_sql_file = f"merge_{base}.sql"
        table_name = f"staging.{base}"

        if os.path.exists(csv_file) and os.path.exists(os.path.join(merge_dir, merge_sql_file)):
            start = time.time()
            result = import_csv_to_sql(cursor, conn, csv_file, table_name)
            if result:
                summary.append(result)
                run_merge_script(cursor, conn, merge_sql_file, merge_dir=merge_dir)
            log(f"[DONE] Processed {base} in {round(time.time() - start, 2)}s")
        else:
            log(f"[SKIP] {base}: missing CSV or merge SQL")

    cursor.close()
    conn.close()
    return summary


def run_acc_import(project_dropdown, acc_folder_entry, acc_summary_listbox):
    selected = project_dropdown.get()
    if " - " not in selected:
        return False, "Select a valid project."

    project_id = selected.split(" - ")[0]
    folder_path = acc_folder_entry.get().strip()

    if not os.path.exists(folder_path):
        return False, "Folder path is invalid."

    folder_name = os.path.basename(folder_path.rstrip(os.sep))
    confirm = messagebox.askyesno(
        "Confirm Import",
        f"Import ACC data from '{folder_name}'?",
    )
    if not confirm:
        return False, "Import canceled."

    progress_win = tk.Toplevel()
    progress_win.title("Importing ACC Data")
    progress_win.transient(acc_folder_entry.winfo_toplevel())
    progress_win.grab_set()
    lbl_status = ttk.Label(progress_win, text=f"Importing '{folder_name}'...")
    lbl_status.pack(padx=20, pady=(20, 10))
    pb = ttk.Progressbar(progress_win, mode="indeterminate")
    pb.pack(padx=20, pady=(0, 20))
    pb.start()
    progress_win.update()

    summary = import_acc_data(
        folder_path,
        "P-NB-USER-028\\SQLEXPRESS",
        "acc_data_schema",
        "admin02",
        "1234",
    )

    pb.stop()
    lbl_status.config(text="Import complete")
    progress_win.update()
    time.sleep(0.5)
    progress_win.destroy()

    if not summary:
        return False, "ACC import failed or found no data."

    summary_text = f"✅ Imported: {os.path.basename(folder_path)}\n"
    for stat in summary:
        summary_text += (
            f"{stat['table']} — Total: {stat['rows_total']}, "
            f"Valid: {stat['rows_valid']}, "
            f"Skipped: {stat['rows_skipped']}, "
            f"Errors: {stat['rows_errors']}\n"
        )

    log_acc_import(project_id, os.path.basename(folder_path), summary_text)

    acc_summary_listbox.delete(0, "end")
    for line in summary_text.strip().split("\n"):
        acc_summary_listbox.insert("end", line)

    return True, "ACC data imported successfully."
