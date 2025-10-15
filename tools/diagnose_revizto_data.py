"""
Check the ReviztoData database for Revizto issues
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

print("=" * 70)
print("REVIZTO DATA DATABASE CHECK")
print("=" * 70)

# First check if ReviztoData database exists
print("\n1. Checking if ReviztoData database exists:")
print("-" * 70)
try:
    with get_db_connection('master') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name 
            FROM sys.databases 
            WHERE name = 'ReviztoData'
        """)
        result = cursor.fetchone()
        
        if result:
            print(f"   ✓ ReviztoData database EXISTS")
        else:
            print(f"   ❌ ReviztoData database NOT FOUND")
            print("\n   Available databases:")
            cursor.execute("SELECT name FROM sys.databases ORDER BY name")
            for db in cursor.fetchall():
                print(f"      - {db[0]}")
except Exception as e:
    print(f"   ❌ Error checking databases: {e}")

# Check the view that's being queried
print("\n2. Checking vw_ReviztoProjectIssues_Deconstructed:")
print("-" * 70)
try:
    # Try to connect directly to ReviztoData
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Try the view with full path
        cursor.execute("""
            SELECT COUNT(*) 
            FROM ReviztoData.dbo.vw_ReviztoProjectIssues_Deconstructed
        """)
        count = cursor.fetchone()[0]
        print(f"   ✓ View exists with {count:,} issues")
        
        if count > 0:
            print("\n   Sample Revizto issues from view:")
            cursor.execute("""
                SELECT TOP 5
                    issue_id,
                    title,
                    status,
                    project_name
                FROM ReviztoData.dbo.vw_ReviztoProjectIssues_Deconstructed
                ORDER BY created_at DESC
            """)
            for issue in cursor.fetchall():
                print(f"      - [{issue[0]}] {issue[1]} ({issue[2]}) - Project: {issue[3]}")
        else:
            print("\n   ⚠️  View exists but contains NO issues")
            
except Exception as e:
    print(f"   ❌ Error accessing view: {e}")
    
    # Try alternative: check if we can see any ReviztoData tables
    print("\n   Attempting to list ReviztoData tables:")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TABLE_SCHEMA, TABLE_NAME 
                FROM ReviztoData.INFORMATION_SCHEMA.TABLES
                ORDER BY TABLE_NAME
            """)
            tables = cursor.fetchall()
            if tables:
                print(f"   Found {len(tables)} tables in ReviztoData:")
                for schema, table in tables[:10]:
                    print(f"      - {schema}.{table}")
            else:
                print("   No tables found in ReviztoData")
    except Exception as e2:
        print(f"   ❌ Cannot access ReviztoData: {e2}")

# Check the actual Revizto tables in ProjectManagement database
print("\n3. Checking tblReviztoProjectIssues in ProjectManagement:")
print("-" * 70)
try:
    with get_db_connection('ProjectManagement') as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM tblReviztoProjectIssues")
        count = cursor.fetchone()[0]
        print(f"   tblReviztoProjectIssues: {count:,} issues")
        
        if count > 0:
            print("\n   Sample issues:")
            cursor.execute("""
                SELECT TOP 5
                    IssueGUID,
                    Title,
                    StatusDisplay,
                    ProjectNameDisplay
                FROM tblReviztoProjectIssues
            """)
            for issue in cursor.fetchall():
                print(f"      - [{issue[0]}] {issue[1]} ({issue[2]}) - Project: {issue[3]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Get the full view definition to understand the problem
print("\n4. Full view definition:")
print("-" * 70)
try:
    with get_db_connection('ProjectManagement') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT OBJECT_DEFINITION(OBJECT_ID('vw_ProjectManagement_AllIssues'))
        """)
        view_def = cursor.fetchone()[0]
        print(view_def)
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
