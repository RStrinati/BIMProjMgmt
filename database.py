def create_service_template(template_name, description, service_type, parameters, created_by):
    """Insert a new service template."""
    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {S.ServiceTemplates.TABLE} (
                {S.ServiceTemplates.TEMPLATE_NAME}, {S.ServiceTemplates.DESCRIPTION},
                {S.ServiceTemplates.SERVICE_TYPE}, {S.ServiceTemplates.PARAMETERS},
                {S.ServiceTemplates.CREATED_BY}
            ) VALUES (?, ?, ?, ?, ?);
            """,
            (template_name, description, service_type, parameters, created_by)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error creating service template: {e}")
        return False
    finally:
        conn.close()

def get_service_templates():
    """Fetch all service templates."""
    conn = connect_to_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT {S.ServiceTemplates.ID}, {S.ServiceTemplates.TEMPLATE_NAME}, {S.ServiceTemplates.DESCRIPTION}, {S.ServiceTemplates.SERVICE_TYPE}, {S.ServiceTemplates.PARAMETERS}, {S.ServiceTemplates.CREATED_BY}, {S.ServiceTemplates.CREATED_AT}, {S.ServiceTemplates.IS_ACTIVE} FROM {S.ServiceTemplates.TABLE} WHERE {S.ServiceTemplates.IS_ACTIVE} = 1 ORDER BY {S.ServiceTemplates.ID};"
        )
        templates = [dict(
            id=row[0],
            template_name=row[1],
            description=row[2],
            service_type=row[3],
            parameters=row[4],
            created_by=row[5],
            created_at=row[6],
            is_active=row[7]
        ) for row in cursor.fetchall()]
        return templates
    except Exception as e:
        print(f"❌ Error fetching service templates: {e}")
        return []
    finally:
        conn.close()

def update_service_template(template_id, template_name=None, description=None, service_type=None, parameters=None, is_active=None):
    """Update an existing service template."""
    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        update_fields = {}
        if template_name is not None:
            update_fields[S.ServiceTemplates.TEMPLATE_NAME] = template_name
        if description is not None:
            update_fields[S.ServiceTemplates.DESCRIPTION] = description
        if service_type is not None:
            update_fields[S.ServiceTemplates.SERVICE_TYPE] = service_type
        if parameters is not None:
            update_fields[S.ServiceTemplates.PARAMETERS] = parameters
        if is_active is not None:
            update_fields[S.ServiceTemplates.IS_ACTIVE] = is_active
        if not update_fields:
            return False
        set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
        values = list(update_fields.values()) + [template_id]
        cursor.execute(
            f"UPDATE {S.ServiceTemplates.TABLE} SET {set_clause} WHERE {S.ServiceTemplates.ID} = ?",
            values
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating service template: {e}")
        return False
    finally:
        conn.close()

def delete_service_template(template_id):
    """Soft delete a service template by setting is_active to 0."""
    return update_service_template(template_id, is_active=0)
import logging
import pyodbc
import os
import pandas as pd
from datetime import datetime, timedelta

from config import Config
from constants import schema as S

logger = logging.getLogger(__name__)

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

        cursor.execute(
            f"""
            INSERT INTO {S.Projects.TABLE} (
                {S.Projects.NAME}, {S.Projects.FOLDER_PATH}, {S.Projects.IFC_FOLDER_PATH},
                {S.Projects.START_DATE}, {S.Projects.END_DATE}
            ) VALUES (?, ?, ?, ?, ?);
            """,
            (project_name, folder_path, ifc_folder_path, start_date, end_date),
        )

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
        cursor.execute(
            f"SELECT {S.Projects.ID}, {S.Projects.NAME} FROM {S.Projects.TABLE} ORDER BY {S.Projects.ID};"
        )
        projects = [(row[0], row[1]) for row in cursor.fetchall()]
        return projects
    except Exception as e:
        print(f"❌ Error fetching projects: {str(e)}")
        return []
    finally:
        conn.close()

def get_project_details(project_id):
    """Fetch project details from the database including client information."""
    conn = connect_to_db("ProjectManagement")  
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT p.{S.Projects.NAME}, p.{S.Projects.START_DATE}, p.{S.Projects.END_DATE}, 
                   p.{S.Projects.STATUS}, p.{S.Projects.PRIORITY},
                   c.{S.Clients.CLIENT_NAME}, c.{S.Clients.CONTACT_NAME}, c.{S.Clients.CONTACT_EMAIL}
            FROM dbo.{S.Projects.TABLE} p
            LEFT JOIN dbo.{S.Clients.TABLE} c ON p.{S.Projects.CLIENT_ID} = c.{S.Clients.CLIENT_ID}
            WHERE p.{S.Projects.ID} = ?;
            """,
            (project_id,),
        )
        row = cursor.fetchone()
        
        if row:
            result = {
                "project_name": row[0],
                "start_date": row[1].strftime('%Y-%m-%d') if row[1] else "",
                "end_date": row[2].strftime('%Y-%m-%d') if row[2] else "",
                "status": row[3],
                "priority": row[4],
                "client_name": row[5],
                "client_contact": row[6],
                "contact_email": row[7]
            }
            return result
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
        cursor.execute(
            f"""
            UPDATE dbo.{S.Projects.TABLE}
            SET {S.Projects.START_DATE} = ?, {S.Projects.END_DATE} = ?, {S.Projects.STATUS} = ?, {S.Projects.PRIORITY} = ?, {S.Projects.UPDATED_AT} = GETDATE()
            WHERE {S.Projects.ID} = ?;
            """,
            (start_date, end_date, status, priority, project_id),
        )
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
            f"""
            SELECT {S.ReviewSchedule.ID}, {S.ReviewSchedule.REVIEW_DATE}, {S.ReviewSchedule.CYCLE_ID},
                   project_name, construction_stage, proposed_fee, assigned_users,
                   reviews_per_phase, planned_start_date, planned_completion_date,
                   actual_start_date, actual_completion_date, hold_date, resume_date, new_contract
            FROM vw_ReviewScheduleDetails
            WHERE {S.ReviewSchedule.PROJECT_ID} = ? AND {S.ReviewSchedule.CYCLE_ID} = ?
            ORDER BY {S.ReviewSchedule.REVIEW_DATE} ASC;
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
            cursor.execute(
                f"UPDATE dbo.{S.Projects.TABLE} SET {S.Projects.FOLDER_PATH} = ? WHERE {S.Projects.ID} = ?",
                (models_path, project_id),
            )

        if data_path is not None:
            cursor.execute(
                f"UPDATE dbo.{S.Projects.TABLE} SET {S.Projects.DATA_EXPORT_FOLDER} = ? WHERE {S.Projects.ID} = ?",
                (data_path, project_id),
            )

        if ifc_path is not None:
            cursor.execute(
                f"UPDATE dbo.{S.Projects.TABLE} SET {S.Projects.IFC_FOLDER_PATH} = ? WHERE {S.Projects.ID} = ?",
                (ifc_path, project_id),
            )

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
        cursor.execute(
            f"""
            SELECT TOP 5 {S.ACCImportLogs.FOLDER_NAME}, {S.ACCImportLogs.IMPORT_DATE}, {S.ACCImportLogs.SUMMARY}
            FROM {S.ACCImportLogs.TABLE}
            WHERE {S.ACCImportLogs.PROJECT_ID} = ?
            ORDER BY {S.ACCImportLogs.IMPORT_DATE} DESC
            """,
            (project_id,),
        )
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
        cursor.execute(
            f"SELECT {S.Projects.FOLDER_PATH}, {S.Projects.IFC_FOLDER_PATH} FROM dbo.{S.Projects.TABLE} WHERE {S.Projects.ID} = ?",
            (project_id,),
        )
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
        cursor.execute(
            f"""
            SELECT DISTINCT {S.ReviewParameters.CYCLE_ID} FROM {S.ReviewParameters.TABLE}
            WHERE {S.ReviewParameters.PROJECT_ID} = ?
            ORDER BY {S.ReviewParameters.CYCLE_ID} DESC;
            """,
            (project_id,),
        )
        
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
        cursor.execute(
            f"DELETE FROM {S.ACCDocs.TABLE} WHERE {S.ACCDocs.PROJECT_ID} = ?",
            (project_id,),
        )
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
            cursor.executemany(
                f"""
                INSERT INTO {S.ACCDocs.TABLE}
                ({S.ACCDocs.FILE_NAME}, {S.ACCDocs.FILE_PATH}, {S.ACCDocs.DATE_MODIFIED}, {S.ACCDocs.FILE_TYPE}, {S.ACCDocs.FILE_SIZE_KB}, {S.ACCDocs.CREATED_AT}, {S.ACCDocs.DELETED_AT}, {S.ACCDocs.PROJECT_ID})
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                file_details,
            )

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
        cursor.execute(f"DELETE FROM dbo.{S.ACCDocs.TABLE}")
        conn.commit()

        # Insert new data
        cursor.executemany(
            f"""
            INSERT INTO dbo.{S.ACCDocs.TABLE} ({S.ACCDocs.FILE_NAME}, {S.ACCDocs.FILE_PATH}, {S.ACCDocs.DATE_MODIFIED}, {S.ACCDocs.FILE_TYPE}, {S.ACCDocs.FILE_SIZE_KB})
            VALUES (?, ?, ?, ?, ?)
            """,
            file_details,
        )

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
    try:
        conn = connect_to_db()
        if not conn:
            return False
            
        cursor = conn.cursor()
        cursor.execute(
            f"""
            MERGE INTO {S.ACCImportFolders.TABLE} AS target
            USING (SELECT ? AS {S.ACCImportFolders.PROJECT_ID}, ? AS {S.ACCImportFolders.ACC_FOLDER_PATH}) AS source
            ON target.{S.ACCImportFolders.PROJECT_ID} = source.{S.ACCImportFolders.PROJECT_ID}
            WHEN MATCHED THEN UPDATE SET {S.ACCImportFolders.ACC_FOLDER_PATH} = source.{S.ACCImportFolders.ACC_FOLDER_PATH}
            WHEN NOT MATCHED THEN INSERT ({S.ACCImportFolders.PROJECT_ID}, {S.ACCImportFolders.ACC_FOLDER_PATH})
                VALUES (source.{S.ACCImportFolders.PROJECT_ID}, source.{S.ACCImportFolders.ACC_FOLDER_PATH});
            """,
            (project_id, folder_path),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving ACC folder path: {e}")
        return False

def get_acc_folder_path(project_id):
    try:
        conn = connect_to_db()
        if not conn:
            return None
            
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT {S.ACCImportFolders.ACC_FOLDER_PATH} FROM {S.ACCImportFolders.TABLE} WHERE {S.ACCImportFolders.PROJECT_ID} = ?",
            (project_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"Error getting ACC folder path: {e}")
        return None

def log_acc_import(project_id, folder_name, summary):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        INSERT INTO {S.ACCImportLogs.TABLE} ({S.ACCImportLogs.PROJECT_ID}, {S.ACCImportLogs.FOLDER_NAME}, {S.ACCImportLogs.IMPORT_DATE}, {S.ACCImportLogs.SUMMARY})
        VALUES (?, ?, GETDATE(), ?)
        """,
        (project_id, folder_name, summary),
    )
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
        cursor.execute(
            f"SELECT {S.Users.ID}, {S.Users.NAME} FROM {S.Users.TABLE} ORDER BY {S.Users.NAME};"
        )
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
            f"""
            SELECT rs.{S.ReviewSchedule.ID}, rs.{S.ReviewSchedule.REVIEW_DATE},
                   u.{S.Users.NAME}, rs.{S.ReviewSchedule.STATUS}
            FROM {S.ReviewSchedule.TABLE} rs
            LEFT JOIN {S.Users.TABLE} u ON rs.{S.ReviewSchedule.ASSIGNED_TO} = u.{S.Users.ID}
            WHERE rs.{S.ReviewSchedule.PROJECT_ID} = ? AND rs.{S.ReviewSchedule.CYCLE_ID} = ?
            ORDER BY rs.{S.ReviewSchedule.REVIEW_DATE} ASC;
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
            f"""
            INSERT INTO {S.ReviewCycleDetails.TABLE} (
                {S.ReviewCycleDetails.PROJECT_ID},
                {S.ReviewCycleDetails.CYCLE_ID},
                {S.ReviewCycleDetails.CONSTRUCTION_STAGE},
                {S.ReviewCycleDetails.PROPOSED_FEE},
                {S.ReviewCycleDetails.ASSIGNED_USERS},
                {S.ReviewCycleDetails.REVIEWS_PER_PHASE},
                {S.ReviewCycleDetails.PLANNED_START},
                {S.ReviewCycleDetails.PLANNED_COMPLETION},
                {S.ReviewCycleDetails.ACTUAL_START},
                {S.ReviewCycleDetails.ACTUAL_COMPLETION},
                {S.ReviewCycleDetails.HOLD_DATE},
                {S.ReviewCycleDetails.RESUME_DATE},
                {S.ReviewCycleDetails.NEW_CONTRACT}
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
            f"UPDATE {S.ReviewSchedule.TABLE} SET {S.ReviewSchedule.ASSIGNED_TO} = ? WHERE {S.ReviewSchedule.ID} = ?",
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
            f"""
            UPDATE {S.ReviewCycleDetails.TABLE}
            SET {S.ReviewCycleDetails.CONSTRUCTION_STAGE} = ?,
                {S.ReviewCycleDetails.PROPOSED_FEE} = ?,
                {S.ReviewCycleDetails.ASSIGNED_USERS} = ?,
                {S.ReviewCycleDetails.REVIEWS_PER_PHASE} = ?,
                {S.ReviewCycleDetails.PLANNED_START} = ?,
                {S.ReviewCycleDetails.PLANNED_COMPLETION} = ?,
                {S.ReviewCycleDetails.ACTUAL_START} = ?,
                {S.ReviewCycleDetails.ACTUAL_COMPLETION} = ?,
                {S.ReviewCycleDetails.HOLD_DATE} = ?,
                {S.ReviewCycleDetails.RESUME_DATE} = ?,
                {S.ReviewCycleDetails.NEW_CONTRACT} = ?
            WHERE {S.ReviewCycleDetails.PROJECT_ID} = ? AND {S.ReviewCycleDetails.CYCLE_ID} = ?;
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
            f"""
            MERGE {S.ProjectReviews.TABLE} AS tgt
            USING (SELECT ? AS {S.ProjectReviews.PROJECT_ID}, ? AS {S.ProjectReviews.CYCLE_ID}) AS src
            ON tgt.{S.ProjectReviews.PROJECT_ID} = src.{S.ProjectReviews.PROJECT_ID}
               AND tgt.{S.ProjectReviews.CYCLE_ID} = src.{S.ProjectReviews.CYCLE_ID}
            WHEN MATCHED THEN
                UPDATE SET {S.ProjectReviews.SCOPED_REVIEWS} = ?,
                           {S.ProjectReviews.COMPLETED_REVIEWS} = ?,
                           {S.ProjectReviews.LAST_UPDATED} = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT ({S.ProjectReviews.PROJECT_ID}, {S.ProjectReviews.CYCLE_ID}, {S.ProjectReviews.SCOPED_REVIEWS}, {S.ProjectReviews.COMPLETED_REVIEWS}, {S.ProjectReviews.LAST_UPDATED})
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
            f"SELECT {S.ProjectReviews.SCOPED_REVIEWS}, {S.ProjectReviews.COMPLETED_REVIEWS}, {S.ProjectReviews.LAST_UPDATED} FROM {S.ProjectReviews.TABLE} WHERE {S.ProjectReviews.PROJECT_ID} = ? AND {S.ProjectReviews.CYCLE_ID} = ?",
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
            f"""
            SELECT p.{S.Projects.NAME},
                   rp.{S.ReviewParameters.CYCLE_ID},
                   d.{S.ReviewCycleDetails.CONSTRUCTION_STAGE},
                   rp.{S.ReviewParameters.LICENSE_START},
                   DATEDIFF(month, rp.{S.ReviewParameters.LICENSE_START}, rp.{S.ReviewParameters.LICENSE_END}) AS license_months,
                   pr.{S.ProjectReviews.SCOPED_REVIEWS},
                   pr.{S.ProjectReviews.COMPLETED_REVIEWS},
                   pr.{S.ProjectReviews.LAST_UPDATED}
            FROM {S.Projects.TABLE} p
            JOIN {S.ReviewParameters.TABLE} rp ON p.{S.Projects.ID} = rp.{S.ReviewParameters.PROJECT_ID} AND rp.{S.ReviewParameters.CYCLE_ID} = ?
            LEFT JOIN {S.ReviewCycleDetails.TABLE} d ON d.{S.ReviewCycleDetails.PROJECT_ID} = rp.{S.ReviewParameters.PROJECT_ID} AND d.{S.ReviewCycleDetails.CYCLE_ID} = rp.{S.ReviewParameters.CYCLE_ID}
            LEFT JOIN {S.ProjectReviews.TABLE} pr ON pr.{S.ProjectReviews.PROJECT_ID} = rp.{S.ReviewParameters.PROJECT_ID} AND pr.{S.ProjectReviews.CYCLE_ID} = rp.{S.ReviewParameters.CYCLE_ID}
            WHERE p.{S.Projects.ID} = ?;
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
            f"""
            INSERT INTO {S.ContractualLinks.TABLE} (
                {S.ContractualLinks.PROJECT_ID},
                {S.ContractualLinks.REVIEW_CYCLE_ID},
                {S.ContractualLinks.BEP_CLAUSE},
                {S.ContractualLinks.BILLING_EVENT},
                {S.ContractualLinks.AMOUNT_DUE},
                {S.ContractualLinks.STATUS}
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
                f"""
                SELECT {S.ContractualLinks.BEP_CLAUSE}, {S.ContractualLinks.BILLING_EVENT}, {S.ContractualLinks.AMOUNT_DUE}, {S.ContractualLinks.STATUS}
                FROM {S.ContractualLinks.TABLE}
                WHERE {S.ContractualLinks.PROJECT_ID} = ? AND {S.ContractualLinks.REVIEW_CYCLE_ID} = ?
                ORDER BY {S.ContractualLinks.ID};
                """,
                (project_id, review_cycle_id),
            )
        else:
            cursor.execute(
                f"""
                SELECT {S.ContractualLinks.BEP_CLAUSE}, {S.ContractualLinks.BILLING_EVENT}, {S.ContractualLinks.AMOUNT_DUE}, {S.ContractualLinks.STATUS}
                FROM {S.ContractualLinks.TABLE}
                WHERE {S.ContractualLinks.PROJECT_ID} = ?
                ORDER BY {S.ContractualLinks.ID};
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
    """Return review cycles for the given project from ServiceReviews table."""
    conn = connect_to_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sr.review_id, ps.service_name, sr.cycle_no, sr.planned_date, 
                   sr.due_date, sr.status, sr.disciplines
            FROM ServiceReviews sr
            LEFT JOIN ProjectServices ps ON sr.service_id = ps.service_id
            WHERE ps.project_id = ?
            ORDER BY sr.planned_date, sr.cycle_no;
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
            f"""
            INSERT INTO {S.ReviewCycles.TABLE}
            ({S.ReviewCycles.PROJECT_ID}, {S.ReviewCycles.STAGE_ID}, {S.ReviewCycles.START_DATE}, {S.ReviewCycles.END_DATE}, {S.ReviewCycles.NUM_REVIEWS}, {S.ReviewCycles.CREATED_BY})
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
            f"""
            UPDATE {S.ReviewCycles.TABLE}
            SET {S.ReviewCycles.START_DATE} = COALESCE(?, {S.ReviewCycles.START_DATE}),
                {S.ReviewCycles.END_DATE} = COALESCE(?, {S.ReviewCycles.END_DATE}),
                {S.ReviewCycles.NUM_REVIEWS} = COALESCE(?, {S.ReviewCycles.NUM_REVIEWS}),
                {S.ReviewCycles.STAGE_ID} = COALESCE(?, {S.ReviewCycles.STAGE_ID})
            WHERE {S.ReviewCycles.ID} = ?;
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
            f"DELETE FROM {S.ReviewCycles.TABLE} WHERE {S.ReviewCycles.ID} = ?;",
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
            f"""
            SELECT {S.ReviewTasks.ID}, {S.ReviewTasks.TASK_ID}, {S.ReviewTasks.ASSIGNED_TO}, {S.ReviewTasks.STATUS}
            FROM {S.ReviewTasks.TABLE}
            WHERE {S.ReviewTasks.SCHEDULE_ID} = ?
            ORDER BY {S.ReviewTasks.ID};
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
            f"""
            UPDATE {S.ReviewTasks.TABLE}
            SET {S.ReviewTasks.ASSIGNED_TO} = COALESCE(?, {S.ReviewTasks.ASSIGNED_TO}),
                {S.ReviewTasks.STATUS} = COALESCE(?, {S.ReviewTasks.STATUS})
            WHERE {S.ReviewTasks.ID} = ?;
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
        return []
    finally:
        conn.close()


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
        return False
    finally:
        conn.close()


def update_project_financials(project_id, contract_value=None, payment_terms=None):
    """Update financial fields in the projects table."""

    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
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
        return False
    finally:
        conn.close()


def update_client_info(project_id, client_contact=None, contact_email=None):
    """Update client contact details for a project."""
    
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        
        # First, get the client_id for this project
        cursor.execute(
            f"SELECT {S.Projects.CLIENT_ID} FROM dbo.{S.Projects.TABLE} WHERE {S.Projects.ID} = ?",
            (project_id,)
        )
        result = cursor.fetchone()
        
        if not result or not result[0]:
            print(f"⚠️ No client_id found for project {project_id}")
            return False
            
        client_id = result[0]
        
        # Update the client information
        sets = []
        params = []
        if client_contact is not None:
            sets.append(f"{S.Clients.CONTACT_NAME} = ?")
            params.append(client_contact)
        if contact_email is not None:
            sets.append(f"{S.Clients.CONTACT_EMAIL} = ?")
            params.append(contact_email)
            
        if sets:
            sql = f"UPDATE dbo.{S.Clients.TABLE} SET " + ", ".join(sets) + f" WHERE {S.Clients.CLIENT_ID} = ?"
            params.append(client_id)
            cursor.execute(sql, params)
            conn.commit()
            print(f"✅ Updated client info for client_id {client_id}")
            
        return True
    except Exception as e:
        print(f"❌ Error updating client info: {e}")
        return False
    finally:
        conn.close()


def get_available_clients():
    """Return list of all available clients."""
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {S.Clients.CLIENT_ID}, {S.Clients.CLIENT_NAME}, 
                   {S.Clients.CONTACT_NAME}, {S.Clients.CONTACT_EMAIL}
            FROM dbo.{S.Clients.TABLE}
            ORDER BY {S.Clients.CLIENT_NAME};
            """
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error fetching clients: {e}")
        return []
    finally:
        conn.close()


def get_available_project_types():
    """Return list of all available project types."""
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {S.ProjectTypes.TYPE_ID}, {S.ProjectTypes.TYPE_NAME}
            FROM dbo.{S.ProjectTypes.TABLE}
            ORDER BY {S.ProjectTypes.TYPE_NAME};
            """
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error fetching project types: {e}")
        return []
    finally:
        conn.close()


def get_available_sectors():
    """Return list of all available sectors."""
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {S.Sectors.SECTOR_ID}, {S.Sectors.SECTOR_NAME}
            FROM dbo.{S.Sectors.TABLE}
            ORDER BY {S.Sectors.SECTOR_NAME};
            """
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error fetching sectors: {e}")
        return []
    finally:
        conn.close()


def get_available_delivery_methods():
    """Return list of all available delivery methods."""
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {S.DeliveryMethods.DELIVERY_METHOD_ID}, {S.DeliveryMethods.DELIVERY_METHOD_NAME}
            FROM dbo.{S.DeliveryMethods.TABLE}
            ORDER BY {S.DeliveryMethods.DELIVERY_METHOD_NAME};
            """
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error fetching delivery methods: {e}")
        return []
    finally:
        conn.close()


def get_available_construction_phases():
    """Return list of all available construction phases."""
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {S.ProjectPhases.PROJECT_PHASE_ID}, {S.ProjectPhases.PROJECT_PHASE_NAME}
            FROM dbo.{S.ProjectPhases.TABLE}
            ORDER BY {S.ProjectPhases.PROJECT_PHASE_NAME};
            """
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error fetching construction phases: {e}")
        return []
    finally:
        conn.close()


def get_available_construction_stages():
    """Return list of all available construction stages."""
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {S.ConstructionStages.CONSTRUCTION_STAGE_ID}, {S.ConstructionStages.CONSTRUCTION_STAGE_NAME}
            FROM dbo.{S.ConstructionStages.TABLE}
            ORDER BY {S.ConstructionStages.CONSTRUCTION_STAGE_NAME};
            """
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error fetching construction stages: {e}")
        return []
    finally:
        conn.close()


def get_available_users():
    """Return list of all available users for project managers and leads."""
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {S.Users.ID}, {S.Users.NAME}, {S.Users.EMAIL}
            FROM dbo.{S.Users.TABLE}
            ORDER BY {S.Users.NAME};
            """
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error fetching users: {e}")
        return []
    finally:
        conn.close()


def insert_client(client_data):
    """Insert a new client into the database."""
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {S.Clients.TABLE} (
                {S.Clients.CLIENT_NAME}, {S.Clients.CONTACT_NAME}, {S.Clients.CONTACT_EMAIL},
                {S.Clients.CONTACT_PHONE}, {S.Clients.ADDRESS}, {S.Clients.CITY},
                {S.Clients.STATE}, {S.Clients.POSTCODE}, {S.Clients.COUNTRY}
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                client_data.get('name', ''),
                client_data.get('contact_name', ''),
                client_data.get('contact_email', ''),
                client_data.get('contact_phone', ''),
                client_data.get('address', ''),
                client_data.get('city', ''),
                client_data.get('state', ''),
                client_data.get('postcode', ''),
                client_data.get('country', '')
            )
        )
        conn.commit()
        print(f"✅ Client '{client_data.get('name')}' created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating client: {e}")
        return False
    finally:
        conn.close()


def assign_client_to_project(project_id, client_id):
    """Assign a client to a project by updating the project's client_id."""
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE dbo.{S.Projects.TABLE} 
            SET {S.Projects.CLIENT_ID} = ? 
            WHERE {S.Projects.ID} = ?
            """,
            (client_id, project_id)
        )
        conn.commit()
        print(f"✅ Assigned client {client_id} to project {project_id}")
        return True
    except Exception as e:
        print(f"❌ Error assigning client to project: {e}")
        return False
    finally:
        conn.close()


def create_new_client(client_data):
    """Create a new client in the database and return the client_id."""
    conn = connect_to_db("ProjectManagement")
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO dbo.{S.Clients.TABLE} (
                {S.Clients.CLIENT_NAME}, {S.Clients.CONTACT_NAME}, {S.Clients.CONTACT_EMAIL},
                {S.Clients.CONTACT_PHONE}, {S.Clients.ADDRESS}, {S.Clients.CITY},
                {S.Clients.STATE}, {S.Clients.POSTCODE}, {S.Clients.COUNTRY}
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_data['client_name'],
                client_data['contact_name'], 
                client_data['contact_email'],
                client_data['contact_phone'],
                client_data['address'],
                client_data['city'],
                client_data['state'],
                client_data['postcode'],
                client_data['country']
            )
        )
        conn.commit()
        
        # Get the newly created client_id
        cursor.execute("SELECT @@IDENTITY")
        client_id = cursor.fetchone()[0]
        
        print(f"✅ Created new client: {client_data['client_name']} (ID: {client_id})")
        return client_id
        
    except Exception as e:
        print(f"❌ Error creating client: {e}")
        return None
    finally:
        conn.close()


def get_reference_options(table):
    """Return (id, name) tuples from a reference table."""
    conn = connect_to_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        id_col = table.rstrip('s') + '_id'
        name_col = table.rstrip('s') + '_name'
        cursor.execute(f"SELECT {id_col}, {name_col} FROM {table} ORDER BY {name_col};")
        return [(row[0], row[1]) for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching {table}: {e}")
        return []
    finally:
        conn.close()


def insert_project_full(data):
    """Insert a project record with arbitrary fields.

    SQL Server is strict about data types, so values coming from the
    frontend (often as strings) need to be coerced into the proper
    numeric types before insertion. Without this, pyodbc tries to insert
    NVARCHAR values into numeric columns and the database raises
    "Error converting data type nvarchar to numeric".
    """
    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cols = list(data.keys())
        if not cols:
            return False

        # Columns expected to be numeric in the projects table
        numeric_fields = {
            S.Projects.CLIENT_ID,
            S.Projects.TYPE_ID,
            S.Projects.SECTOR_ID,
            S.Projects.METHOD_ID,
            S.Projects.PHASE_ID,
            S.Projects.STAGE_ID,
            S.Projects.PROJECT_MANAGER,
            S.Projects.INTERNAL_LEAD,
            S.Projects.CONTRACT_VALUE,
            S.Projects.AGREED_FEE,
            S.Projects.PRIORITY,
            # New numeric fields added for enhanced project creation
            S.Projects.AREA_HECTARES,
            S.Projects.MW_CAPACITY,
        }

        values = []
        for c in cols:
            val = data.get(c)
            if val in ("", None):
                values.append(None)
            elif c in numeric_fields:
                try:
                    values.append(float(val) if "." in str(val) else int(val))
                except (ValueError, TypeError):
                    values.append(None)
            else:
                values.append(val)

        placeholders = ', '.join(['?'] * len(cols))
        sql = f"INSERT INTO projects ({', '.join(cols)}) VALUES ({placeholders})"
        cursor.execute(sql, values)
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error inserting project: {e}")
        return False
    finally:
        conn.close()


def update_project_record(project_id, data):
    """Update arbitrary project fields for a given project_id."""
    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cols = [c for c in data.keys() if c]
        if not cols:
            return False
        set_clause = ', '.join([f"{c} = ?" for c in cols])
        sql = f"UPDATE projects SET {set_clause} WHERE project_id = ?"
        cursor.execute(sql, [data[c] for c in cols] + [project_id])
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating project: {e}")
        return False
    finally:
        conn.close()
        
# ===================== Project Bookmarks Functions =====================

def get_project_bookmarks(project_id):
    """Get all bookmarks for a specific project."""
    conn = connect_to_db()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {S.ProjectBookmarks.ID}, {S.ProjectBookmarks.NAME}, 
                   {S.ProjectBookmarks.URL}, {S.ProjectBookmarks.DESCRIPTION}, 
                   {S.ProjectBookmarks.CATEGORY}, {S.ProjectBookmarks.TAGS},
                   {S.ProjectBookmarks.NOTES}, {S.ProjectBookmarks.CREATED_AT}
            FROM {S.ProjectBookmarks.TABLE} 
            WHERE {S.ProjectBookmarks.PROJECT_ID} = ?
            ORDER BY {S.ProjectBookmarks.CATEGORY}, {S.ProjectBookmarks.NAME}
            """,
            (project_id,)
        )
        bookmarks = []
        for row in cursor.fetchall():
            bookmarks.append({
                'id': row[0],
                'name': row[1],
                'url': row[2],
                'description': row[3],
                'category': row[4],
                'tags': row[5],
                'notes': row[6],
                'created_at': row[7]
            })
        return bookmarks
    except Exception as e:
        print(f"❌ Error fetching bookmarks: {e}")
        return []
    finally:
        conn.close()

