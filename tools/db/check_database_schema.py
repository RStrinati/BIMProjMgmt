#!/usr/bin/env python3
"""Check the actual database schema for ProjectServices table"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

def check_table_schema():
    """Check what columns actually exist in the ProjectServices table"""
    
    db = connect_to_db()
    if not db:
        print("❌ Failed to connect to database")
        return
    
    cursor = db.cursor()
    
    # Get table schema
    print("🔍 Checking ProjectServices table schema...")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'ProjectServices'
        ORDER BY ORDINAL_POSITION
    """)
    
    columns = cursor.fetchall()
    
    print(f"\n📋 ProjectServices table has {len(columns)} columns:")
    for col in columns:
        col_name, data_type, nullable, default = col
        default_str = f" (default: {default})" if default else ""
        nullable_str = "NULL" if nullable == 'YES' else "NOT NULL"
        print(f"  📄 {col_name}: {data_type} {nullable_str}{default_str}")
    
    # Also check ServiceReviews table
    print("\n🔍 Checking ServiceReviews table schema...")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'ServiceReviews'
        ORDER BY ORDINAL_POSITION
    """)
    
    sr_columns = cursor.fetchall()
    
    if sr_columns:
        print(f"\n📋 ServiceReviews table has {len(sr_columns)} columns:")
        for col in sr_columns:
            col_name, data_type, nullable, default = col
            default_str = f" (default: {default})" if default else ""
            nullable_str = "NULL" if nullable == 'YES' else "NOT NULL"
            print(f"  📄 {col_name}: {data_type} {nullable_str}{default_str}")
    else:
        print("\n❌ ServiceReviews table not found or empty")
    
    # Check if there are any related tables
    print("\n🔍 Checking for schedule-related tables...")
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME LIKE '%Schedule%' OR TABLE_NAME LIKE '%Review%'
        ORDER BY TABLE_NAME
    """)
    
    related_tables = cursor.fetchall()
    
    if related_tables:
        print(f"\n📋 Related tables found:")
        for table in related_tables:
            print(f"  📄 {table[0]}")
    else:
        print(f"\n⚠️ No schedule or review related tables found")
    
    cursor.close()
    db.close()

if __name__ == "__main__":
    check_table_schema()