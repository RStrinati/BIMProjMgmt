import pyodbc
import os
import pandas as pd 
from datetime import datetime, timedelta

from config import Config

def connect_to_db(db_name=None):
    """Connect to the specified SQL Server database using environment settings."""
    try:
        driver = Config.DB_DRIVER
        server = Config.DB_SERVER
        user = Config.DB_USER
        password = Config.DB_PASSWORD
        database = db_name if db_name else Config.PROJECT_MGMT_DB

        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"UID={user};"
            f"PWD={password};"
            f"DATABASE={database};"
            "TrustServerCertificate=yes;"
        )

        connection = pyodbc.connect(conn_str)
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
        
        cursor.execute(
            """
            SELECT rs.schedule_id,
                   rs.review_date,
                   rs.cycle_id,
                   p.project_name,
                   d.construction_stage,
                   d.proposed_fee,
                   d.assigned_users,
                   d.reviews_per_phase,
                   d.planned_start_date,
                   d.planned_completion_date,
                   d.actual_start_date,
                   d.actual_completion_date,
                   d.hold_date,
                   d.resume_date,
                   d.new_contract
            FROM ReviewSchedule rs
            JOIN Projects p ON rs.project_id = p.project_id
            LEFT JOIN ReviewCycleDetails d ON rs.project_id = d.project_id AND rs.cycle_id = d.cycle_id
            WHERE rs.project_id = ? AND rs.cycle_id = ?
            ORDER BY rs.review_date ASC;
        """,
            (project_id, cycle_id),
        )

        result = cursor.fetchall()

        # ✅ Debugging: Print raw SQL query result
        print(f"🔹 Raw SQL Query Result: {result}")

        if not result:
            print(f"⚠️ No review schedule data found for Project {project_id}, Cycle {cycle_id}")
            return pd.DataFrame(columns=["schedule_id", "review_date", "cycle_id", "project_name"]), "", ""

        # ✅ Convert query result into a Pandas DataFrame
        structured_result = [tuple(row) for row in result]
        df = pd.DataFrame(
            structured_result,
            columns=[
                "schedule_id",
                "review_date",
                "cycle_id",
                "project_name",
                "construction_stage",
                "proposed_fee",
                "assigned_users",
                "reviews_per_phase",
                "planned_start_date",
                "planned_completion_date",
                "actual_start_date",
                "actual_completion_date",
                "hold_date",
                "resume_date",
                "new_contract",
            ],
        )
        df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
        for col in [
            "planned_start_date",
            "planned_completion_date",
            "actual_start_date",
            "actual_completion_date",
            "hold_date",
            "resume_date",
        ]:
            df[col] = pd.to_datetime(df[col], errors="coerce")

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

def update_file_validation_status(file_name, status, reason, regex_used,
                                  failed_field=None, failed_value=None, failed_reason=None, discipline=None, discipline_full=None):
    # Convert everything to string if not None
    file_name = str(file_name) if file_name is not None else ""
    status = str(status) if status is not None else ""
    reason = str(reason) if reason is not None else ""
    regex_used = str(regex_used) if regex_used is not None else ""
    failed_field = str(failed_field) if failed_field is not None else None
    failed_value = str(failed_value) if failed_value is not None else None
    failed_reason = str(failed_reason) if failed_reason is not None else None
    discipline = str(discipline) if discipline is not None else None
    discipline_full = str(discipline_full) if discipline_full is not None else None

    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE RevitHealthCheckDB.dbo.tblRvtProjHealth
            SET validation_status = ?, 
                validation_reason = ?, 
                compiled_regex = ?, 
                validated_date = GETDATE(),
                failed_field_name = ?, 
                failed_field_value = ?, 
                failed_field_reason = ?,
                discipline_code = ?,         
                discipline_full_name = ?  
            WHERE strRvtFileName = ?
        """, status, reason, regex_used, failed_field, failed_value, failed_reason, discipline, discipline_full, file_name)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Failed to update validation for {file_name}: {e}")



def get_users_list():
    """Return a list of (user_id, name) tuples from the users table."""
    conn = connect_to_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name FROM users ORDER BY name;")
        return [(row[0], row[1]) for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching users: {e}")
        return []
    finally:
        conn.close()


def get_review_tasks(project_id, cycle_id):
    """Return review schedule tasks for a project and cycle."""
    conn = connect_to_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT rs.schedule_id,
                   rs.review_date,
                   u.name,
                   rs.status
            FROM ReviewSchedule rs
            LEFT JOIN users u ON rs.assigned_to = u.user_id
            WHERE rs.project_id = ? AND rs.cycle_id = ?
            ORDER BY rs.review_date ASC;
            """,
            (project_id, cycle_id),
        )
        return [
            (row[0], row[1], row[2], row[3])
            for row in cursor.fetchall()
        ]
    except Exception as e:
        print(f"❌ Error fetching review tasks: {e}")
        return []
    finally:
        conn.close()