def add_bookmark(project_id, name, url, description="", category="General", tags="", notes=""):
    """Add a new bookmark for a project."""
    conn = connect_to_db()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute(
            f"""
            INSERT INTO {S.ProjectBookmarks.TABLE} (
                {S.ProjectBookmarks.PROJECT_ID}, {S.ProjectBookmarks.NAME}, 
                {S.ProjectBookmarks.URL}, {S.ProjectBookmarks.DESCRIPTION}, 
                {S.ProjectBookmarks.CATEGORY}, {S.ProjectBookmarks.TAGS},
                {S.ProjectBookmarks.NOTES}, {S.ProjectBookmarks.CREATED_AT}
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, name, url, description, category, tags, notes, created_at)
        )
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error adding bookmark: {e}")
        return False
    finally:
        conn.close()

def update_bookmark(bookmark_id, name=None, url=None, description=None, category=None, tags=None, notes=None):
    """Update an existing bookmark."""
    conn = connect_to_db()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Build dynamic update query
        update_fields = {}
        if name is not None:
            update_fields[S.ProjectBookmarks.NAME] = name
        if url is not None:
            update_fields[S.ProjectBookmarks.URL] = url
        if description is not None:
            update_fields[S.ProjectBookmarks.DESCRIPTION] = description
        if category is not None:
            update_fields[S.ProjectBookmarks.CATEGORY] = category
        if tags is not None:
            update_fields[S.ProjectBookmarks.TAGS] = tags
        if notes is not None:
            update_fields[S.ProjectBookmarks.NOTES] = notes
            
        if not update_fields:
            return False
            
        set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
        values = list(update_fields.values()) + [bookmark_id]
        
        cursor.execute(
            f"UPDATE {S.ProjectBookmarks.TABLE} SET {set_clause} WHERE {S.ProjectBookmarks.ID} = ?",
            values
        )
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating bookmark: {e}")
        return False
    finally:
        conn.close()

def delete_bookmark(bookmark_id):
    """Delete a bookmark by ID."""
    conn = connect_to_db()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM {S.ProjectBookmarks.TABLE} WHERE {S.ProjectBookmarks.ID} = ?",
            (bookmark_id,)
        )
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error deleting bookmark: {e}")
        return False
    finally:
        conn.close()

def get_bookmark_categories(project_id):
    """Get distinct categories for a project's bookmarks."""
    conn = connect_to_db()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT DISTINCT {S.ProjectBookmarks.CATEGORY}
            FROM {S.ProjectBookmarks.TABLE} 
            WHERE {S.ProjectBookmarks.PROJECT_ID} = ?
            ORDER BY {S.ProjectBookmarks.CATEGORY}
            """,
            (project_id,)
        )
        categories = [row[0] for row in cursor.fetchall()]
        return categories
    except Exception as e:
        print(f"❌ Error fetching bookmark categories: {e}")
        return []
    finally:
        conn.close()
        
def delete_project(project_id):
    """Delete a project and all related data from the database."""
    conn = connect_to_db()
    if conn is None:
        print("❌ Database connection failed.")
        return False

    try:
        cursor = conn.cursor()
        
        # Delete in order of dependencies (child tables first)
        
        # Project-specific documents and clauses
        cursor.execute(f"DELETE FROM {S.ProjectClauses.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ProjectSections.TABLE} ps INNER JOIN {S.ProjectDocuments.TABLE} pd ON ps.{S.ProjectSections.PROJECT_DOCUMENT_ID} = pd.{S.ProjectDocuments.PROJECT_DOCUMENT_ID} WHERE {S.ProjectClauses.TABLE}.{S.ProjectClauses.PROJECT_SECTION_ID} = ps.{S.ProjectSections.PROJECT_SECTION_ID} AND pd.{S.ProjectDocuments.PROJECT_ID} = ?)", (project_id,))
        cursor.execute(f"DELETE FROM {S.ProjectSections.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ProjectDocuments.TABLE} pd WHERE {S.ProjectSections.TABLE}.{S.ProjectSections.PROJECT_DOCUMENT_ID} = pd.{S.ProjectDocuments.PROJECT_DOCUMENT_ID} AND pd.{S.ProjectDocuments.PROJECT_ID} = ?)", (project_id,))
        cursor.execute(f"DELETE FROM {S.DocumentRevisions.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ProjectDocuments.TABLE} pd WHERE {S.DocumentRevisions.TABLE}.{S.DocumentRevisions.PROJECT_DOCUMENT_ID} = pd.{S.ProjectDocuments.PROJECT_DOCUMENT_ID} AND pd.{S.ProjectDocuments.PROJECT_ID} = ?)", (project_id,))
        cursor.execute(f"DELETE FROM {S.PublishedFiles.TABLE} WHERE EXISTS (SELECT 1 FROM {S.DocumentRevisions.TABLE} dr INNER JOIN {S.ProjectDocuments.TABLE} pd ON dr.{S.DocumentRevisions.PROJECT_DOCUMENT_ID} = pd.{S.ProjectDocuments.PROJECT_DOCUMENT_ID} WHERE {S.PublishedFiles.TABLE}.{S.PublishedFiles.REVISION_ID} = dr.{S.DocumentRevisions.REVISION_ID} AND pd.{S.ProjectDocuments.PROJECT_ID} = ?)", (project_id,))
        cursor.execute(f"DELETE FROM {S.ProjectDocuments.TABLE} WHERE {S.ProjectDocuments.PROJECT_ID} = ?", (project_id,))
        
        # Clause assignments
        cursor.execute(f"DELETE FROM {S.ClauseAssignments.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ProjectClauses.TABLE} pc INNER JOIN {S.ProjectSections.TABLE} ps ON pc.{S.ProjectClauses.PROJECT_SECTION_ID} = ps.{S.ProjectSections.PROJECT_SECTION_ID} INNER JOIN {S.ProjectDocuments.TABLE} pd ON ps.{S.ProjectSections.PROJECT_DOCUMENT_ID} = pd.{S.ProjectDocuments.PROJECT_DOCUMENT_ID} WHERE {S.ClauseAssignments.TABLE}.{S.ClauseAssignments.PROJECT_CLAUSE_ID} = pc.{S.ProjectClauses.PROJECT_CLAUSE_ID} AND pd.{S.ProjectDocuments.PROJECT_ID} = ?)", (project_id,))
        
        # Service-related data
        cursor.execute(f"DELETE FROM {S.ServiceReviews.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ProjectServices.TABLE} ps WHERE ps.{S.ProjectServices.SERVICE_ID} = {S.ServiceReviews.TABLE}.{S.ServiceReviews.SERVICE_ID} AND ps.{S.ProjectServices.PROJECT_ID} = ?)", (project_id,))
        cursor.execute(f"DELETE FROM {S.ServiceScheduleSettings.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ProjectServices.TABLE} ps WHERE ps.{S.ProjectServices.SERVICE_ID} = {S.ServiceScheduleSettings.TABLE}.{S.ServiceScheduleSettings.SERVICE_ID} AND ps.{S.ProjectServices.PROJECT_ID} = ?)", (project_id,))
        cursor.execute(f"DELETE FROM {S.ServiceDeliverables.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ProjectServices.TABLE} ps WHERE ps.{S.ProjectServices.SERVICE_ID} = {S.ServiceDeliverables.TABLE}.{S.ServiceDeliverables.SERVICE_ID} AND ps.{S.ProjectServices.PROJECT_ID} = ?)", (project_id,))
        cursor.execute(f"DELETE FROM {S.ProjectServices.TABLE} WHERE {S.ProjectServices.PROJECT_ID} = ?", (project_id,))
        
        # Billing data
        cursor.execute(f"DELETE FROM {S.BillingClaimLines.TABLE} WHERE EXISTS (SELECT 1 FROM {S.BillingClaims.TABLE} bc WHERE {S.BillingClaimLines.TABLE}.{S.BillingClaimLines.CLAIM_ID} = bc.{S.BillingClaims.CLAIM_ID} AND bc.{S.BillingClaims.PROJECT_ID} = ?)", (project_id,))
        cursor.execute(f"DELETE FROM {S.BillingClaims.TABLE} WHERE {S.BillingClaims.PROJECT_ID} = ?", (project_id,))
        
        # Review and task data
        cursor.execute(f"DELETE FROM {S.ReviewAssignments.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ReviewSchedule.TABLE} rs WHERE {S.ReviewAssignments.TABLE}.{S.ReviewAssignments.SCHEDULE_ID} = rs.{S.ReviewSchedule.SCHEDULE_ID} AND rs.{S.ReviewSchedule.PROJECT_ID} = ?)", (project_id,))
        cursor.execute(f"DELETE FROM {S.ReviewTasks.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ReviewSchedule.TABLE} rs WHERE {S.ReviewTasks.TABLE}.{S.ReviewTasks.SCHEDULE_ID} = rs.{S.ReviewSchedule.SCHEDULE_ID} AND rs.{S.ReviewSchedule.PROJECT_ID} = ?)", (project_id,))
        cursor.execute(f"DELETE FROM {S.ReviewSchedule.TABLE} WHERE {S.ReviewSchedule.PROJECT_ID} = ?", (project_id,))
        cursor.execute(f"DELETE FROM {S.ReviewSchedules.TABLE} WHERE {S.ReviewSchedules.PROJECT_ID} = ?", (project_id,))
        cursor.execute(f"DELETE FROM {S.ReviewCycleDetails.TABLE} WHERE {S.ReviewCycleDetails.PROJECT_ID} = ?", (project_id,))
        cursor.execute(f"DELETE FROM {S.ReviewStages.TABLE} WHERE {S.ReviewStages.PROJECT_ID} = ?", (project_id,))
        cursor.execute(f"DELETE FROM {S.ReviewParameters.TABLE} WHERE {S.ReviewParameters.PROJECT_ID} = ?", (project_id,))
        cursor.execute(f"DELETE FROM {S.ContractualLinks.TABLE} WHERE {S.ContractualLinks.PROJECT_ID} = ?", (project_id,))
        
        # Project phases and reviews
        cursor.execute(f"DELETE FROM {S.ProjectReviews.TABLE} WHERE {S.ProjectReviews.PROJECT_ID} = ?", (project_id,))
        cursor.execute(f"DELETE FROM {S.ProjectReviewCycles.TABLE} WHERE {S.ProjectReviewCycles.PROJECT_ID} = ?", (project_id,))
        cursor.execute(f"DELETE FROM {S.ProjectHolds.TABLE} WHERE {S.ProjectHolds.PROJECT_ID} = ?", (project_id,))
        cursor.execute(f"DELETE FROM {S.ProjectBEPSections.TABLE} WHERE {S.ProjectBEPSections.PROJECT_ID} = ?", (project_id,))
        
        # BEP approvals
        cursor.execute(f"DELETE FROM {S.BEPApprovals.TABLE} WHERE {S.BEPApprovals.PROJECT_ID} = ?", (project_id,))
        
        # Tasks
        cursor.execute(f"DELETE FROM {S.Tasks.TABLE} WHERE {S.Tasks.PROJECT_ID} = ?", (project_id,))
        
        # Bookmarks
        cursor.execute(f"DELETE FROM {S.ProjectBookmarks.TABLE} WHERE {S.ProjectBookmarks.PROJECT_ID} = ?", (project_id,))
        
        # ACC and document data
        cursor.execute(f"DELETE FROM {S.ACCImportLogs.TABLE} WHERE {S.ACCImportLogs.PROJECT_ID} = ?", (project_id,))
        cursor.execute(f"DELETE FROM {S.ACCImportFolders.TABLE} WHERE {S.ACCImportFolders.PROJECT_ID} = ?", (project_id,))
        cursor.execute(f"DELETE FROM {S.ACCDocs.TABLE} WHERE {S.ACCDocs.PROJECT_ID} = ?", (project_id,))
        
        # Finally, delete the project itself
        cursor.execute(f"DELETE FROM {S.Projects.TABLE} WHERE {S.Projects.ID} = ?", (project_id,))
        
        conn.commit()
        print(f"✅ Project {project_id} and all related data deleted successfully.")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting project {project_id}: {e}")
        conn.rollback()
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


def delete_project_service(service_id: int) -> bool:
    """Delete a single project service and all related data"""
    conn = connect_to_db()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        # Delete in order of dependencies (child tables first)

        # Service-related data
        cursor.execute(f"DELETE FROM {S.ServiceReviews.TABLE} WHERE {S.ServiceReviews.SERVICE_ID} = ?", (service_id,))
        cursor.execute(f"DELETE FROM {S.ServiceScheduleSettings.TABLE} WHERE {S.ServiceScheduleSettings.SERVICE_ID} = ?", (service_id,))
        cursor.execute(f"DELETE FROM {S.ServiceDeliverables.TABLE} WHERE {S.ServiceDeliverables.SERVICE_ID} = ?", (service_id,))

        # Finally delete the service itself
        cursor.execute(f"DELETE FROM {S.ProjectServices.TABLE} WHERE {S.ProjectServices.SERVICE_ID} = ?", (service_id,))

        conn.commit()
        return True

    except Exception as e:
        print(f"❌ Error deleting project service: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_current_month_activities(project_id):
    """Get current month review activities for a project"""
    from datetime import datetime
    conn = connect_to_db()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        current_month = datetime.now().month
        current_year = datetime.now().year

        # Get reviews scheduled for current month
        cursor.execute(
            f"""
            SELECT rs.{S.ReviewSchedule.REVIEW_DATE}, rs.{S.ReviewSchedule.STATUS},
                   rcd.{S.ReviewCycleDetails.CONSTRUCTION_STAGE}, rcd.{S.ReviewCycleDetails.REVIEWS_PER_PHASE}
            FROM {S.ReviewSchedule.TABLE} rs
            LEFT JOIN {S.ReviewCycleDetails.TABLE} rcd ON rs.{S.ReviewSchedule.CYCLE_ID} = rcd.{S.ReviewCycleDetails.CYCLE_ID}
            WHERE rs.{S.ReviewSchedule.PROJECT_ID} = ?
            AND MONTH(rs.{S.ReviewSchedule.REVIEW_DATE}) = ?
            AND YEAR(rs.{S.ReviewSchedule.REVIEW_DATE}) = ?
            ORDER BY rs.{S.ReviewSchedule.REVIEW_DATE}
            """,
            (project_id, current_month, current_year)
        )

        activities = []
        for row in cursor.fetchall():
            activities.append({
                'review_date': row[0],
                'status': row[1] or 'Scheduled',
                'stage': row[2] or 'Unknown',
                'reviews_per_phase': row[3] or 1
            })

        return activities
    except Exception as e:
        print(f"❌ Error getting current month activities: {e}")
        return []
    finally:
        conn.close()


def get_current_month_billing(project_id):
    """Get billing amounts due for current month"""
    from datetime import datetime
    conn = connect_to_db()
    if conn is None:
        return 0

    try:
        cursor = conn.cursor()
        current_month = datetime.now().month
        current_year = datetime.now().year

        # Get billing claims for current month
        cursor.execute(
            f"""
            SELECT SUM(bcl.{S.BillingClaimLines.AMOUNT_THIS_CLAIM})
            FROM {S.BillingClaims.TABLE} bc
            JOIN {S.BillingClaimLines.TABLE} bcl ON bc.{S.BillingClaims.CLAIM_ID} = bcl.{S.BillingClaimLines.CLAIM_ID}
            WHERE bc.{S.BillingClaims.PROJECT_ID} = ?
            AND MONTH(bc.{S.BillingClaims.PERIOD_END}) = ?
            AND YEAR(bc.{S.BillingClaims.PERIOD_END}) = ?
            AND bc.{S.BillingClaims.STATUS} IN ('Pending', 'Approved')
            """,
            (project_id, current_month, current_year)
        )

        result = cursor.fetchone()
        return result[0] if result[0] else 0
    except Exception as e:
        print(f"❌ Error getting current month billing: {e}")
        return 0
    finally:
        conn.close()


def get_scope_remaining(project_id):
    """Get remaining scope (upcoming reviews)"""
    from datetime import datetime
    conn = connect_to_db()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        today = datetime.now().date()

        # Get upcoming reviews
        cursor.execute(
            f"""
            SELECT rs.{S.ReviewSchedule.REVIEW_DATE}, rcd.{S.ReviewCycleDetails.CONSTRUCTION_STAGE},
                   rs.{S.ReviewSchedule.STATUS}
            FROM {S.ReviewSchedule.TABLE} rs
            LEFT JOIN {S.ReviewCycleDetails.TABLE} rcd ON rs.{S.ReviewSchedule.CYCLE_ID} = rcd.{S.ReviewCycleDetails.CYCLE_ID}
            WHERE rs.{S.ReviewSchedule.PROJECT_ID} = ?
            AND rs.{S.ReviewSchedule.REVIEW_DATE} >= ?
            AND rs.{S.ReviewSchedule.STATUS} NOT IN ('Completed', 'Cancelled')
            ORDER BY rs.{S.ReviewSchedule.REVIEW_DATE}
            """,
            (project_id, today)
        )

        reviews = []
        for row in cursor.fetchall():
            reviews.append({
                'date': row[0],
                'stage': row[1] or 'Unknown',
                'status': row[2] or 'Scheduled'
            })

        return reviews
    except Exception as e:
        print(f"❌ Error getting scope remaining: {e}")
        return []
    finally:
        conn.close()


def get_project_completion_estimate(project_id):
    """Get estimated project completion dates"""
    conn = connect_to_db()
    if conn is None:
        return {'phase_completion': None, 'project_completion': None}

    try:
        cursor = conn.cursor()

        # Get the latest review cycle details for completion estimates
        cursor.execute(
            f"""
            SELECT TOP 1 rcd.{S.ReviewCycleDetails.PLANNED_COMPLETION_DATE},
                   p.{S.Projects.END_DATE}
            FROM {S.ReviewCycleDetails.TABLE} rcd
            JOIN {S.Projects.TABLE} p ON rcd.{S.ReviewCycleDetails.PROJECT_ID} = p.{S.Projects.ID}
            WHERE rcd.{S.ReviewCycleDetails.PROJECT_ID} = ?
            ORDER BY rcd.{S.ReviewCycleDetails.PLANNED_COMPLETION_DATE} DESC
            """,
            (project_id,)
        )

        result = cursor.fetchone()
        if result:
            return {
                'phase_completion': result[0],
                'project_completion': result[1]
            }
        else:
            # Fallback to project end date
            cursor.execute(
                f"SELECT {S.Projects.END_DATE} FROM {S.Projects.TABLE} WHERE {S.Projects.ID} = ?",
                (project_id,)
            )
            result = cursor.fetchone()
            return {
                'phase_completion': None,
                'project_completion': result[0] if result else None
            }
    except Exception as e:
        print(f"❌ Error getting project completion estimate: {e}")
        return {'phase_completion': None, 'project_completion': None}
    finally:
        conn.close()


def get_project_details_summary(project_id):
    """Get comprehensive project details summary for the UI"""
    from datetime import datetime

    activities = get_current_month_activities(project_id)
    billing = get_current_month_billing(project_id)
    scope = get_scope_remaining(project_id)
    completion = get_project_completion_estimate(project_id)

    # Process activities for current month
    current_month_reviews = []
    for activity in activities:
        if activity['stage'].lower().startswith('phase 7'):
            current_month_reviews.append(f"{activity['reviews_per_phase']} x Phase 7 coordination reviews")

    # Process scope remaining
    scope_remaining = []
    phase_7_count = 0
    cupix_count = 0
    pc_report_count = 0

    for review in scope:
        stage = review['stage'].lower()
        if 'phase 7' in stage and 'audit' in stage:
            phase_7_count += 1
        elif 'cupix' in stage:
            cupix_count += 1
        elif 'pc report' in stage or 'progress claim' in stage:
            pc_report_count += 1

    if phase_7_count > 0:
        scope_remaining.append(f"{phase_7_count} x Phase 7 audit")
    if cupix_count > 0:
        scope_remaining.append(f"{cupix_count} x Cupix Reviews")
    if pc_report_count > 0:
        scope_remaining.append(f"{pc_report_count} x PC Report")

    # Format completion dates
    phase_completion = None
    project_completion = None

    if completion['phase_completion']:
        phase_completion = completion['phase_completion'].strftime('%B %Y')

    if completion['project_completion']:
        project_completion = completion['project_completion'].strftime('%B %Y')

    return {
        'current_activities': current_month_reviews,
        'billing_amount': billing,
        'scope_remaining': scope_remaining,
        'phase_completion': phase_completion,
        'project_completion': project_completion
    }




# ===================== Revizto Extraction Run Functions =====================

def start_revizto_extraction_run(export_folder=None, notes=None):
    """Start a new Revizto extraction run and return the run_id."""
    from datetime import datetime
    conn = connect_to_db()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        # Generate a run_id based on timestamp
        run_id = f"run_{int(datetime.utcnow().timestamp())}"
        
        cursor.execute(
            f"""
            INSERT INTO {S.ReviztoExtractionRuns.TABLE} (
                {S.ReviztoExtractionRuns.RUN_ID},
                {S.ReviztoExtractionRuns.START_TIME},
                {S.ReviztoExtractionRuns.STATUS},
                {S.ReviztoExtractionRuns.EXPORT_FOLDER},
                {S.ReviztoExtractionRuns.NOTES}
            ) VALUES (?, GETUTCDATE(), 'running', ?, ?);
            """,
            (run_id, export_folder, notes)
        )
        
        conn.commit()
        return run_id
    except Exception as e:
        print(f"❌ Error starting Revizto extraction run: {e}")
        return None
    finally:
        conn.close()


def complete_revizto_extraction_run(run_id, projects_extracted=0, issues_extracted=0, licenses_extracted=0, status='completed'):
    """Complete a Revizto extraction run with final statistics."""
    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {S.ReviztoExtractionRuns.TABLE}
            SET {S.ReviztoExtractionRuns.END_TIME} = GETUTCDATE(),
                {S.ReviztoExtractionRuns.STATUS} = ?,
                {S.ReviztoExtractionRuns.PROJECTS_EXTRACTED} = ?,
                {S.ReviztoExtractionRuns.ISSUES_EXTRACTED} = ?,
                {S.ReviztoExtractionRuns.LICENSES_EXTRACTED} = ?
            WHERE {S.ReviztoExtractionRuns.RUN_ID} = ?;
            """,
            (status, projects_extracted, issues_extracted, licenses_extracted, run_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error completing Revizto extraction run: {e}")
        return False
    finally:
        conn.close()


def get_revizto_extraction_runs(limit=50):
    """Get recent Revizto extraction runs."""
    conn = connect_to_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {S.ReviztoExtractionRuns.RUN_ID},
                   {S.ReviztoExtractionRuns.START_TIME},
                   {S.ReviztoExtractionRuns.END_TIME},
                   {S.ReviztoExtractionRuns.STATUS},
                   {S.ReviztoExtractionRuns.PROJECTS_EXTRACTED},
                   {S.ReviztoExtractionRuns.ISSUES_EXTRACTED},
                   {S.ReviztoExtractionRuns.LICENSES_EXTRACTED},
                   {S.ReviztoExtractionRuns.EXPORT_FOLDER},
                   {S.ReviztoExtractionRuns.NOTES}
            FROM {S.ReviztoExtractionRuns.TABLE}
            ORDER BY {S.ReviztoExtractionRuns.START_TIME} DESC
            OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY;
            """,
            (limit,)
        )
        runs = []
        for row in cursor.fetchall():
            runs.append({
                'run_id': row[0],
                'start_time': row[1],
                'end_time': row[2],
                'status': row[3],
                'projects_extracted': row[4] or 0,
                'issues_extracted': row[5] or 0,
                'licenses_extracted': row[6] or 0,
                'export_folder': row[7],
                'notes': row[8]
            })
        return runs
    except Exception as e:
        print(f"❌ Error fetching Revizto extraction runs: {e}")
        return []
    finally:
        conn.close()


def get_last_revizto_extraction_run():
    """Get the most recent completed Revizto extraction run."""
    conn = connect_to_db()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT TOP 1 {S.ReviztoExtractionRuns.RUN_ID},
                   {S.ReviztoExtractionRuns.START_TIME},
                   {S.ReviztoExtractionRuns.END_TIME},
                   {S.ReviztoExtractionRuns.STATUS},
                   {S.ReviztoExtractionRuns.PROJECTS_EXTRACTED},
                   {S.ReviztoExtractionRuns.ISSUES_EXTRACTED},
                   {S.ReviztoExtractionRuns.LICENSES_EXTRACTED},
                   {S.ReviztoExtractionRuns.EXPORT_FOLDER},
                   {S.ReviztoExtractionRuns.NOTES}
            FROM {S.ReviztoExtractionRuns.TABLE}
            WHERE {S.ReviztoExtractionRuns.STATUS} = 'completed'
            ORDER BY {S.ReviztoExtractionRuns.START_TIME} DESC;
            """
        )
        row = cursor.fetchone()
        if row:
            return {
                'run_id': row[0],
                'start_time': row[1],
                'end_time': row[2],
                'status': row[3],
                'projects_extracted': row[4] or 0,
                'issues_extracted': row[5] or 0,
                'licenses_extracted': row[6] or 0,
                'export_folder': row[7],
                'notes': row[8]
            }
        return None
    except Exception as e:
        print(f"❌ Error fetching last Revizto extraction run: {e}")
        return None
    finally:
        conn.close()


def get_revizto_projects_since_last_run():
    """Get Revizto projects that have been updated since the last extraction run."""
    last_run = get_last_revizto_extraction_run()
    if not last_run or not last_run['end_time']:
        # If no previous run, return all projects
        return get_revizto_projects()

    conn = connect_to_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {S.TblReviztoProjects.PROJECT_ID},
                   {S.TblReviztoProjects.PROJECT_UUID},
                   {S.TblReviztoProjects.TITLE},
                   {S.TblReviztoProjects.CREATED},
                   {S.TblReviztoProjects.UPDATED},
                   {S.TblReviztoProjects.REGION},
                   {S.TblReviztoProjects.ARCHIVED},
                   {S.TblReviztoProjects.FROZEN},
                   {S.TblReviztoProjects.OWNER_EMAIL}
            FROM {S.TblReviztoProjects.TABLE}
            WHERE {S.TblReviztoProjects.UPDATED} > ?
            ORDER BY {S.TblReviztoProjects.UPDATED} DESC;
            """,
            (last_run['end_time'],)
        )
        projects = []
        for row in cursor.fetchall():
            projects.append({
                'project_id': row[0],
                'project_uuid': row[1],
                'title': row[2],
                'created': row[3],
                'updated': row[4],
                'region': row[5],
                'archived': row[6],
                'frozen': row[7],
                'owner_email': row[8]
            })
        return projects
    except Exception as e:
        print(f"❌ Error fetching Revizto projects since last run: {e}")
        return []
    finally:
        conn.close()


def get_revizto_projects():
    """Get all Revizto projects."""
    conn = connect_to_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {S.TblReviztoProjects.PROJECT_ID},
                   {S.TblReviztoProjects.PROJECT_UUID},
                   {S.TblReviztoProjects.TITLE},
                   {S.TblReviztoProjects.CREATED},
                   {S.TblReviztoProjects.UPDATED},
                   {S.TblReviztoProjects.REGION},
                   {S.TblReviztoProjects.ARCHIVED},
                   {S.TblReviztoProjects.FROZEN},
                   {S.TblReviztoProjects.OWNER_EMAIL}
            FROM {S.TblReviztoProjects.TABLE}
            ORDER BY {S.TblReviztoProjects.TITLE};
            """
        )
        projects = []
        for row in cursor.fetchall():
            projects.append({
                'project_id': row[0],
                'project_uuid': row[1],
                'title': row[2],
                'created': row[3],
                'updated': row[4],
                'region': row[5],
                'archived': row[6],
                'frozen': row[7],
                'owner_email': row[8]
            })
        return projects
    except Exception as e:
        print(f"❌ Error fetching Revizto projects: {e}")
        return []
    finally:
        conn.close()


