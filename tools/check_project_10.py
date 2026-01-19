"""Check if project 10 exists"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT project_id, project_name FROM Projects WHERE project_id = 10")
    result = cursor.fetchone()
    
    if result:
        print(f"✓ Project 10 exists: {result[1]}")
    else:
        print("✗ Project 10 does NOT exist")
        
    # List some projects
    cursor.execute("SELECT TOP 5 project_id, project_name FROM Projects ORDER BY project_id")
    print("\nAvailable projects:")
    for row in cursor.fetchall():
        print(f"  - ID {row[0]}: {row[1]}")
