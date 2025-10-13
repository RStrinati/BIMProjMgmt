#!/usr/bin/env python3
"""
Migration script to add regeneration_signature column to ServiceReviews table
and update existing records
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
import logging

def migrate_regeneration_signature():
    """Add regeneration_signature column and update existing records"""
    
    with get_db_connection() as conn:
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'ServiceReviews' 
            AND COLUMN_NAME = 'regeneration_signature'
        """)
        
        if cursor.fetchone()[0] > 0:
            print("✅ regeneration_signature column already exists")
            return True
        
        print("🔄 Adding regeneration_signature column to ServiceReviews table...")
        
        # Add the column
        cursor.execute("""
            ALTER TABLE ServiceReviews 
            ADD regeneration_signature NVARCHAR(500) NULL
        """)
        
        print("✅ Successfully added regeneration_signature column")
        
        # Initialize existing records with empty signature
        # This will force regeneration check on first run
        cursor.execute("""
            UPDATE ServiceReviews 
            SET regeneration_signature = ''
            WHERE regeneration_signature IS NULL
        """)
        
        updated_rows = cursor.rowcount
        print(f"✅ Initialized {updated_rows} existing records")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:

if __name__ == "__main__":
    success = migrate_regeneration_signature()
    sys.exit(0 if success else 1)