def get_project_combined_issues_overview(project_id):
    """Get combined ACC and Revizto issues overview for a specific project."""
    conn = connect_to_db()
    if conn is None:
        return {'summary': {}, 'recent_issues': []}
    
    try:
        cursor = conn.cursor()
        
        # Get project name and all its aliases
        cursor.execute(f"""
            SELECT {S.Projects.NAME} FROM {S.Projects.TABLE} WHERE {S.Projects.ID} = ?
        """, (project_id,))
        project_row = cursor.fetchone()
        if not project_row:
            return {'summary': {'total_issues': 0}, 'recent_issues': []}
        
        project_name = project_row[0]
        
        # Get all aliases for this project (including the main project name)
        cursor.execute("""
            SELECT alias_name FROM project_aliases WHERE pm_project_id = ?
        """, (project_id,))
        aliases = [row[0] for row in cursor.fetchall()]
        
        # Include the main project name as well
        all_project_names = [project_name] + aliases
        
        # Create placeholders for the IN clause
        placeholders = ','.join(['?' for _ in all_project_names])
        
        # Get issue summary statistics using all possible project names
        cursor.execute(f"""
            SELECT 
                source,
                status,
                COUNT(*) as count
            FROM vw_ProjectManagement_AllIssues
            WHERE project_name IN ({placeholders})
            GROUP BY source, status
        """, all_project_names)
        
        stats = cursor.fetchall()
        
        # Build summary statistics
        summary = {
            'total_issues': 0,
            'acc_issues': {'total': 0, 'open': 0, 'closed': 0},
            'revizto_issues': {'total': 0, 'open': 0, 'closed': 0},
            'overall': {'open': 0, 'closed': 0}
        }
        
        for source, status, count in stats:
            summary['total_issues'] += count
            if source == 'ACC':
                summary['acc_issues']['total'] += count
                summary['acc_issues'][status] = count
            elif source == 'Revizto':
                summary['revizto_issues']['total'] += count
                summary['revizto_issues'][status] = count
            
            summary['overall'][status] = summary['overall'].get(status, 0) + count
        
        # Get recent issues (last 10) - use all project names
        cursor.execute(f"""
            SELECT TOP 10
                source,
                issue_id,
                title,
                status,
                created_at,
                assignee,
                priority
            FROM vw_ProjectManagement_AllIssues
            WHERE project_name IN ({placeholders})
            ORDER BY created_at DESC
        """, all_project_names)
        
        recent_issues = []
        for row in cursor.fetchall():
            recent_issues.append({
                'source': row[0],
                'issue_id': row[1],
                'title': row[2],
                'status': row[3],
                'created_at': row[4],
                'assignee': row[5],
                'priority': row[6]
            })
        
        return {
            'summary': summary,
            'recent_issues': recent_issues
        }
        
    except Exception as e:
        print(f"❌ Error fetching project issues overview: {e}")
        return {'summary': {}, 'recent_issues': []}
    finally:
        conn.close()


