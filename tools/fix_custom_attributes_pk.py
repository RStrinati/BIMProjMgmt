"""
Fix the issues_custom_attributes table primary key.

PROBLEM: PK is only (issue_id), but it should be (issue_id, attribute_mapping_id, mapped_item_type)
         because each issue can have MULTIPLE custom attributes.

SOLUTION: Drop existing PK, create new composite PK.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import connect_to_db

def fix_primary_key():
    """Fix the primary key constraint on issues_custom_attributes."""
    
    print("🔌 Connecting to acc_data_schema...")
    conn = connect_to_db('acc_data_schema')
    
    if conn is None:
        print("❌ Failed to connect")
        return False
    
    try:
        cursor = conn.cursor()
        
        print("\n📊 Current table state:")
        cursor.execute("SELECT COUNT(*) FROM dbo.issues_custom_attributes")
        count = cursor.fetchone()[0]
        print(f"  Total rows: {count}")
        
        print("\n🗑️  Dropping incorrect PRIMARY KEY constraint...")
        cursor.execute("""
            ALTER TABLE dbo.issues_custom_attributes
            DROP CONSTRAINT PK_issues_custom_attributes
        """)
        print("  ✅ Old PK dropped")
        
        print("\n� Making columns NOT NULL...")
        cursor.execute("""
            ALTER TABLE dbo.issues_custom_attributes
            ALTER COLUMN attribute_mapping_id uniqueidentifier NOT NULL
        """)
        print("  ✅ attribute_mapping_id set to NOT NULL")
        
        cursor.execute("""
            ALTER TABLE dbo.issues_custom_attributes
            ALTER COLUMN mapped_item_type nvarchar(50) NOT NULL
        """)
        print("  ✅ mapped_item_type set to NOT NULL")
        
        print("\n�🔑 Creating new composite PRIMARY KEY...")
        cursor.execute("""
            ALTER TABLE dbo.issues_custom_attributes
            ADD CONSTRAINT PK_issues_custom_attributes
            PRIMARY KEY (issue_id, attribute_mapping_id, mapped_item_type)
        """)
        print("  ✅ New composite PK created: (issue_id, attribute_mapping_id, mapped_item_type)")
        
        conn.commit()
        
        print("\n✅ PRIMARY KEY successfully fixed!")
        print("\nTable can now support multiple custom attributes per issue:")
        print("  - Issue A can have Building Level, Clash Level, Phase, Location")
        print("  - Issue B can have the same attributes")
        print("  - Each (issue, attribute, type) combination is unique")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error fixing primary key: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    success = fix_primary_key()
    sys.exit(0 if success else 1)
