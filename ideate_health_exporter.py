import os
import pandas as pd
import pyodbc

def assess_health_check(file_path, control_model_name=None):
    # Insert function from earlier here (same logic as shared)
    ...

def export_health_checks_to_sql(folder_path, project_id, table_name, control_model_table="ProjectControlModels"):
    from database import connect_to_db, get_control_file
    summaries = []
    control_model = get_control_file(project_id)

    conn = connect_to_db("ProjectManagement")
    if not conn:
        print("❌ Failed to connect to DB")
        return []

    for file in os.listdir(folder_path):
        if not file.endswith(".xlsx") or file.startswith("~$"):
            continue
        full_path = os.path.join(folder_path, file)
        summary = assess_health_check(full_path, control_model)
        summaries.append(summary)

    df = pd.DataFrame(summaries)

    cursor = conn.cursor()
    for _, row in df.iterrows():
        columns = ', '.join(row.index)
        placeholders = ', '.join(['?'] * len(row))
        cursor.execute(
            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
            *row.fillna("").tolist()
        )
    conn.commit()
    conn.close()

    return df