# ------------------------------------------------------------
# Review cycle detail functions
# ------------------------------------------------------------

def insert_review_cycle_details(
    project_id,
    cycle_id,
    construction_stage,
    proposed_fee,
    assigned_users,
    reviews_per_phase,
    planned_start_date,
    planned_completion_date,
    actual_start_date,
    actual_completion_date,
    hold_date,
    resume_date,
    new_contract,
):
    """Insert details for a review cycle."""
    conn = connect_to_db()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ReviewCycleDetails (
                project_id,
                cycle_id,
                construction_stage,
                proposed_fee,
                assigned_users,
                reviews_per_phase,
                planned_start_date,
                planned_completion_date,
                actual_start_date,
                actual_completion_date,
                hold_date,
                resume_date,
                new_contract
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                project_id,
                cycle_id,
                construction_stage,
                proposed_fee,
                assigned_users,
                reviews_per_phase,
                planned_start_date,
                planned_completion_date,
                actual_start_date,
                actual_completion_date,
                hold_date,
                resume_date,
                int(new_contract),
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error inserting review cycle details: {e}")
        return False
    finally:
        conn.close()


def update_review_task_assignee(schedule_id, user_id):
    """Update the assigned reviewer for a review task."""
    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ReviewSchedule SET assigned_to = ? WHERE schedule_id = ?",
            (user_id, schedule_id),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating review task assignee: {e}")
        return False
    finally:
        conn.close()

def update_review_cycle_details(
    project_id,
    cycle_id,
    construction_stage,
    proposed_fee,
    assigned_users,
    reviews_per_phase,
    planned_start_date,
    planned_completion_date,
    actual_start_date,
    actual_completion_date,
    hold_date,
    resume_date,
    new_contract,
):
    """Update details for a review cycle."""

    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE ReviewCycleDetails
            SET construction_stage = ?,
                proposed_fee = ?,
                assigned_users = ?,
                reviews_per_phase = ?,
                planned_start_date = ?,
                planned_completion_date = ?,
                actual_start_date = ?,
                actual_completion_date = ?,
                hold_date = ?,
                resume_date = ?,
                new_contract = ?
            WHERE project_id = ? AND cycle_id = ?;
            """,
            (
                construction_stage,
                proposed_fee,
                assigned_users,
                reviews_per_phase,
                planned_start_date,
                planned_completion_date,
                actual_start_date,
                actual_completion_date,
                hold_date,
                resume_date,
                int(new_contract),
                project_id,
                cycle_id,
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating review cycle details: {e}")
        return False
    finally:
        conn.close()


def upsert_project_review_progress(project_id, cycle_id, scoped_reviews, completed_reviews=0):
    """Create or update progress metrics for a project's review cycle."""
    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            MERGE project_reviews AS tgt
            USING (SELECT ? AS project_id, ? AS cycle_id) AS src
            ON tgt.project_id = src.project_id AND tgt.cycle_id = src.cycle_id
            WHEN MATCHED THEN
                UPDATE SET scoped_reviews = ?, completed_reviews = ?, last_updated = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (project_id, cycle_id, scoped_reviews, completed_reviews, last_updated)
                VALUES (?, ?, ?, ?, GETDATE());
            """,
            (
                project_id,
                cycle_id,
                scoped_reviews,
                completed_reviews,
                project_id,
                cycle_id,
                scoped_reviews,
                completed_reviews,
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating project review progress: {e}")
        return False
    finally:
        conn.close()


def get_project_review_progress(project_id, cycle_id):
    """Fetch scoped/completed review counts and last update timestamp."""
    conn = connect_to_db()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT scoped_reviews, completed_reviews, last_updated FROM project_reviews WHERE project_id = ? AND cycle_id = ?",
            (project_id, cycle_id),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "scoped_reviews": row[0],
            "completed_reviews": row[1],
            "last_updated": row[2].strftime("%Y-%m-%d %H:%M") if row[2] else "",
        }
    except Exception as e:
        print(f"❌ Error fetching review progress: {e}")
        return None
    finally:
        conn.close()


def get_review_summary(project_id, cycle_id):
    """Return key summary information for a review cycle."""
    conn = connect_to_db()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT p.project_name,
                   rp.cycle_id,
                   d.construction_stage,
                   rp.LicenseStartDate,
                   DATEDIFF(month, rp.LicenseStartDate, rp.LicenseEndDate) AS license_months,
                   pr.scoped_reviews,
                   pr.completed_reviews,
                   pr.last_updated
            FROM Projects p
            JOIN ReviewParameters rp ON p.project_id = rp.ProjectID AND rp.cycle_id = ?
            LEFT JOIN ReviewCycleDetails d ON d.project_id = rp.ProjectID AND d.cycle_id = rp.cycle_id
            LEFT JOIN project_reviews pr ON pr.project_id = rp.ProjectID AND pr.cycle_id = rp.cycle_id
            WHERE p.project_id = ?;
            """,
            (cycle_id, project_id),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "project_name": row[0],
            "cycle_id": row[1],
            "construction_stage": row[2] or "",
            "license_start": row[3].strftime("%Y-%m-%d") if row[3] else "",
            "license_duration": row[4],
            "scoped_reviews": row[5] if row[5] is not None else 0,
            "completed_reviews": row[6] if row[6] is not None else 0,
            "last_updated": row[7].strftime("%Y-%m-%d %H:%M") if row[7] else "",
        }
    except Exception as e:
        print(f"❌ Error fetching review summary: {e}")
        return None
    finally:
        conn.close()


