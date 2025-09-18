#!/usr/bin/env python3
"""Fix missing task table columns"""

import database

def fix_task_schema():
    """Add missing columns to the tasks table"""
    conn = database.connect_to_db()
    if not conn:
        print("❌ Could not connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if columns already exist to avoid duplicate column errors
        columns_to_add = [
            ("priority", "VARCHAR(20) DEFAULT 'Medium'"),
            ("estimated_hours", "DECIMAL(5,2)"),
            ("actual_hours", "DECIMAL(5,2)"),
            ("predecessor_task_id", "INT"),
            ("progress_percentage", "INT DEFAULT 0"),
            ("status", "VARCHAR(50) DEFAULT 'Not Started'"),
            ("description", "NVARCHAR(1000)"),
            ("updated_at", "DATETIME DEFAULT GETDATE()")
        ]
        
        for column_name, column_def in columns_to_add:
            try:
                # Check if column exists
                cursor.execute("""
                    SELECT COUNT(*) FROM sys.columns 
                    WHERE object_id = OBJECT_ID('tasks') AND name = ?
                """, (column_name,))
                
                exists = cursor.fetchone()[0] > 0
                
                if not exists:
                    print(f"Adding column: {column_name}")
                    cursor.execute(f"ALTER TABLE tasks ADD {column_name} {column_def}")
                    conn.commit()
                    print(f"✅ Added column: {column_name}")
                else:
                    print(f"⚠️ Column already exists: {column_name}")
                    
            except Exception as e:
                print(f"❌ Error adding column {column_name}: {e}")
                continue
        
        # Add foreign key constraint if it doesn't exist
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM sys.foreign_keys 
                WHERE name = 'FK_tasks_predecessor'
            """)
            
            fk_exists = cursor.fetchone()[0] > 0
            
            if not fk_exists:
                print("Adding foreign key constraint...")
                cursor.execute("""
                    ALTER TABLE tasks ADD CONSTRAINT FK_tasks_predecessor 
                    FOREIGN KEY (predecessor_task_id) REFERENCES tasks(task_id)
                """)
                conn.commit()
                print("✅ Added foreign key constraint")
            else:
                print("⚠️ Foreign key constraint already exists")
                
        except Exception as e:
            print(f"❌ Error adding foreign key: {e}")
        
        print("✅ Task schema fix completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing task schema: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    fix_task_schema()