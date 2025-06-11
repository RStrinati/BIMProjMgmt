import pyodbc
import os
import pandas as pd 
from datetime import datetime, timedelta

def connect_to_db(db_name="ProjectManagement"):
    """Connect to the specified SQL Server database."""
    try:
        connection = pyodbc.connect(
            f"Driver={{SQL Server}};"
            f"Server=P-NB-USER-028\\SQLEXPRESS;"
            f"Database={db_name};"
            f"Trusted_Connection=yes;"
        )
        return connection
    except pyodbc.Error as e:
        print(f"❌ Database connection error ({db_name}): {e}")
        return None
    
def insert_project(project_name, folder_path, ifc_folder_path=None):
    """Insert a new project into the database with an optional IFC folder path."""
    conn = connect_to_db()
    if conn is None:
        print("❌ Database connection failed.")
        return False

    try:
        cursor = conn.cursor()
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')

        cursor.execute("""
            INSERT INTO projects (project_name, folder_path, ifc_folder_path, start_date, end_date)
            VALUES (?, ?, ?, ?, ?);
        """, (project_name, folder_path, ifc_folder_path, start_date, end_date))

        conn.commit()
        print(f"✅ Project '{project_name}' inserted with IFC folder: {ifc_folder_path}")
        return True
    except pyodbc.Error as e:
        print(f"❌ Database Error: {e}")
        return False
    finally:
        conn.close()

def get_projects():
    """Fetch available projects."""
    conn = connect_to_db()
    if conn is None:
        return []  # Return empty list if connection fails
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT project_id, project_name FROM projects ORDER BY project_id;")
        projects = [(row[0], row[1]) for row in cursor.fetchall()]
        return projects
    except Exception as e:
        print(f"❌ Error fetching projects: {str(e)}")
        return []
    finally:
        conn.close()

def get_project_details(project_id):
    """Fetch project details from the database (excluding folder paths)."""
    conn = connect_to_db("ProjectManagement")  
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT project_name, start_date, end_date, status, priority
            FROM dbo.projects 
            WHERE project_id = ?;
        """, (project_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                "project_name": row[0],
                "start_date": row[1].strftime('%Y-%m-%d') if row[1] else "",
                "end_date": row[2].strftime('%Y-%m-%d') if row[2] else "",
                "status": row[3],
                "priority": row[4]
            }
        else:
            return None
    except Exception as e:
        print(f"❌ Error fetching project details: {str(e)}")
        return None
    finally:
        conn.close()

def update_project_details(project_id, start_date, end_date, status, priority):
    """Update project start date, end date, status, and priority."""
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        print("❌ Database connection failed.")
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE dbo.projects 
            SET start_date = ?, end_date = ?, status = ?, priority = ?, updated_at = GETDATE()
            WHERE project_id = ?;
        """, (start_date, end_date, status, priority, project_id))
        conn.commit()
        print(f"✅ Project {project_id} details updated.")
        return True
    except Exception as e:
        print(f"❌ Database Error updating project details: {e}")
        return False
    finally:
        conn.close()

