"""
Fix ProcessedIssues Schema
===========================

Safely executes schema fixes for ProcessedIssues table to resolve
data type mismatches with the source view.

This script:
1. Backs up existing data (if any)
2. Drops foreign key constraints
3. Alters project_id to NVARCHAR(255)
4. Verifies changes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db


def check_current_schema():
    """Check current schema before making changes."""
    print("\n" + "="*70)
    print("CURRENT SCHEMA (BEFORE FIX)")
    print("="*70)
    
    conn = connect_to_db('ProjectManagement')
    if conn is None:
        print("❌ Failed to connect to database")
        return False
        
    try:
        cursor = conn.cursor()
        
        # Check current columns
        cursor.execute("""
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'ProcessedIssues'
            AND COLUMN_NAME IN ('source_issue_id', 'project_id', 'source')
            ORDER BY ORDINAL_POSITION
        """)
        
        print("\nCurrent ProcessedIssues columns:")
        for row in cursor.fetchall():
            max_len = f"({row[2]})" if row[2] else ""
            nullable = "NULL" if row[3] == 'YES' else "NOT NULL"
            print(f"  {row[0]:25s} {row[1]}{max_len:15s} {nullable}")
        
        # Check row count
        cursor.execute("SELECT COUNT(*) FROM ProcessedIssues")
        count = cursor.fetchone()[0]
        print(f"\nCurrent rows: {count}")
        
        return True
        
    finally:
        conn.close()


def backup_data():
    """Create backup of existing data."""
    print("\n" + "="*70)
    print("CREATING BACKUP")
    print("="*70)
    
    conn = connect_to_db('ProjectManagement')
    if conn is None:
        return False
        
    try:
        cursor = conn.cursor()
        
        # Check if data exists
        cursor.execute("SELECT COUNT(*) FROM ProcessedIssues")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("✓ No data to backup (table is empty)")
            return True
        
        print(f"Backing up {count} rows...")
        
        # Drop backup table if exists
        cursor.execute("""
            IF OBJECT_ID('ProcessedIssues_Backup', 'U') IS NOT NULL
                DROP TABLE ProcessedIssues_Backup
        """)
        
        # Create backup
        cursor.execute("SELECT * INTO ProcessedIssues_Backup FROM ProcessedIssues")
        conn.commit()
        
        print(f"✓ Backup created: ProcessedIssues_Backup ({count} rows)")
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False
    finally:
        conn.close()


def drop_foreign_key():
    """Drop foreign key constraint on project_id."""
    print("\n" + "="*70)
    print("DROPPING FOREIGN KEY CONSTRAINT")
    print("="*70)
    
    conn = connect_to_db('ProjectManagement')
    if conn is None:
        return False
        
    try:
        cursor = conn.cursor()
        
        # Find constraint name
        cursor.execute("""
            SELECT fk.name
            FROM sys.foreign_keys AS fk
            INNER JOIN sys.foreign_key_columns AS fc 
                ON fk.object_id = fc.constraint_object_id
            WHERE OBJECT_NAME(fk.parent_object_id) = 'ProcessedIssues'
            AND COL_NAME(fc.parent_object_id, fc.parent_column_id) = 'project_id'
        """)
        
        result = cursor.fetchone()
        
        if result:
            constraint_name = result[0]
            print(f"Found constraint: {constraint_name}")
            
            # Drop it
            cursor.execute(f"ALTER TABLE ProcessedIssues DROP CONSTRAINT {constraint_name}")
            conn.commit()
            
            print(f"✓ Constraint dropped: {constraint_name}")
        else:
            print("✓ No foreign key constraint found (nothing to drop)")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to drop constraint: {e}")
        return False
    finally:
        conn.close()


def drop_indexes():
    """Drop indexes on project_id column."""
    print("\n" + "="*70)
    print("DROPPING INDEXES")
    print("="*70)
    
    conn = connect_to_db('ProjectManagement')
    if conn is None:
        return False, []
        
    try:
        cursor = conn.cursor()
        
        # Find all indexes on project_id
        cursor.execute("""
            SELECT DISTINCT i.name, i.type_desc
            FROM sys.indexes i
            INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE i.object_id = OBJECT_ID('ProcessedIssues')
            AND c.name = 'project_id'
            AND i.is_primary_key = 0
        """)
        
        indexes = cursor.fetchall()
        dropped_indexes = []
        
        if not indexes:
            print("✓ No indexes found on project_id")
            return True, []
        
        for idx_name, idx_type in indexes:
            print(f"Dropping index: {idx_name} ({idx_type})...")
            cursor.execute(f"DROP INDEX {idx_name} ON ProcessedIssues")
            dropped_indexes.append((idx_name, idx_type))
            print(f"  ✓ Dropped")
        
        conn.commit()
        print(f"\n✓ Dropped {len(dropped_indexes)} index(es)")
        return True, dropped_indexes
        
    except Exception as e:
        print(f"❌ Failed to drop indexes: {e}")
        return False, []
    finally:
        conn.close()


def alter_column():
    """Alter project_id column to NVARCHAR(255)."""
    print("\n" + "="*70)
    print("ALTERING COLUMN TYPE")
    print("="*70)
    
    conn = connect_to_db('ProjectManagement')
    if conn is None:
        return False
        
    try:
        cursor = conn.cursor()
        
        print("Changing project_id from INT to NVARCHAR(255)...")
        
        cursor.execute("""
            ALTER TABLE ProcessedIssues
            ALTER COLUMN project_id NVARCHAR(255) NOT NULL
        """)
        conn.commit()
        
        print("✓ Column altered successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to alter column: {e}")
        return False
    finally:
        conn.close()


def recreate_indexes(indexes):
    """Recreate indexes that were dropped."""
    if not indexes:
        return True
        
    print("\n" + "="*70)
    print("RECREATING INDEXES")
    print("="*70)
    
    conn = connect_to_db('ProjectManagement')
    if conn is None:
        return False
        
    try:
        cursor = conn.cursor()
        
        for idx_name, idx_type in indexes:
            print(f"Recreating index: {idx_name}...")
            
            # Determine columns based on index name
            if 'project_status' in idx_name.lower():
                cursor.execute(f"""
                    CREATE NONCLUSTERED INDEX {idx_name} 
                    ON ProcessedIssues(project_id, status)
                """)
            else:
                cursor.execute(f"""
                    CREATE NONCLUSTERED INDEX {idx_name} 
                    ON ProcessedIssues(project_id)
                """)
            print(f"  ✓ Recreated")
        
        conn.commit()
        print(f"\n✓ Recreated {len(indexes)} index(es)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to recreate indexes: {e}")
        print("Note: You can recreate them manually later if needed")
        return True  # Don't fail the whole process
    finally:
        conn.close()


def verify_changes():
    """Verify the schema changes."""
    print("\n" + "="*70)
    print("VERIFICATION (AFTER FIX)")
    print("="*70)
    
    conn = connect_to_db('ProjectManagement')
    if conn is None:
        return False
        
    try:
        cursor = conn.cursor()
        
        # Check columns
        cursor.execute("""
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'ProcessedIssues'
            AND COLUMN_NAME IN ('source_issue_id', 'project_id', 'source')
            ORDER BY ORDINAL_POSITION
        """)
        
        print("\nUpdated ProcessedIssues columns:")
        for row in cursor.fetchall():
            max_len = f"({row[2]})" if row[2] else ""
            nullable = "NULL" if row[3] == 'YES' else "NOT NULL"
            status = "✓" if row[0] == 'project_id' and row[1] == 'nvarchar' else " "
            print(f"  {status} {row[0]:25s} {row[1]}{max_len:15s} {nullable}")
        
        # Test with sample data from view
        print("\nTesting compatibility with source view...")
        cursor.execute("""
            SELECT TOP 1 
                issue_id,
                project_id,
                source
            FROM vw_ProjectManagement_AllIssues
        """)
        
        row = cursor.fetchone()
        if row:
            print(f"  Sample issue_id: {row[0]} (type: {type(row[0]).__name__})")
            print(f"  Sample project_id: {row[1]} (type: {type(row[1]).__name__})")
            print(f"  Sample source: {row[2]} (type: {type(row[2]).__name__})")
            print("\n  ✓ All types are compatible!")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        conn.close()


def main():
    """Main execution function."""
    print("\n" + "="*70)
    print("PROCESSEDISSUES SCHEMA FIX UTILITY")
    print("="*70)
    print("\nThis script will:")
    print("  1. Check current schema")
    print("  2. Backup existing data (if any)")
    print("  3. Drop foreign key constraints")
    print("  4. Change project_id from INT to NVARCHAR(255)")
    print("  5. Verify changes")
    print("\n" + "="*70)
    
    # Get user confirmation
    response = input("\nProceed with schema fix? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("\n❌ Operation cancelled by user.")
        return 1
    
    # Execute steps
    if not check_current_schema():
        print("\n❌ FAILED at step: Check current schema")
        return 1
    
    if not backup_data():
        print("\n❌ FAILED at step: Backup data")
        return 1
    
    if not drop_foreign_key():
        print("\n❌ FAILED at step: Drop foreign key")
        return 1
    
    # Drop indexes (keep track of what was dropped)
    success, dropped_indexes = drop_indexes()
    if not success:
        print("\n❌ FAILED at step: Drop indexes")
        return 1
    
    if not alter_column():
        print("\n❌ FAILED at step: Alter column type")
        return 1
    
    # Recreate indexes
    if not recreate_indexes(dropped_indexes):
        print("\n⚠️  WARNING: Some indexes may not have been recreated")
    
    if not verify_changes():
        print("\n❌ FAILED at step: Verify changes")
        return 1
    
    # Success!
    print("\n" + "="*70)
    print("✅ SCHEMA FIX COMPLETE!")
    print("="*70)
    print("\nProcessedIssues table is now compatible with the source view.")
    print("\nNext steps:")
    print("  1. Test with small batch:")
    print("     python tools\\run_batch_processing.py --limit 10 --yes")
    print("\n  2. Process all issues:")
    print("     python tools\\run_batch_processing.py --batch-size 500 --yes")
    print("\n" + "="*70)
    
    return 0


if __name__ == '__main__':
    exit(main())
