"""Check project_updates table structure"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COLUMN_NAME, COLUMN_DEFAULT, IS_NULLABLE, DATA_TYPE, IS_IDENTITY 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'project_updates' 
        ORDER BY ORDINAL_POSITION
    """)
    cols = cursor.fetchall()
    
    print("project_updates table columns:")
    for col in cols:
        print(f"  {col[0]}: {col[1]} {col[2]} {col[3]} IDENTITY={col[4]}")
        
    # Check if IDENTITY is working
    cursor.execute("SELECT IDENT_CURRENT('project_updates') as current_id")
    current_id = cursor.fetchone()
    print(f"\nCurrent IDENTITY value: {current_id[0] if current_id else 'None'}")
    
    # Check if there are any rows
    cursor.execute("SELECT COUNT(*) FROM project_updates")
    count = cursor.fetchone()
    print(f"Total rows in table: {count[0] if count else 0}")
