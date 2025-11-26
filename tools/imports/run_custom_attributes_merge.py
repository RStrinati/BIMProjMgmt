"""
Run the issues_custom_attributes merge script to sync staging -> dbo.

This will transfer the 421 rows of Building Level, Clash Level, Location, 
and Phase data from staging to dbo.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_pool import get_db_connection

def run_merge():
    """Execute the merge script to sync custom attributes."""
    
    # Read the SQL file
    sql_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                            'sql', 'merge_issues_custom_attributes.sql')
    
    print(f"📄 Reading merge SQL: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # Connect to database
    print("🔌 Connecting to acc_data_schema...")
    
    try:
        with get_db_connection('acc_data_schema') as conn:
            cursor = conn.cursor()
            
            # Check staging counts before
            print("\n📊 BEFORE MERGE:")
            cursor.execute("""
                SELECT COUNT(*) as total, attribute_title
                FROM staging.issues_custom_attributes
                WHERE attribute_title NOT LIKE '%Priority%'
                GROUP BY attribute_title
                ORDER BY attribute_title
            """)
            staging_before = cursor.fetchall()
            for row in staging_before:
                print(f"  Staging - {row[1]}: {row[0]} rows")
            
            cursor.execute("""
                SELECT COUNT(*) as total, attribute_title
                FROM dbo.issues_custom_attributes
                WHERE attribute_title NOT LIKE '%Priority%'
                GROUP BY attribute_title
                ORDER BY attribute_title
            """)
            dbo_before = cursor.fetchall()
            if dbo_before:
                for row in dbo_before:
                    print(f"  DBO - {row[1]}: {row[0]} rows")
            else:
                print(f"  DBO - NO DATA (0 rows)")
            
            # Execute merge
            print("\n🚀 Executing MERGE...")
            cursor.execute(sql_script)
            rows_affected = cursor.rowcount
            conn.commit()
            print(f"✅ MERGE completed - {rows_affected} rows affected")
            
            # Check dbo counts after
            print("\n📊 AFTER MERGE:")
            cursor.execute("""
                SELECT COUNT(*) as total, attribute_title
                FROM dbo.issues_custom_attributes
                WHERE attribute_title NOT LIKE '%Priority%'
                GROUP BY attribute_title
                ORDER BY attribute_title
            """)
            dbo_after = cursor.fetchall()
            for row in dbo_after:
                print(f"  DBO - {row[1]}: {row[0]} rows ✅")
            
            print("\n✅ Custom attributes successfully merged to dbo!")
            return True
            
    except Exception as e:
        print(f"❌ Error during merge: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_merge()
    sys.exit(0 if success else 1)
