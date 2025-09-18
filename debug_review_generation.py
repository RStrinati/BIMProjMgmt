#!/usr/bin/env python3
"""Debug script to check review cycle generation accuracy"""

try:
    from database import connect_to_db, get_review_cycles
    from review_management_service import ReviewManagementService
    from datetime import datetime, timedelta
    
    print("🔍 Testing review cycle generation accuracy...")
    
    # Test database connection
    db_conn = connect_to_db()
    if db_conn:
        review_service = ReviewManagementService(db_conn)
        
        # Get project 2 (NEPS) services
        print("\n1. Getting NEPS project services...")
        services = review_service.get_project_services(2)
        review_services = [s for s in services if s.get('unit_type') == 'review']
        
        print(f"Found {len(review_services)} review services:")
        for i, service in enumerate(review_services):
            print(f"  Service {i+1}: {service['service_name']}")
            print(f"    - Unit Qty: {service.get('unit_qty', 'None')}")
            print(f"    - Start Date: {service.get('schedule_start', 'None')}")
            print(f"    - End Date: {service.get('schedule_end', 'None')}")
            print(f"    - Frequency: {service.get('schedule_frequency', 'None')}")
        
        # Check current cycles in database
        print("\n2. Checking current review cycles...")
        cycles = get_review_cycles(2)
        print(f"Current cycles in database: {len(cycles)}")
        
        if cycles:
            print("Sample cycles:")
            for i, cycle in enumerate(cycles[:5]):  # Show first 5
                print(f"  Cycle {i+1}: {cycle}")
        
        # Calculate what we should expect
        print("\n3. Calculating expected cycles...")
        total_expected = sum(int(s.get('unit_qty', 0)) for s in review_services)
        print(f"Total expected cycles: {total_expected}")
        
        # Test generation for a specific service if any
        if review_services:
            service = review_services[0]
            service_id = service['service_id']
            unit_qty = int(service.get('unit_qty', 0))
            
            print(f"\n4. Testing generation for service {service_id} (expecting {unit_qty} cycles)...")
            
            # Use service dates or defaults
            if service.get('schedule_start'):
                start_date = datetime.strptime(str(service['schedule_start']), '%Y-%m-%d')
            else:
                start_date = datetime.now()
            
            if service.get('schedule_end'):
                end_date = datetime.strptime(str(service['schedule_end']), '%Y-%m-%d')
            else:
                end_date = start_date + timedelta(days=30)
            
            frequency = service.get('schedule_frequency', 'weekly')
            
            print(f"  Service details:")
            print(f"    - Service ID: {service_id}")
            print(f"    - Expected cycles: {unit_qty}")
            print(f"    - Start: {start_date.strftime('%Y-%m-%d')}")
            print(f"    - End: {end_date.strftime('%Y-%m-%d')}")
            print(f"    - Frequency: {frequency}")
            
            # Test the generation method directly
            test_cycles = review_service.generate_review_cycles(
                service_id=service_id,
                unit_qty=unit_qty,
                start_date=start_date,
                end_date=end_date,
                cadence=frequency,
                disciplines=service.get('phase', 'All')
            )
            
            print(f"  Generated {len(test_cycles)} cycles (expected {unit_qty})")
            
            if len(test_cycles) != unit_qty:
                print(f"  ❌ MISMATCH: Generated {len(test_cycles)} but expected {unit_qty}")
            else:
                print(f"  ✅ CORRECT: Generated exactly {unit_qty} cycles as expected")
            
            # Show the generated cycles
            for i, cycle in enumerate(test_cycles):
                print(f"    Cycle {i+1}: {cycle.get('planned_date')} (cycle_no: {cycle.get('cycle_no')})")
        
        db_conn.close()
        print("\n✅ Debug test completed!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()