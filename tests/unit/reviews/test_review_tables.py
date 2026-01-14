#!/usr/bin/env python3
"""Test script to check database tables and review data"""

try:
    from database import get_db_connection
    
    print("Checking review-related tables and data...")
    
    # Test database connection
    with get_db_connection() as db_conn:
        cursor = db_conn.cursor()
        
        # Check ServiceReviews table
        print("\n1. Checking ServiceReviews table:")
        try:
            cursor.execute("SELECT COUNT(*) FROM ServiceReviews")
            count = cursor.fetchone()[0]
            print(f"   Found {count} service reviews")
            
            if count > 0:
                cursor.execute("""
                    SELECT TOP 5 sr.review_id, sr.service_id, ps.service_name, sr.cycle_no, 
                           sr.planned_date, sr.status
                    FROM ServiceReviews sr
                    LEFT JOIN ProjectServices ps ON sr.service_id = ps.service_id
                    ORDER BY sr.review_id DESC
                """)
                reviews = cursor.fetchall()
                print("   Recent reviews:")
                for review in reviews:
                    print(f"     ID: {review[0]}, Service: {review[2]}, Cycle: {review[3]}, Date: {review[4]}, Status: {review[5]}")
                    
        except Exception as e:
            print(f"   Error: {e}")
        
        # Check ReviewCycles table (old schema)
        print("\n2. Checking ReviewCycles table:")
        try:
            cursor.execute("SELECT COUNT(*) FROM ReviewCycles")
            count = cursor.fetchone()[0]
            print(f"   Found {count} review cycles")
            
            if count > 0:
                cursor.execute("SELECT TOP 5 * FROM ReviewCycles ORDER BY review_cycle_id DESC")
                cycles = cursor.fetchall()
                print("   Recent cycles:")
                for cycle in cycles:
                    print(f"     {cycle}")
                    
        except Exception as e:
            print(f"   Error: {e}")
        
        # Check project 2 specifically
        print("\n3. Checking project 2 (NFPS) reviews:")
        try:
            cursor.execute("""
                SELECT sr.review_id, ps.service_name, sr.cycle_no, sr.planned_date, sr.status
                FROM ServiceReviews sr
                LEFT JOIN ProjectServices ps ON sr.service_id = ps.service_id
                WHERE ps.project_id = 2
                ORDER BY sr.planned_date
            """)
            project_reviews = cursor.fetchall()
            print(f"   Found {len(project_reviews)} reviews for project 2:")
            for review in project_reviews:
                print(f"     Service: {review[1]}, Cycle: {review[2]}, Date: {review[3]}, Status: {review[4]}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
