"""Check if Quality Register tables exist"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

def check_tables():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check ExpectedModels
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'ExpectedModels'
            """)
            expected_models_exists = cursor.fetchone()[0] > 0
            print(f"{'✅' if expected_models_exists else '❌'} ExpectedModels table exists: {expected_models_exists}")
            
            # Check ExpectedModelAliases
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'ExpectedModelAliases'
            """)
            aliases_exists = cursor.fetchone()[0] > 0
            print(f"{'✅' if aliases_exists else '❌'} ExpectedModelAliases table exists: {aliases_exists}")
            
            # If tables exist, check structure
            if expected_models_exists:
                cursor.execute("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'ExpectedModels'
                    ORDER BY ORDINAL_POSITION
                """)
                columns = [row[0] for row in cursor.fetchall()]
                print(f"\n📋 ExpectedModels columns: {', '.join(columns)}")
            
            if aliases_exists:
                cursor.execute("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'ExpectedModelAliases'
                    ORDER BY ORDINAL_POSITION
                """)
                columns = [row[0] for row in cursor.fetchall()]
                print(f"📋 ExpectedModelAliases columns: {', '.join(columns)}")
            
            return expected_models_exists and aliases_exists
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = check_tables()
    sys.exit(0 if success else 1)
