#!/usr/bin/env python3
"""Test just the stage schedule functionality"""

import importlib
import sys

# Force reload of modules
modules_to_reload = ['review_management_service', 'database']
for module in modules_to_reload:
    if module in sys.modules:
        importlib.reload(sys.modules[module])

try:
    from database import connect_to_db
    from review_management_service import ReviewManagementService
    from datetime import datetime, timedelta
    
    print("Testing stage schedule generation...")
    
    db_conn = connect_to_db()
    review_service = ReviewManagementService(db_conn)
    
    # Check if method exists
    if hasattr(review_service, 'generate_stage_schedule'):
        print("✅ generate_stage_schedule method found")
        
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
        
        result = review_service.generate_stage_schedule(2, sample_stages)
        print(f"Stage schedule generation result: {result}")
        
    else:
        print("❌ generate_stage_schedule method not found")
        print("Available methods:")
        methods = [method for method in dir(review_service) if not method.startswith('_')]
        for method in methods:
            print(f"  - {method}")
    
    db_conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
