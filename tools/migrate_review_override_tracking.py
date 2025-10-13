"""
Migration script to add status_override tracking to ServiceReviews table

This adds three new columns to support manual status override tracking:
- status_override: BIT flag indicating if status was manually set
- status_override_by: VARCHAR(100) storing who made the manual change
- status_override_at: DATETIME2 storing when the manual change was made

Run this ONCE to add the new columns before deploying the code changes.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection, get_db_connection

def migrate_add_override_columns():
    """Add status_override tracking columns to ServiceReviews"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            print("📋 Checking if columns already exist...")
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'ServiceReviews' 
                AND COLUMN_NAME = 'status_override'
            """)
            
            if cursor.fetchone()[0] > 0:
                print("✅ Columns already exist, migration not needed")
                return True
            
            print("🔧 Adding status_override tracking columns...")
            cursor.execute("""
                ALTER TABLE ServiceReviews
                ADD status_override BIT DEFAULT 0,
                    status_override_by VARCHAR(100),
                    status_override_at DATETIME2;
            """)
            
            conn.commit()
            print("✅ Columns added successfully!")
            
            # Set default values for existing records
            print("🔧 Setting defaults for existing records...")
            cursor.execute("""
                UPDATE ServiceReviews
                SET status_override = 0
                WHERE status_override IS NULL
            """)
            conn.commit()
            
            rows_updated = cursor.rowcount
            print(f"✅ Updated {rows_updated} existing records with default values")
            
            # Verify the changes
            print("\n📋 Verifying new columns...")
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'ServiceReviews' 
                AND COLUMN_NAME IN ('status_override', 'status_override_by', 'status_override_at')
                ORDER BY COLUMN_NAME
            """)
            
            print("\nNew columns:")
            for row in cursor.fetchall():
                print(f"  - {row[0]}: {row[1]} (Nullable: {row[2]}, Default: {row[3]})")
            
            return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def rollback_migration():
    """Rollback the migration (remove columns) - USE WITH CAUTION"""
    print("\n⚠️  WARNING: This will remove the status_override columns!")
    print("⚠️  Any manual override data will be lost!")
    response = input("Are you sure you want to rollback? (type 'YES' to confirm): ")
    
    if response != 'YES':
        print("Rollback cancelled")
        return False
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            print("🔧 Removing status_override tracking columns...")
            cursor.execute("""
                ALTER TABLE ServiceReviews
                DROP COLUMN status_override, status_override_by, status_override_at;
            """)
            
            conn.commit()
            print("✅ Columns removed successfully!")
            return True
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("ServiceReviews Status Override Migration")
    print("=" * 70)
    print("\nThis migration adds manual status override tracking to ServiceReviews.")
    print("This enables users to manually set review statuses that won't be")
    print("overwritten by automatic date-based status calculations.\n")
    
    print("Options:")
    print("  1. Run migration (add columns)")
    print("  2. Rollback migration (remove columns)")
    print("  3. Cancel")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\n" + "=" * 70)
        print("Running Migration...")
        print("=" * 70 + "\n")
        
        result = migrate_add_override_columns()
        
        if result:
            print("\n" + "=" * 70)
            print("🎉 Migration completed successfully!")
            print("=" * 70)
            print("\n✅ Next steps:")
            print("   1. The code changes in review_management_service.py are now compatible")
            print("   2. The code changes in phase1_enhanced_ui.py are now compatible")
            print("   3. Test the implementation with a sample project")
            print("   4. Verify that manual status updates persist after refresh")
        else:
            print("\n" + "=" * 70)
            print("❌ Migration failed - check error messages above")
            print("=" * 70)
    
    elif choice == "2":
        print("\n" + "=" * 70)
        print("Running Rollback...")
        print("=" * 70 + "\n")
        rollback_migration()
    
    else:
        print("\nMigration cancelled")
    
    input("\nPress Enter to exit...")