def get_review_schedule(project_id, cycle_id):
    """Fetch review schedule including project name and cycle ID from the database."""
    conn = connect_to_db()
    if conn is None:
        return pd.DataFrame(), "", ""

    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT rs.schedule_id, rs.review_date, rs.cycle_id, p.project_name
            FROM ReviewSchedule rs
            JOIN Projects p ON rs.project_id = p.project_id
            WHERE rs.project_id = ? AND rs.cycle_id = ?
            ORDER BY rs.review_date ASC;
        """, (project_id, cycle_id))

        result = cursor.fetchall()

        # ✅ Debugging: Print raw SQL query result
        print(f"🔹 Raw SQL Query Result: {result}")

        if not result:
            print(f"⚠️ No review schedule data found for Project {project_id}, Cycle {cycle_id}")
            return pd.DataFrame(columns=["schedule_id", "review_date", "cycle_id", "project_name"]), "", ""

        # ✅ Convert query result into a Pandas DataFrame
        structured_result = [tuple(row) for row in result]
        df = pd.DataFrame(structured_result, columns=["schedule_id", "review_date", "cycle_id", "project_name"])
        df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")  # ✅ Ensure proper date format

        project_name = df["project_name"].iloc[0] if not df.empty else "Unknown Project"
        cycle_id = df["cycle_id"].iloc[0] if not df.empty else "Unknown Cycle"

        # ✅ Debugging: Print DataFrame structure
        print(f"🔹 DataFrame Shape: {df.shape}")
        print(f"🔹 DataFrame Preview:\n{df.head()}")

        return df, project_name, cycle_id
    except Exception as e:
        print(f"❌ Error fetching review schedule: {str(e)}")
        return pd.DataFrame(), "", ""
    finally:
        conn.close()


def update_project_folders(project_id, models_path=None, data_path=None, ifc_path=None):
    """Update standard (models), data export, and IFC folder paths in dbo.projects."""
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        print("❌ Database connection failed.")
        return False

    try:
        cursor = conn.cursor()

        if models_path is not None:
            cursor.execute("UPDATE dbo.projects SET folder_path = ? WHERE project_id = ?", (models_path, project_id))

        if data_path is not None:
            cursor.execute("UPDATE dbo.projects SET data_export_folder = ? WHERE project_id = ?", (data_path, project_id))

        if ifc_path is not None:
            cursor.execute("UPDATE dbo.projects SET ifc_folder_path = ? WHERE project_id = ?", (ifc_path, project_id))

        conn.commit()
        print(f"✅ Project {project_id} paths updated: models={models_path}, data={data_path}, ifc={ifc_path}")
        return True

    except Exception as e:
        print(f"❌ Database Error updating project folders: {e}")
        return False

    finally:
        conn.close()




def get_acc_import_logs(project_id):
    conn = connect_to_db()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 5 folder_name, import_date, summary
            FROM ACCImportLogs
            WHERE project_id = ?
            ORDER BY import_date DESC
        """, (project_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error retrieving import logs: {e}")
        return []
    finally:
        conn.close()


def get_recent_files():
    """Fetch the latest 1000 records from the view qry_SharedFolderValidation."""
    conn = connect_to_db()  # ✅ Use the shared connection function
    if conn is None:
        print("❌ Error: Could not connect to the database.")
        return []

    try:
        cursor = conn.cursor()

        query = """
            SELECT TOP (1000)
                [project_id],
                [file_name],
                [date_modified],
                [level_10_folder],
                [is_recent]  -- ✅ Make sure this column exists in the SQL View
            FROM dbo.qry_SharedFolderValidation
            ORDER BY date_modified DESC;
        """

        cursor.execute(query)
        results = cursor.fetchall()

        # ✅ Convert results into a list of tuples
        return [(row.level_10_folder, row.file_name, row.date_modified, row.is_recent) for row in results]

    except pyodbc.Error as e:
        print(f"❌ Error fetching recent files: {e}")
        return []
    
    finally:
        conn.close()  # ✅ Ensure connection is always closed

def get_project_folders(project_id):
    """Fetch both the standard and IFC folder paths for a given project from dbo.projects."""
    conn = connect_to_db("ProjectManagement")  # ✅ Ensure it queries the correct DB
    if conn is None:
        print("❌ Database connection failed.")
        return None, None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT folder_path, ifc_folder_path FROM dbo.projects WHERE project_id = ?", (project_id,))
        row = cursor.fetchone()
        
        if row:
            print(f"✅ Retrieved from DB: Folder Path={row[0]}, IFC Folder Path={row[1]}")
            return row[0], row[1]  # (folder_path, ifc_folder_path)
        else:
            print(f"⚠️ No matching project found for ID: {project_id}")
            return None, None
    except Exception as e:
        print(f"❌ Error fetching project folders: {str(e)}")
        return None, None
    finally:
        conn.close()



def get_cycle_ids(project_id):
    """Fetch available cycle IDs for a given project."""
    conn = connect_to_db()
    if conn is None:
        return ["No Cycles Available"]

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT cycle_id FROM ReviewParameters 
            WHERE ProjectID = ? 
            ORDER BY cycle_id DESC;
        """, (project_id,))
        
        cycles = [str(row[0]) for row in cursor.fetchall()]
        
        print(f"🔹 Querying Cycle IDs for Project {project_id}")
        print(f"🔹 SQL Query Result: {cycles}")

        return cycles if cycles else ["No Cycles Available"]
    except Exception as e:
        print(f"❌ Error fetching cycle IDs: {str(e)}")
        return ["No Cycles Available"]
    finally:
        conn.close()

def fetch_data(query):
    conn = connect_to_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        return data
    finally:
        conn.close()


def insert_files_into_tblACCDocs(project_id, folder_path):
    """
    Extracts files from the given folder and replaces only the records for the selected project in tblACCDocs.

    :param project_id: The project ID associated with the files.
    :param folder_path: The folder path containing the files.
    """
    conn = connect_to_db()
    if conn is None:
        print("❌ Database connection failed.")
        return False

    try:
        cursor = conn.cursor()

        # ✅ DELETE only files related to the selected project
        cursor.execute("DELETE FROM tblACCDocs WHERE project_id = ?", (project_id,))
        rows_deleted = cursor.rowcount
        conn.commit()
        print(f"🗑️ {rows_deleted} existing records deleted for project {project_id} from tblACCDocs.")

        # Extract file metadata
        file_details = []

        try:
            for root, _, files in os.walk(folder_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    date_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                    file_type = os.path.splitext(file_name)[1][1:] if os.path.splitext(file_name)[1] else "Unknown"
                    file_size_kb = round(os.path.getsize(file_path) / 1024, 2)
                    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  

                    file_details.append((file_name, file_path, date_modified, file_type, file_size_kb, created_at, None, project_id))
        except Exception as e:
            print(f"❌ Error accessing folder: {e}")
            return False

        # ✅ Print file details for debugging
        if not file_details:
            print("⚠️ No files found in the folder.")
            return False
        else:
            print(f"📁 Found {len(file_details)} files. Preparing to insert...")
            print("📂 Files to be inserted:")
            for file_detail in file_details[:5]:
                print(file_detail)  # Display the first 5 files for verification

        # ✅ Insert new records only for the selected project
        try:
            cursor.executemany("""
                INSERT INTO tblACCDocs 
                (file_name, file_path, date_modified, file_type, file_size_kb, created_at, deleted_at, project_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, file_details)

            rows_inserted = cursor.rowcount
            conn.commit()
            print(f"✅ {rows_inserted} files inserted into tblACCDocs for project {project_id}.")
            return True
        except pyodbc.Error as e:
            print(f"❌ Database Error during insertion: {e}")
            conn.rollback()  # Rollback if insertion fails
            return False

    finally:
        conn.close()

def store_file_details_in_db(file_details):
    """
    Store file details in the database.
    :param file_details: List of tuples (file_name, file_path, date_modified, file_type, file_size_kb)
    """
    conn = connect_to_db()
    if conn is None:
        print("❌ Error: Could not connect to the database.")
        return

    try:
        cursor = conn.cursor()

        # Clear existing records (optional: use `TRUNCATE TABLE` if necessary)
        cursor.execute("DELETE FROM dbo.tblACCDocs")
        conn.commit()

        # Insert new data
        cursor.executemany("""
            INSERT INTO dbo.tblACCDocs (file_name, file_path, date_modified, file_type, file_size_kb)
            VALUES (?, ?, ?, ?, ?)
        """, file_details)

        conn.commit()
        print("✅ File details successfully stored in the database.")

    except Exception as e:
        print(f"❌ Error storing file details in the database: {e}")
        conn.rollback()

    finally:
        conn.close()

def get_last_export_date():
    """Retrieve the most recent export date from tblIFCData in RevitHealthCheckDB."""
    conn = connect_to_db("RevitHealthCheckDB")  # ✅ Connect to the correct DB
    if conn is None:
        return "No exports found"

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 1 date_exported FROM dbo.tblIFCData 
            ORDER BY date_exported DESC;
        """)
        row = cursor.fetchone()
        
        if row:
            return row[0]  # Return the latest date
        else:
            return "No exports found"
    
    except Exception as e:
        print(f"❌ Error fetching last export date: {e}")
        return "Error fetching data"
    
    finally:
        conn.close()

def save_acc_folder_path(project_id, folder_path):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""
        MERGE INTO ACCImportFolders AS target
        USING (SELECT ? AS project_id, ? AS acc_folder_path) AS source
        ON target.project_id = source.project_id
        WHEN MATCHED THEN UPDATE SET acc_folder_path = source.acc_folder_path
        WHEN NOT MATCHED THEN INSERT (project_id, acc_folder_path) VALUES (source.project_id, source.acc_folder_path);
    """, (project_id, folder_path))
    conn.commit()
    conn.close()

