from database import connect_to_db

try:
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Add missing columns to ProjectServices table
    missing_columns = [
        "ALTER TABLE ProjectServices ADD status NVARCHAR(100) DEFAULT 'Active'",
        "ALTER TABLE ProjectServices ADD progress_pct DECIMAL(5,2) DEFAULT 0",
        "ALTER TABLE ProjectServices ADD claimed_to_date DECIMAL(18,2) DEFAULT 0"
    ]
    
    for sql in missing_columns:
        try:
            cursor.execute(sql)
            print(f"✅ Executed: {sql}")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column name" in str(e):
                print(f"ℹ️ Column already exists: {sql}")
            else:
                print(f"❌ Error with {sql}: {e}")
    
    conn.commit()
    print("✅ ProjectServices table updated successfully!")
    
    # Verify the columns exist
    cursor.execute("SELECT TOP 1 * FROM ProjectServices")
    columns = [desc[0] for desc in cursor.description]
    print(f"✅ Current ProjectServices columns: {columns}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')
