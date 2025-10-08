"""
Update vw_issues_expanded view with all 6 custom attribute columns.

This script executes the SQL file to add:
- Building_Level
- Clash_Level  
- Location
- Location_01
- Phase
- Priority
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db

def update_view():
    """Execute the view update SQL script."""
    
    # Read the SQL file
    sql_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                            'sql', 'update_vw_issues_expanded_with_priority.sql')
    
    print(f"📄 Reading SQL file: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # Connect to database
    print("🔌 Connecting to acc_data_schema database...")
    conn = connect_to_db('acc_data_schema')
    
    if conn is None:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Execute the SQL script in batches (split by GO)
        print("🚀 Executing view update...")
        batches = [batch.strip() for batch in sql_script.split('GO') if batch.strip()]
        
        for i, batch in enumerate(batches, 1):
            print(f"  Executing batch {i}/{len(batches)}...")
            cursor.execute(batch)
        
        conn.commit()
        
        print("✅ View updated successfully!")
        print("\nNew columns available in vw_issues_expanded:")
        print("  - Building_Level")
        print("  - Clash_Level")
        print("  - Location")
        print("  - Location_01")
        print("  - Phase")
        print("  - Priority")
        
        # Test the view
        print("\n🧪 Testing view with sample query...")
        cursor.execute("""
            SELECT TOP 5
                issue_id,
                title,
                Building_Level,
                Clash_Level,
                Location,
                Location_01,
                Phase,
                Priority
            FROM acc_data_schema.dbo.vw_issues_expanded
            WHERE Building_Level IS NOT NULL 
               OR Clash_Level IS NOT NULL
               OR Location IS NOT NULL
               OR Phase IS NOT NULL
               OR Priority IS NOT NULL
        """)
        
        results = cursor.fetchall()
        if results:
            print(f"\n✅ Found {len(results)} issues with custom attributes:")
            for row in results:
                print(f"  Issue: {row[1][:50]}...")
                if row[2]: print(f"    Building Level: {row[2]}")
                if row[3]: print(f"    Clash Level: {row[3]}")
                if row[4]: print(f"    Location: {row[4]}")
                if row[5]: print(f"    Location 01: {row[5]}")
                if row[6]: print(f"    Phase: {row[6]}")
                if row[7]: print(f"    Priority: {row[7]}")
        else:
            print("\n⚠️  No issues found with custom attribute values")
            print("    (This is expected if custom attributes haven't been populated in ACC)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating view: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()
        print("\n🔌 Database connection closed")

if __name__ == '__main__':
    success = update_view()
    sys.exit(0 if success else 1)
