#!/usr/bin/env python3
"""Test the new stage schedule method"""

import importlib
import sys

# Force reload
if 'review_management_service' in sys.modules:
    importlib.reload(sys.modules['review_management_service'])

try:
    from database import get_db_connection
    from review_management_service import ReviewManagementService
    from datetime import datetime, timedelta
    
    print("Testing new stage schedule generation...")
    
    with get_db_connection() as db_conn:
        review_service = ReviewManagementService(db_conn)
        
        # Check if new method exists
        if hasattr(review_service, 'generate_stage_schedule_new'):
            print("✅ generate_stage_schedule_new method found")
            
            # Test with sample stages
            sample_stages = [
                {
                    'stage_name': 'Test Stage',
                    'start_date': datetime.now(),
                    'end_date': datetime.now() + timedelta(days=30),
                    'num_reviews': 2,
                    'frequency': 'weekly'
                }
            ]
            
            result = review_service.generate_stage_schedule_new(2, sample_stages)
            print(f"✅ Stage schedule generation result: {result}")
            
        else:
            print("❌ generate_stage_schedule_new method not found")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
