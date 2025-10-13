#!/usr/bin/env python3
"""Test stage schedule with all required fields"""

import importlib
import sys

# Force reload
if 'review_management_service' in sys.modules:
    importlib.reload(sys.modules['review_management_service'])

try:
    from database import get_db_connection
    from review_management_service import ReviewManagementService
    from datetime import datetime, timedelta
    
    print("Testing stage schedule with proper fields...")
    
    with get_db_connection() as db_conn:
        review_service = ReviewManagementService(db_conn)
        
        # Test manual service creation first
        print("1. Testing manual service creation...")
        service_data = {
            'project_id': 2,
            'phase': 'Test Stage Manual',
            'service_code': 'STAGE_REVIEW',
            'service_name': 'Test Stage Manual Reviews',
            'unit_type': 'review',
            'unit_qty': 2,
            'unit_rate': 0.0,
            'lump_sum_fee': None,
            'agreed_fee': 0.0,
            'bill_rule': 'on_delivery',
            'notes': 'Auto-generated from stage planning'
        }
        
        service_id = review_service.create_project_service(service_data)
        print(f"✅ Created service with ID: {service_id}")
        
        if service_id:
            # Test review cycle generation
            print("2. Testing review cycle generation...")
            cycles = review_service.generate_review_cycles(
                service_id=service_id,
                unit_qty=2,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
                cadence='weekly',
                disciplines='Test Stage'
            )
            print(f"✅ Generated {len(cycles)} review cycles")
    
    print("✅ Test completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
