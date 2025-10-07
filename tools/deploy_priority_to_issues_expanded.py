"""
Deploy the updated vw_issues_expanded view with Priority column extraction.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db
from config import ACC_DB

def deploy_updated_view():
    """Deploy the updated vw_issues_expanded view."""
    
    sql_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                           'sql', 'update_vw_issues_expanded_with_priority.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL file not found: {sql_file}")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_raw = f.read()
    
    # Remove GO statements and SET statements (not needed for pyodbc)
    sql_lines = sql_raw.split('\n')
    sql_lines = [line for line in sql_lines if not line.strip().upper() in ('GO', 'SET ANSI_NULLS ON', 'SET QUOTED_IDENTIFIER ON')]
    sql = '\n'.join(sql_lines)
    
    print("="*70)
    print("🔧 DEPLOYING UPDATED vw_issues_expanded VIEW")
    print("="*70)
    print(f"\nSQL File: {sql_file}")
    print(f"Database: {ACC_DB}")
    print("\nChanges:")
    print("  ✅ Added Priority column extraction from custom_attributes_json")
    print("  ✅ Fixed syntax errors in SELECT list")
    print("  ✅ Uses OPENJSON to parse JSON array structure")
    
    conn = connect_to_db(ACC_DB)
    if conn is None:
        print("\n❌ Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        print("\n🚀 Executing ALTER VIEW statement...")
        cursor.execute(sql)
        conn.commit()
        print("✅ View updated successfully!")
        
        # Test the Priority column
        print("\n📊 Testing Priority column...")
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_issues,
                COUNT(Priority) AS issues_with_priority
            FROM [dbo].[vw_issues_expanded]
        """)
        
        result = cursor.fetchone()
        print(f"  Total Issues: {result[0]}")
        print(f"  Issues with Priority: {result[1]}")
        
        if result[1] > 0:
            cursor.execute("""
                SELECT TOP 5
                    display_id,
                    Priority,
                    status
                FROM [dbo].[vw_issues_expanded]
                WHERE Priority IS NOT NULL
                ORDER BY created_at DESC
            """)
            
            print("\n  Sample Issues:")
            for row in cursor.fetchall():
                print(f"    Issue {row[0]}: Priority={row[1]}, Status={row[2]}")
        
        print("\n" + "="*70)
        print("✅ DEPLOYMENT SUCCESSFUL!")
        print("="*70)
        print("\nThe Priority column is now available in vw_issues_expanded!")
        print("You can query it like any other column:")
        print("\n  SELECT display_id, title, Priority, status")
        print("  FROM [acc_data_schema].[dbo].[vw_issues_expanded]")
        print("  WHERE Priority = 'Critical'")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error deploying view: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    deploy_updated_view()
