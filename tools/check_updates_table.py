"""Quick script to check if project_updates table exists."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

def check_table():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'project_updates'
        """)
        result = cursor.fetchall()
        
        if result:
            print(f"✓ Table 'project_updates' exists")
            
            # Get columns
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'project_updates'
                ORDER BY ORDINAL_POSITION
            """)
            columns = cursor.fetchall()
            print("\nColumns:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        else:
            print("✗ Table 'project_updates' does NOT exist")

if __name__ == '__main__':
    check_table()
