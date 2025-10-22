"""
Apply naming convention migration to projects table.

This script adds the naming_convention column to the projects table
and updates the vw_projects_full view.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def apply_migration():
    """Apply the naming convention migration to projects table."""
    
    migration_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'sql', 'migrations', 'add_naming_convention_to_projects.sql'
    )
    
    if not os.path.exists(migration_file):
        logger.error(f"❌ Migration file not found: {migration_file}")
        return False
    
    logger.info("=" * 60)
    logger.info("Applying Naming Convention Migration to Projects Table")
    logger.info("=" * 60)
    logger.info("")
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Remove GO statements and split into batches
        # Split by line breaks and manually handle batches
        lines = sql_script.split('\n')
        current_batch = []
        batches = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.upper() == 'GO':
                if current_batch:
                    batches.append('\n'.join(current_batch))
                    current_batch = []
            else:
                current_batch.append(line)
        
        # Add final batch if any
        if current_batch:
            batches.append('\n'.join(current_batch))
        
        with get_db_connection() as conn:
            if not conn:
                logger.error("❌ Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            for i, batch in enumerate(batches, 1):
                batch = batch.strip()
                if not batch or batch.startswith('--'):
                    continue
                    
                try:
                    cursor.execute(batch)
                    conn.commit()
                    
                    # Check for messages
                    if cursor.messages:
                        for message in cursor.messages:
                            # Extract just the message text
                            if isinstance(message, tuple) and len(message) >= 2:
                                msg_text = message[1]
                                if msg_text:
                                    decoded = msg_text.decode('utf-8') if isinstance(msg_text, bytes) else msg_text
                                    logger.info(f"  {decoded}")
                    
                except Exception as e:
                    logger.error(f"❌ Error executing batch {i}: {e}")
                    logger.error(f"   Batch content: {batch[:200]}...")
                    conn.rollback()
                    return False
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Migration Applied Successfully!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Restart the backend server")
        logger.info("  2. Test creating/editing projects with naming conventions")
        logger.info("  3. Verify the naming_convention field persists correctly")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = apply_migration()
    sys.exit(0 if success else 1)
