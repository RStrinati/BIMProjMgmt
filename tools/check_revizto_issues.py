"""
Check if Revizto issues exist in the database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

print("=" * 70)
print("REVIZTO ISSUES DIAGNOSTIC")
print("=" * 70)

with get_db_connection('ProjectManagement') as conn:
    cursor = conn.cursor()
    
    # 1. Check issues by source in the view
    print("\n1. Issues in vw_ProjectManagement_AllIssues by Source:")
    print("-" * 70)
    cursor.execute("""
        SELECT 
            source,
            COUNT(*) as count
        FROM vw_ProjectManagement_AllIssues
        GROUP BY source
    """)
    
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"   {row[0]}: {row[1]:,} issues")
    else:
        print("   ❌ No issues found in view!")
    
    # 2. Check if Revizto tables exist
    print("\n2. Checking for Revizto-related tables:")
    print("-" * 70)
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME LIKE '%revizto%' OR TABLE_NAME LIKE '%Revizto%'
        ORDER BY TABLE_NAME
    """)
    
    revizto_tables = cursor.fetchall()
    if revizto_tables:
        for table in revizto_tables:
            print(f"   ✓ {table[0]}")
    else:
        print("   ❌ No Revizto tables found!")
    
    # 3. Check Revizto extraction runs
    print("\n3. Checking Revizto extraction run history:")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT TOP 5
                run_id,
                export_folder,
                run_date,
                status,
                total_files,
                notes
            FROM ReviztoExtractionRuns
            ORDER BY run_date DESC
        """)
        
        runs = cursor.fetchall()
        if runs:
            print(f"   Found {len(runs)} recent extraction runs:")
            for run in runs:
                print(f"   - Run #{run[0]}: {run[1]} on {run[2]} - Status: {run[3]} ({run[4]} files)")
        else:
            print("   ⚠️  No extraction runs found in ReviztoExtractionRuns table")
    except Exception as e:
        print(f"   ❌ Error checking extraction runs: {e}")
    
    # 4. Check if there's a Revizto issues table
    print("\n4. Checking for Revizto issues data:")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM ReviztoIssues
        """)
        count = cursor.fetchone()[0]
        print(f"   ReviztoIssues table: {count:,} issues")
        
        if count > 0:
            cursor.execute("""
                SELECT TOP 5
                    issue_id,
                    title,
                    status,
                    project_name
                FROM ReviztoIssues
                ORDER BY created_at DESC
            """)
            sample = cursor.fetchall()
            print("\n   Sample Revizto issues:")
            for issue in sample:
                print(f"   - [{issue[0]}] {issue[1]} ({issue[2]}) - Project: {issue[3]}")
    except Exception as e:
        print(f"   ❌ Error checking ReviztoIssues table: {e}")
    
    # 5. Check view definition
    print("\n5. Checking how vw_ProjectManagement_AllIssues is defined:")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT OBJECT_DEFINITION(OBJECT_ID('vw_ProjectManagement_AllIssues'))
        """)
        view_def = cursor.fetchone()[0]
        
        if view_def:
            # Check if Revizto is mentioned in the view
            lines = view_def.split('\n')
            if 'revizto' in view_def.lower():
                print("   ✓ View definition includes Revizto sources")
                # Extract relevant parts
                for i, line in enumerate(lines):
                    if 'revizto' in line.lower():
                        print(f"   Line {i}: {line.strip()[:100]}")
            else:
                print("   ❌ View definition does NOT include Revizto!")
                print("\n   View appears to query from:")
                if 'FROM' in view_def:
                    from_clauses = [line.strip() for line in lines if 'FROM' in line.upper()]
                    for clause in from_clauses[:3]:
                        print(f"   - {clause}")
    except Exception as e:
        print(f"   ❌ Error getting view definition: {e}")
    
    # 6. Check ACC database for comparison
    print("\n6. Checking ACC issues for comparison:")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT COUNT(*) as acc_count
            FROM vw_ProjectManagement_AllIssues
            WHERE source = 'ACC'
        """)
        acc_count = cursor.fetchone()[0]
        print(f"   ACC issues in view: {acc_count:,}")
    except Exception as e:
        print(f"   ❌ Error checking ACC issues: {e}")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
