#!/usr/bin/env python3
"""Test script to verify review generation functionality"""

try:
    from database import connect_to_db, get_review_cycles
    from review_management_service import ReviewManagementService
    
    print("Testing review cycle display...")
    
    # Test database connection
    db_conn = connect_to_db()
    if db_conn:
        # Test get_review_cycles for project 2
        print("1. Testing get_review_cycles for project 2 (NFPS)...")
        cycles = get_review_cycles(2)
        print(f"Found {len(cycles)} review cycles")
        
        if cycles:
            print("Sample cycles:")
            for i, cycle in enumerate(cycles[:5]):  # Show first 5
                print(f"  Cycle {i+1}: {cycle}")
                
        # Test review service stats
        print("\n2. Testing review service stats...")
        review_service = ReviewManagementService(db_conn)
        stats = review_service.get_project_review_stats(2)
        print(f"Project stats: {stats}")
        
        # Test service reviews query
        print("\n3. Testing service reviews query...")
        service_reviews = review_service.get_service_reviews(2)
        print(f"Found {len(service_reviews)} service reviews")
        
        if service_reviews:
            print("Sample service reviews:")
            for i, review in enumerate(service_reviews[:3]):
                print(f"  Review {i+1}: {review}")
        
        db_conn.close()
    else:
        print("❌ Database connection failed")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
