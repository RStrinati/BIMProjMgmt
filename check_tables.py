#!/usr/bin/env python3
"""Check database tables"""

from database import connect_to_db

try:
    conn = connect_to_db()
    cursor = conn.cursor()
    
    print("Checking for Project-related tables...")
    cursor.execute("SELECT name FROM sys.tables WHERE name LIKE '%Project%'")
    project_tables = [row[0] for row in cursor.fetchall()]
    print(f"Project tables: {project_tables}")
    
    print("\nChecking for Service-related tables...")
    cursor.execute("SELECT name FROM sys.tables WHERE name LIKE '%Service%'")
    service_tables = [row[0] for row in cursor.fetchall()]
    print(f"Service tables: {service_tables}")
    
    # Check if ProjectServices table exists
    if 'ProjectServices' in project_tables:
        print("\n✅ ProjectServices table exists")
        cursor.execute("SELECT TOP 5 * FROM ProjectServices")
        rows = cursor.fetchall()
        if rows:
            print(f"Found {len(rows)} sample records")
        else:
            print("Table is empty")
    else:
        print("\n❌ ProjectServices table does not exist")
        
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
