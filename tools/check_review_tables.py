#!/usr/bin/env python3
"""Check review cycle related tables schema"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

def check_review_cycle_tables():
    """Check all review cycle related tables"""
    
    db = connect_to_db()
    if not db:
        print("❌ Failed to connect to database")
        return
    
    cursor = db.cursor()
    
    # Get all review-related table names
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME LIKE '%review%' OR TABLE_NAME LIKE '%cycle%'
        ORDER BY TABLE_NAME
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"🔍 Found {len(tables)} review/cycle related tables:")
    
    for table_name in tables:
        print(f"\n📋 {table_name} table schema:")
        
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """)
        
        columns = cursor.fetchall()
        
        if columns:
            for col in columns:
                col_name, data_type, nullable = col
                nullable_str = "NULL" if nullable == 'YES' else "NOT NULL"
                print(f"  📄 {col_name}: {data_type} {nullable_str}")
            
            # Show sample data if exists
            cursor.execute(f"SELECT TOP 3 * FROM {table_name}")
            rows = cursor.fetchall()
            
            if rows:
                print(f"  📊 Sample data ({len(rows)} rows):")
                col_names = [desc[0] for desc in cursor.description]
                for i, row in enumerate(rows):
                    row_dict = dict(zip(col_names, row))
                    print(f"    Row {i+1}: {row_dict}")
            else:
                print(f"  ⚠️ No data in {table_name}")
        else:
            print(f"  ❌ No columns found for {table_name}")
    
    cursor.close()
    db.close()

if __name__ == "__main__":
    check_review_cycle_tables()