#!/usr/bin/env python3
"""
Create ServiceItems table for comprehensive service item status tracking.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from review_management_service import ReviewManagementService

def main():
    """Create the ServiceItems table."""
    with get_db_connection() as conn:
        if conn is None:
            print("❌ Failed to connect to database")
            return
        
        rms = ReviewManagementService(conn)
        try:
            rms.create_service_items_table()
            print("✅ ServiceItems table creation completed")
        except Exception as e:
            print(f"❌ Error creating ServiceItems table: {e}")
        finally:
            rms.close()

if __name__ == "__main__":
    main()