def get_acc_folder_path(project_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT acc_folder_path FROM ACCImportFolders WHERE project_id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def log_acc_import(project_id, folder_name, summary):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ACCImportLogs (project_id, folder_name, import_date, summary)
        VALUES (?, ?, GETDATE(), ?)
    """, (project_id, folder_name, summary))
    conn.commit()
    conn.close()

 
# Control file management ===========================================

def get_project_health_files(project_id):
    """Return distinct Revit file names from vw_LatestRvtFiles for a project."""
    conn = connect_to_db("RevitHealthCheckDB")
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT strRvtFileName
            FROM dbo.vw_LatestRvtFiles
            WHERE project_id = ?
            ORDER BY strRvtFileName;
        """, (project_id,))
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching health files: {e}")
        return []
    finally:
        conn.close()


def get_control_file(project_id):
    """Retrieve the saved control file for the given project."""
    conn = connect_to_db()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.project_name, cm.control_file_name
            FROM ProjectManagement.dbo.tblControlModels cm
            JOIN ProjectManagement.dbo.projects p ON cm.project_id = p.project_id
            WHERE cm.project_id = ?
        """, (project_id,))

        row = cursor.fetchone()
        return row[1] if row else None
    except Exception as e:
        print(f"❌ Error fetching control file: {e}")
        return None
    finally:
        conn.close()


def set_control_file(project_id, file_name):
    """Save or update the selected control file for the project."""
    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            MERGE dbo.tblControlModels AS target
            USING (SELECT ? AS project_id, ? AS control_file_name) AS src
            ON target.project_id = src.project_id
            WHEN MATCHED THEN 
                UPDATE SET control_file_name = src.control_file_name, updated_at = GETDATE()
            WHEN NOT MATCHED THEN 
                INSERT (project_id, control_file_name)
                VALUES (src.project_id, src.control_file_name);
        """, (project_id, file_name))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error saving control file: {e}")
        return False
    finally:
        conn.close()

def update_file_validation_status(file_name, status, reason, regex_used):
    """
    Updates validation status for a given Revit file in tblRvtProjHealth.
    """
    conn_str = os.getenv("DB_CONNECTION_STRING")  # or use your hardcoded string if not using env vars

    query = """
    UPDATE RevitHealthCheckDB.dbo.tblRvtProjHealth
    SET
        validation_status = ?,
        validation_reason = ?,
        compiled_regex = ?,
        validated_date = ?
    WHERE strRvtFileName = ?
    """

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute(query, status, reason, regex_used, datetime.now(), file_name)
            conn.commit()
    except Exception as e:
        print(f"❌ Failed to update validation for {file_name}: {e}")
