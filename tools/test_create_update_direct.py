"""Directly test create_project_update"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from constants import schema as S

# Test the raw SQL
with get_db_connection() as conn:
    cursor = conn.cursor()
    try:
        print("Attempting INSERT...")
        cursor.execute(f"""
            INSERT INTO {S.ProjectUpdates.TABLE} (
                {S.ProjectUpdates.PROJECT_ID},
                {S.ProjectUpdates.BODY},
                {S.ProjectUpdates.CREATED_BY}
            ) VALUES (?, ?, ?)
        """, (10, "Test direct insert", None))
        
        print("Committing INSERT...")
        conn.commit()
        
        print("Fetching SCOPE_IDENTITY...")
        cursor.execute("SELECT SCOPE_IDENTITY() as update_id")
        result = cursor.fetchone()
        print(f"SCOPE_IDENTITY result: {result}")
        
        if result and result[0]:
            print(f"✓ Successfully created update {int(result[0])}")
        else:
            print(f"✗ Failed - SCOPE_IDENTITY returned: {result}")
            
            # Check if row was actually inserted
            cursor.execute("SELECT TOP 1 update_id, project_id, body FROM project_updates ORDER BY update_id DESC")
            last_row = cursor.fetchone()
            print(f"Last row in table: {last_row}")
            
    except Exception as e:
        print(f"✗ Exception: {e}")
        conn.rollback()