def insert_contractual_link(project_id, review_cycle_id, bep_clause, billing_event, amount_due, status="Pending"):
    """Insert a contractual link record."""
    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ContractualLinks (
                project_id,
                review_cycle_id,
                bep_clause,
                billing_event,
                amount_due,
                status
            ) VALUES (?, ?, ?, ?, ?, ?);
            """,
            (project_id, review_cycle_id, bep_clause, billing_event, amount_due, status),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error inserting contractual link: {e}")
        return False
    finally:
        conn.close()


def get_contractual_links(project_id, review_cycle_id=None):
    """Fetch contractual links for a project, optionally filtered by cycle."""
    conn = connect_to_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        if review_cycle_id:
            cursor.execute(
                """
                SELECT bep_clause, billing_event, amount_due, status
                FROM ContractualLinks
                WHERE project_id = ? AND review_cycle_id = ?
                ORDER BY id;
                """,
                (project_id, review_cycle_id),
            )
        else:
            cursor.execute(
                """
                SELECT bep_clause, billing_event, amount_due, status
                FROM ContractualLinks
                WHERE project_id = ?
                ORDER BY id;
                """,
                (project_id,),
            )
        return [tuple(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching contractual links: {e}")
        return []
    finally:
        conn.close()


def get_review_cycles(project_id):
    """Return review cycles for the given project."""
    conn = connect_to_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT review_cycle_id, stage_id, start_date, end_date, num_reviews
            FROM review_cycles
            WHERE project_id = ?
            ORDER BY review_cycle_id;
            """,
            (project_id,),
        )
        return [tuple(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching review cycles: {e}")
        return []
    finally:
        conn.close()


def create_review_cycle(project_id, stage_id, start_date, end_date, num_reviews, created_by):
    """Insert a new review cycle and return its ID."""
    conn = connect_to_db()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO review_cycles
            (project_id, stage_id, start_date, end_date, num_reviews, created_by)
            VALUES (?, ?, ?, ?, ?, ?);
            SELECT SCOPE_IDENTITY();
            """,
            (project_id, stage_id, start_date, end_date, num_reviews, created_by),
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        return int(new_id)
    except Exception as e:
        print(f"❌ Error creating review cycle: {e}")
        return None
    finally:
        conn.close()


def update_review_cycle(review_cycle_id, start_date=None, end_date=None, num_reviews=None, stage_id=None):
    """Update an existing review cycle."""
    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE review_cycles
            SET start_date = COALESCE(?, start_date),
                end_date = COALESCE(?, end_date),
                num_reviews = COALESCE(?, num_reviews),
                stage_id = COALESCE(?, stage_id)
            WHERE review_cycle_id = ?;
            """,
            (start_date, end_date, num_reviews, stage_id, review_cycle_id),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating review cycle: {e}")
        return False
    finally:
        conn.close()


def delete_review_cycle(review_cycle_id):
    """Delete a review cycle."""
    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM review_cycles WHERE review_cycle_id = ?;",
            (review_cycle_id,),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error deleting review cycle: {e}")
        return False
    finally:
        conn.close()


def get_review_cycle_tasks(schedule_id):
    """Return tasks linked to a review schedule."""
    conn = connect_to_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT review_task_id, task_id, assigned_to, status
            FROM review_tasks
            WHERE schedule_id = ?
            ORDER BY review_task_id;
            """,
            (schedule_id,),
        )
        return [tuple(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching review tasks: {e}")
        return []
    finally:
        conn.close()


def update_review_cycle_task(review_task_id, assigned_to=None, status=None):
    """Update a review task's status or assignee."""
    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE review_tasks
            SET assigned_to = COALESCE(?, assigned_to),
                status = COALESCE(?, status)
            WHERE review_task_id = ?;
            """,
            (assigned_to, status, review_task_id),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating review task: {e}")
        return False
    finally:
        conn.close()


def get_bep_matrix(project_id):
    """Return BEP section data for a project."""
    conn = connect_to_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.id, s.section_title, p.responsible_user_id, p.status, p.notes
            FROM bep_sections s
            LEFT JOIN project_bep_sections p ON s.id = p.section_id AND p.project_id = ?
            ORDER BY s.id;
            """,
            (project_id,),
        )
        return [tuple(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching BEP matrix: {e}")
=======
def get_projects_full():
    """Return all rows from the vw_projects_full view."""
    conn = connect_to_db()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vw_projects_full")
        columns = [c[0] for c in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching full projects: {e}")
        return []
    finally:
        conn.close()



def upsert_bep_section(project_id, section_id, responsible_user_id, status, notes):
    """Create or update a project BEP section record."""

def update_project_financials(project_id, contract_value=None, payment_terms=None):
    """Update financial fields in the projects table."""

    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            MERGE project_bep_sections AS tgt
            USING (SELECT ? AS project_id, ? AS section_id) AS src
            ON tgt.project_id = src.project_id AND tgt.section_id = src.section_id
            WHEN MATCHED THEN
                UPDATE SET responsible_user_id = ?, status = ?, notes = ?
            WHEN NOT MATCHED THEN
                INSERT (project_id, section_id, responsible_user_id, status, notes)
                VALUES (src.project_id, src.section_id, ?, ?, ?);
            """,
            (
                project_id,
                section_id,
                responsible_user_id,
                status,
                notes,
                responsible_user_id,
                status,
                notes,
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error upserting BEP section: {e}")
=======
        sets = []
        params = []
        if contract_value is not None:
            sets.append("contract_value = ?")
            params.append(contract_value)
        if payment_terms is not None:
            sets.append("payment_terms = ?")
            params.append(payment_terms)
        if sets:
            sql = "UPDATE projects SET " + ", ".join(sets) + " WHERE project_id = ?"
            params.append(project_id)
            cursor.execute(sql, params)
            conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating project financials: {e}")
        return False
    finally:
        conn.close()



def update_bep_status(project_id, section_id, status):
    """Update the status of a BEP section for a project."""

def update_client_info(project_id, client_contact=None, contact_email=None):
    """Update client contact details for a project."""

    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE project_bep_sections SET status = ? WHERE project_id = ? AND section_id = ?;",
            (status, project_id, section_id),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating BEP status: {e}")

        sets = []
        params = []
        if client_contact is not None:
            sets.append("client_contact = ?")
            params.append(client_contact)
        if contact_email is not None:
            sets.append("contact_email = ?")
            params.append(contact_email)
        if sets:
            sql = "UPDATE clients SET " + ", ".join(sets) + " WHERE project_id = ?"
            params.append(project_id)
            cursor.execute(sql, params)
            conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating client info: {e}")

        return False
    finally:
        conn.close()
        
if __name__ == "__main__":
    conn = connect_to_db()
    if conn:
        print("✅ Connected to database successfully.")
        conn.close()
    else:
        print("❌ Failed to connect.")



