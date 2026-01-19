"""Execute the project updates migration."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

def run_migration():
    sql_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'sql', 'migrations', 'add_project_updates_tables.sql'
    )
    
    print(f"Reading migration from: {sql_file}")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Split by GO statements
    batches = [batch.strip() for batch in sql_content.split('GO') if batch.strip()]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for i, batch in enumerate(batches, 1):
            print(f"\nExecuting batch {i}/{len(batches)}...")
            try:
                cursor.execute(batch)
                conn.commit()
                print(f"✓ Batch {i} completed")
            except Exception as e:
                print(f"✗ Error in batch {i}: {e}")
                return False
    
    print("\n" + "="*50)
    print("Migration completed successfully!")
    print("="*50)
    return True

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
