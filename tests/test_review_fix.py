#!/usr/bin/env python3
"""Test the fixed generate_review_cycles method"""

try:
    from database import connect_to_db
    from review_management_service import ReviewManagementService
    from datetime import datetime, timedelta
    
    print("🔧 Testing FIXED review cycle generation...")
    
    # Test database connection
    db_conn = connect_to_db()
    if db_conn:
        review_service = ReviewManagementService(db_conn)
        
        # Test the fix with specific parameters
        print("\n1. Testing fixed cycle generation with short timeframe...")
        
        # Test case that would previously fail:
        # - 4 cycles requested
        # - Weekly frequency (7 days)
        # - Short end date (only 14 days from start)
        # This should now create exactly 4 cycles, even if they extend beyond end_date
        
        test_service_id = 999  # Use a test service ID
        unit_qty = 4
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 15)  # Only 14 days - would previously cause issues
        frequency = 'weekly'
        
        print(f"  Test parameters:")
        print(f"    - Service ID: {test_service_id}")
        print(f"    - Unit Qty: {unit_qty}")
        print(f"    - Start: {start_date.strftime('%Y-%m-%d')}")
        print(f"    - End: {end_date.strftime('%Y-%m-%d')} (only {(end_date-start_date).days} days)")
        print(f"    - Frequency: {frequency}")
        
        # Generate cycles with the fixed method
        cycles = review_service.generate_review_cycles(
            service_id=test_service_id,
            unit_qty=unit_qty,
            start_date=start_date,
            end_date=end_date,
            cadence=frequency,
            disciplines='Test'
        )
        
        print(f"\n2. Results:")
        print(f"  Generated {len(cycles)} cycles (expected {unit_qty})")
        
        if len(cycles) == unit_qty:
            print(f"  ✅ SUCCESS: Generated exactly {unit_qty} cycles as expected!")
        else:
            print(f"  ❌ FAILURE: Generated {len(cycles)} cycles, expected {unit_qty}")
        
        print(f"\n3. Generated cycle details:")
        for i, cycle in enumerate(cycles):
            planned_date = cycle.get('planned_date', 'N/A')
            cycle_no = cycle.get('cycle_no', 'N/A')
            print(f"    Cycle {cycle_no}: {planned_date}")
        
        # Test 2: Another edge case - 1 cycle
        print(f"\n4. Testing edge case: 1 cycle...")
        single_cycles = review_service.generate_review_cycles(
            service_id=test_service_id + 1,
            unit_qty=1,
            start_date=start_date,
            end_date=end_date,
            cadence=frequency,
            disciplines='Test'
        )
        
        print(f"  Generated {len(single_cycles)} cycles (expected 1)")
        if len(single_cycles) == 1:
            print(f"  ✅ SUCCESS: Single cycle test passed!")
        else:
            print(f"  ❌ FAILURE: Single cycle test failed")
        
        # Test 3: High frequency - bi-weekly
        print(f"\n5. Testing bi-weekly frequency...")
        biweekly_cycles = review_service.generate_review_cycles(
            service_id=test_service_id + 2,
            unit_qty=3,
            start_date=start_date,
            end_date=start_date + timedelta(days=10),  # Very short window
            cadence='bi-weekly',
            disciplines='Test'
        )
        
        print(f"  Generated {len(biweekly_cycles)} cycles (expected 3)")
        if len(biweekly_cycles) == 3:
            print(f"  ✅ SUCCESS: Bi-weekly test passed!")
        else:
            print(f"  ❌ FAILURE: Bi-weekly test failed")
        
        # Clean up test data (delete the test reviews)
        print(f"\n6. Cleaning up test data...")
        for test_id in [test_service_id, test_service_id + 1, test_service_id + 2]:
            review_service.delete_service_reviews(test_id)
        
        db_conn.close()
        print("\n✅ Fix testing completed!")
        
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()