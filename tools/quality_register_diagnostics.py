"""
Quality Register Diagnostics Script
Purpose: Diagnose why /quality/register returns empty rows

Execution:
  cd backend
  python ../tools/quality_register_diagnostics.py <project_id>
  
Example:
  python ../tools/quality_register_diagnostics.py 1
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database_pool import get_db_connection
from constants.schema import Projects, ControlModels, ReviewSchedule
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def diagnose_project(project_id: int):
    """Run diagnostics for a specific project"""
    
    logger.info(f"=== QUALITY REGISTER DIAGNOSTICS FOR PROJECT {project_id} ===\n")
    
    # STEP 1: Verify project exists in Deliver DB
    logger.info("STEP 1: Verify project exists in ProjectManagement DB")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT {Projects.ID}, {Projects.NAME}
                FROM {Projects.TABLE}
                WHERE {Projects.ID} = ?
            """, (project_id,))
            result = cursor.fetchone()
            if result:
                logger.info(f"✓ Project found: ID={result[0]}, Name={result[1]}")
                project_name = result[1]
                project_code = result[1][:10].upper()  # Assume first 10 chars of name
            else:
                logger.error(f"✗ Project {project_id} NOT FOUND")
                return
            cursor.close()
    except Exception as e:
        logger.error(f"✗ Error querying Projects: {e}")
        return
    
    # STEP 2: Check for data in RevitHealthCheckDB vw_LatestRvtFiles
    logger.info("\nSTEP 2: Check vw_LatestRvtFiles in RevitHealthCheckDB")
    try:
        with get_db_connection("RevitHealthCheckDB") as conn:
            cursor = conn.cursor()
            
            # First: see structure of the view
            logger.info("  2a. Checking view structure:")
            cursor.execute("""
                SELECT TOP 5 *
                FROM vw_LatestRvtFiles
            """)
            columns = [desc[0] for desc in cursor.description]
            logger.info(f"     Columns: {', '.join(columns)}")
            cursor.fetchall()
            
            # Second: check for pm_project_id matches
            logger.info(f"\n  2b. Checking for records with pm_project_id = {project_id}:")
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM vw_LatestRvtFiles
                WHERE pm_project_id = ?
            """, (project_id,))
            count_result = cursor.fetchone()
            count = count_result[0] if count_result else 0
            logger.info(f"     Found {count} rows with pm_project_id = {project_id}")
            
            if count == 0:
                # Check if any data matches by project name
                logger.info(f"\n  2c. Checking if any rows match project name '{project_name}':")
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM vw_LatestRvtFiles
                    WHERE strProjectName LIKE ?
                """, (f"%{project_name[:15]}%",))
                name_result = cursor.fetchone()
                logger.info(f"     Found {name_result[0] if name_result else 0} rows matching project name")
                
                # Show sample data to understand structure
                logger.info(f"\n  2d. Sample data from view (first 10 rows):")
                cursor.execute("""
                    SELECT TOP 10
                        pm_project_id,
                        strProjectName,
                        strRvtFileName,
                        DISCIPLINE_FULL_NAME,
                        ConvertedExportedDate
                    FROM vw_LatestRvtFiles
                    ORDER BY ConvertedExportedDate DESC
                """)
                rows = cursor.fetchall()
                for row in rows:
                    logger.info(f"     pm_project_id={row[0]}, project='{row[1]}', file='{row[2]}', disc='{row[3]}', date={row[4]}")
                
                if count == 0:
                    logger.warning(f"\n⚠️  NO DATA FOUND for project {project_id}")
                    logger.info("     Possible causes:")
                    logger.info("     - Project has no Revit models imported")
                    logger.info("     - pm_project_id column doesn't match project_id")
                    logger.info("     - vw_LatestRvtFiles is empty")
            else:
                # Show actual data for this project
                logger.info(f"\n  2e. Showing {min(count, 10)} records for this project:")
                cursor.execute("""
                    SELECT TOP 10
                        pm_project_id,
                        strRvtFileName,
                        DISCIPLINE_FULL_NAME,
                        ConvertedExportedDate,
                        VALIDATION_STATUS
                    FROM vw_LatestRvtFiles
                    WHERE pm_project_id = ?
                    ORDER BY ConvertedExportedDate DESC
                """, (project_id,))
                rows = cursor.fetchall()
                for row in rows:
                    logger.info(f"     file='{row[1]}', disc='{row[2]}', date={row[3]}, validation={row[4]}")
            
            cursor.close()
    except Exception as e:
        logger.error(f"✗ Error querying RevitHealthCheckDB: {e}")
        logger.error(f"  Ensure you can connect to RevitHealthCheckDB via ODBC")
        return
    
    # STEP 3: Check ReviewSchedule data
    logger.info(f"\nSTEP 3: Check ReviewSchedule for next review date")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT TOP 1 {ReviewSchedule.REVIEW_DATE}
                FROM {ReviewSchedule.TABLE}
                WHERE {ReviewSchedule.PROJECT_ID} = ?
                  AND {ReviewSchedule.REVIEW_DATE} > GETDATE()
                ORDER BY {ReviewSchedule.REVIEW_DATE} ASC
            """, (project_id,))
            result = cursor.fetchone()
            if result:
                logger.info(f"✓ Next review date: {result[0]}")
            else:
                logger.warning(f"⚠️  No future review scheduled for project {project_id}")
            cursor.close()
    except Exception as e:
        logger.error(f"✗ Error querying ReviewSchedule: {e}")
    
    # STEP 4: Check ControlModels
    logger.info(f"\nSTEP 4: Check ControlModels")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM {ControlModels.TABLE}
                WHERE {ControlModels.PROJECT_ID} = ?
                  AND {ControlModels.IS_ACTIVE} = 1
            """, (project_id,))
            result = cursor.fetchone()
            count = result[0] if result else 0
            logger.info(f"  Found {count} active control models")
            
            if count > 0:
                cursor.execute(f"""
                    SELECT {ControlModels.CONTROL_FILE_NAME}
                    FROM {ControlModels.TABLE}
                    WHERE {ControlModels.PROJECT_ID} = ?
                      AND {ControlModels.IS_ACTIVE} = 1
                """, (project_id,))
                for row in cursor.fetchall():
                    logger.info(f"  - {row[0]}")
            cursor.close()
    except Exception as e:
        logger.error(f"✗ Error querying ControlModels: {e}")
    
    # STEP 5: Reproduce the exact query from get_model_register
    logger.info(f"\nSTEP 5: Reproduce exact get_model_register query")
    try:
        with get_db_connection("RevitHealthCheckDB") as conn:
            cursor = conn.cursor()
            query = """
            SELECT 
                h.[strRvtFileName],
                h.[strProjectName],
                h.[DISCIPLINE_FULL_NAME],
                h.[strClientName],
                h.[ConvertedExportedDate],
                h.[VALIDATION_STATUS]
            FROM dbo.vw_LatestRvtFiles h
            WHERE h.[pm_project_id] = ?
            ORDER BY h.[ConvertedExportedDate] DESC
            """
            cursor.execute(query, (project_id,))
            rows = cursor.fetchall()
            logger.info(f"  Query returned {len(rows)} rows")
            for i, row in enumerate(rows[:5], 1):
                logger.info(f"  Row {i}: file={row[0]}, project={row[1]}, validation={row[5]}")
            cursor.close()
    except Exception as e:
        logger.error(f"✗ Error in register query: {e}")
    
    logger.info("\n=== DIAGNOSTICS COMPLETE ===")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        logger.error("Usage: python quality_register_diagnostics.py <project_id>")
        sys.exit(1)
    
    try:
        project_id = int(sys.argv[1])
        diagnose_project(project_id)
    except ValueError:
        logger.error(f"Invalid project_id: {sys.argv[1]}")
        sys.exit(1)
