#!/usr/bin/env python3
"""Comprehensive test of review management functionality"""

def test_review_generation():
    """Test review generation and stage schedule functionality"""
    try:
        from database import connect_to_db, get_review_cycles
        from review_management_service import ReviewManagementService
        from datetime import datetime, timedelta
        
        print("🔧 Testing Review Management Functionality")
        print("=" * 50)
        
        # Test database connection
        print("\n1. Testing database connection...")
        db_conn = connect_to_db()
        if not db_conn:
            print("❌ Database connection failed")
            return False
        
        print("✅ Database connection successful")
        
        # Initialize review service
        print("\n2. Initializing review service...")
        review_service = ReviewManagementService(db_conn)
        print("✅ Review service initialized")
        
        # Test project 2 (NFPS) - has services
        project_id = 2
        print(f"\n3. Testing with project {project_id} (NFPS)...")
        
        # Check project services
        services = review_service.get_project_services(project_id)
        print(f"✅ Found {len(services)} services")
        
        # Test review generation from services
        print("\n4. Testing review generation from services...")
        reviews = review_service.generate_service_reviews(project_id)
        print(f"✅ Generated {len(reviews)} review cycles")
        
        # Test getting review cycles
        print("\n5. Testing review cycles retrieval...")
        cycles = get_review_cycles(project_id)
        print(f"✅ Retrieved {len(cycles)} review cycles from database")
        
        if cycles:
            print("   Sample cycles:")
            for i, cycle in enumerate(cycles[:3]):
                print(f"     {i+1}. {cycle}")
        
        # Test stage schedule generation
        print("\n6. Testing stage schedule generation...")
        
        # Create sample stages
        sample_stages = [
            {
                'stage_name': 'Design Development',
                'start_date': datetime.now(),
                'end_date': datetime.now() + timedelta(days=30),
                'num_reviews': 3,
                'frequency': 'weekly'
            },
            {
                'stage_name': 'Construction Documentation', 
                'start_date': datetime.now() + timedelta(days=31),
                'end_date': datetime.now() + timedelta(days=60),
                'num_reviews': 2,
                'frequency': 'fortnightly'
            }
        ]
        
        result = review_service.generate_stage_schedule_new(project_id, sample_stages)
        if result:
            print("✅ Stage schedule generation successful")
        else:
            print("❌ Stage schedule generation failed")
        
        # Test final cycles count
        print("\n7. Final verification...")
        final_cycles = get_review_cycles(project_id)
        print(f"✅ Total review cycles after all tests: {len(final_cycles)}")
        
        db_conn.close()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_review_generation()
