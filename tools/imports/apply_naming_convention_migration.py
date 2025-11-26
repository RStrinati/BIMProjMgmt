"""
Apply Naming Convention Migration

This script applies the naming_convention column to the clients table.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration():
    """Apply the naming_convention migration to clients table"""
    
    try:
        with get_db_connection(Config.PROJECT_MGMT_DB) as conn:
            cursor = conn.cursor()
            
            logger.info("Applying naming convention migration...")
            
            # Step 1: Add column if it doesn't exist
            logger.info("Checking if naming_convention column exists...")
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'clients' 
                AND COLUMN_NAME = 'naming_convention'
            """)
            
            column_exists = cursor.fetchone()[0] > 0
            
            if not column_exists:
                logger.info("Adding naming_convention column...")
                cursor.execute("""
                    ALTER TABLE dbo.clients 
                    ADD naming_convention NVARCHAR(50) NULL;
                """)
                conn.commit()
                logger.info("✅ Added naming_convention column to clients table")
            else:
                logger.info("ℹ️  naming_convention column already exists")
            
            # Step 2: Add check constraint if it doesn't exist
            logger.info("Checking if check constraint exists...")
            cursor.execute("""
                SELECT COUNT(*) FROM sys.check_constraints 
                WHERE name = 'CK_Clients_NamingConvention'
            """)
            
            constraint_exists = cursor.fetchone()[0] > 0
            
            if not constraint_exists:
                logger.info("Adding check constraint...")
                cursor.execute("""
                    ALTER TABLE dbo.clients
                    ADD CONSTRAINT CK_Clients_NamingConvention 
                    CHECK (naming_convention IN ('AWS', 'SINSW', NULL));
                """)
                conn.commit()
                logger.info("✅ Added naming_convention check constraint")
            else:
                logger.info("ℹ️  Check constraint already exists")
            
            logger.info("✅ Migration applied successfully!")
            
            # Verify the column exists
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'clients' AND COLUMN_NAME = 'naming_convention'
            """)
            
            result = cursor.fetchone()
            if result:
                logger.info(f"✅ Verified: {result[0]} column exists ({result[1]}({result[2]}))")
            else:
                logger.error("❌ Column verification failed")
                return False
            
            # Verify constraint exists
            cursor.execute("""
                SELECT name FROM sys.check_constraints
                WHERE name = 'CK_Clients_NamingConvention'
            """)
            
            constraint = cursor.fetchone()
            if constraint:
                logger.info(f"✅ Verified: Check constraint exists ({constraint[0]})")
            else:
                logger.warning("⚠️ Check constraint verification failed")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_migration():
    """Verify the migration was applied correctly"""
    try:
        with get_db_connection(Config.PROJECT_MGMT_DB) as conn:
            cursor = conn.cursor()
            
            # Check column exists
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'clients' AND COLUMN_NAME = 'naming_convention'
            """)
            
            if cursor.fetchone()[0] == 1:
                logger.info("✅ Column exists")
                return True
            else:
                logger.error("❌ Column does not exist")
                return False
                
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Naming Convention Migration Tool")
    print("=" * 60)
    print()
    
    # Check if already applied
    if verify_migration():
        print("ℹ️  Migration already applied. No action needed.")
    else:
        print("Applying migration...")
        if apply_migration():
            print()
            print("✅ Migration completed successfully!")
            print()
            print("Next steps:")
            print("1. Update UI code to include naming convention field")
            print("2. See docs/NAMING_CONVENTION_INTEGRATION.md for details")
        else:
            print()
            print("❌ Migration failed. Check error messages above.")
            sys.exit(1)
    
    print()
    print("=" * 60)
