import os
import pandas as pd

def assess_health_check(file_path, control_model_name=None):
    """Analyze a single Ideate Health Check Excel file.

    This repository does not yet provide the implementation for parsing the
    exported workbook, so this function raises ``NotImplementedError`` to make
    the missing logic explicit at runtime.
    """
    raise NotImplementedError("Ideate Health Check parsing not implemented")

def export_health_checks_to_sql(folder_path, project_id, table_name, control_model_table="ProjectControlModels"):
    from database_pool import get_db_connection
    from database import get_control_file
    summaries = []
    control_model = get_control_file(project_id)

    try:
        with get_db_connection("ProjectManagement") as conn:
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

            return df
    except Exception as e:
        print(f"❌ Error exporting health checks: {e}")
        return []