def get_project_issues_by_status(project_id, status='open'):
    """Get all issues for a project filtered by status."""
    conn = connect_to_db()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        
        # Get project name and all its aliases
        cursor.execute(f"""
            SELECT {S.Projects.NAME} FROM {S.Projects.TABLE} WHERE {S.Projects.ID} = ?
        """, (project_id,))
        project_row = cursor.fetchone()
        if not project_row:
            return []
        
        project_name = project_row[0]
        
        # Get all aliases for this project
        cursor.execute("""
            SELECT alias_name FROM project_aliases WHERE pm_project_id = ?
        """, (project_id,))
        aliases = [row[0] for row in cursor.fetchall()]
        
        # Include the main project name as well
        all_project_names = [project_name] + aliases
        
        # Create placeholders for the IN clause
        placeholders = ','.join(['?' for _ in all_project_names])
        
        cursor.execute(f"""
            SELECT 
                source,
                issue_id,
                title,
                status,
                created_at,
                closed_at,
                assignee,
                author,
                priority,
                web_link
            FROM vw_ProjectManagement_AllIssues
            WHERE project_name IN ({placeholders}) AND status = ?
            ORDER BY created_at DESC
        """, all_project_names + [status])
        
        issues = []
        for row in cursor.fetchall():
            issues.append({
                'source': row[0],
                'issue_id': row[1],
                'title': row[2],
                'status': row[3],
                'created_at': row[4],
                'closed_at': row[5],
                'assignee': row[6],
                'author': row[7],
                'priority': row[8],
                'web_link': row[9]
            })
        
        return issues
        
    except Exception as e:
        print(f"❌ Error fetching project issues by status: {e}")
        return []
    finally:
        conn.close()
