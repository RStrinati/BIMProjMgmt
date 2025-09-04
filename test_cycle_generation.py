#!/usr/bin/env python3
"""
Test script for cycle generation functionality
This tests the Generate Cycles button issue
"""

import sqlite3
import os
from datetime import datetime, timedelta
import sys

# Create a simple SQLite database for testing
def create_test_database():
    """Create a simple SQLite database with the required tables"""
    
    if os.path.exists("test_project_data.db"):
        os.remove("test_project_data.db")
    
    conn = sqlite3.connect("test_project_data.db")
    cursor = conn.cursor()
    
    # Create Projects table
    cursor.execute("""
        CREATE TABLE projects (
            project_id INTEGER PRIMARY KEY,
            project_name TEXT NOT NULL,
            client_name TEXT,
            start_date DATE,
            end_date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create ProjectServices table
    cursor.execute("""
        CREATE TABLE ProjectServices (
            service_id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            phase TEXT NOT NULL,
            service_code TEXT NOT NULL,
            service_name TEXT NOT NULL,
            unit_type TEXT NOT NULL,
            unit_qty REAL,
            unit_rate REAL,
            lump_sum_fee REAL,
            agreed_fee REAL,
            bill_rule TEXT,
            status TEXT DEFAULT 'active',
            progress_pct REAL DEFAULT 0,
            claimed_to_date REAL DEFAULT 0,
            notes TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        )
    """)
    
    # Create ServiceReviews table (this is what stores the generated cycles)
    cursor.execute("""
        CREATE TABLE ServiceReviews (
            review_id INTEGER PRIMARY KEY,
            service_id INTEGER NOT NULL,
            cycle_no INTEGER NOT NULL,
            planned_date DATE NOT NULL,
            due_date DATE,
            disciplines TEXT,
            deliverables TEXT,
            status TEXT NOT NULL DEFAULT 'planned',
            weight_factor REAL NOT NULL DEFAULT 1.0,
            evidence_links TEXT,
            actual_issued_at DATETIME,
            FOREIGN KEY (service_id) REFERENCES ProjectServices(service_id)
        )
    """)
    
    # Insert test data
    cursor.execute("""
        INSERT INTO projects (project_id, project_name, client_name, start_date, end_date)
        VALUES (1, 'Test Project', 'Test Client', '2024-01-01', '2024-12-31')
    """)
    
    cursor.execute("""
        INSERT INTO projects (project_id, project_name, client_name, start_date, end_date)
        VALUES (2, 'Demo BIM Project', 'Demo Client', '2024-06-01', '2025-06-01')
    """)
    
    cursor.execute("""
        INSERT INTO ProjectServices (service_id, project_id, phase, service_code, service_name, unit_type, unit_qty, unit_rate, lump_sum_fee, agreed_fee, bill_rule)
        VALUES (1, 1, 'Phase 1', 'REVIEW', 'BIM Coordination Review Cycles', 'review', 5, 1000.0, NULL, 5000.0, 'per_unit_complete')
    """)
    
    cursor.execute("""
        INSERT INTO ProjectServices (service_id, project_id, phase, service_code, service_name, unit_type, unit_qty, unit_rate, lump_sum_fee, agreed_fee, bill_rule)
        VALUES (2, 1, 'Phase 2', 'AUDIT', 'Design Quality Audit', 'audit', 3, 1500.0, NULL, 4500.0, 'on_report_issue')
    """)
    
    conn.commit()
    conn.close()
    print("✅ Test database created: test_project_data.db")

def test_cycle_generation():
    """Test the cycle generation functionality"""
    print("\n🔧 Testing cycle generation...")
    
    # Import the review management service
    try:
        from review_management_service import ReviewManagementService
        
        # Connect to the test database
        conn = sqlite3.connect("test_project_data.db")
        
        # Initialize the service with SQLite connection
        service = ReviewManagementService(conn)
        
        print("✅ ReviewManagementService initialized with SQLite")
        
        # Test getting project services
        services = service.get_project_services(1)
        print(f"✅ Found {len(services)} services for project 1")
        for svc in services:
            print(f"   📋 {svc['service_name']} ({svc['unit_type']}) - {svc['unit_qty']} units")
        
        # Test generating cycles for the first service
        if services:
            service_id = services[0]['service_id']
            unit_qty = int(services[0]['unit_qty'] or 1)
            
            start_date = datetime.now()
            end_date = start_date + timedelta(days=90)
            
            print(f"\n🔄 Generating {unit_qty} cycles for service {service_id}...")
            cycles = service.generate_review_cycles(
                service_id=service_id,
                unit_qty=unit_qty,
                start_date=start_date,
                end_date=end_date,
                cadence='weekly',
                disciplines='Architecture,Structure,Services'
            )
            
            print(f"✅ Generated {len(cycles)} cycles")
            for cycle in cycles:
                print(f"   📅 Cycle {cycle['cycle_no']}: {cycle['planned_date']} → {cycle['due_date']}")
            
            # Test getting the generated cycles back
            print(f"\n📊 Retrieving generated cycles...")
            saved_cycles = service.get_service_reviews(service_id)
            print(f"✅ Retrieved {len(saved_cycles)} saved cycles")
            for cycle in saved_cycles:
                print(f"   📅 Cycle {cycle['cycle_no']}: {cycle['planned_date']} (Status: {cycle['status']})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Cycle generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    print("🚀 Testing Cycle Generation Functionality")
    print("=" * 50)
    
    # Create test database
    create_test_database()
    
    # Test cycle generation
    success = test_cycle_generation()
    
    if success:
        print("\n🎉 Cycle generation test passed!")
        print("\n📋 Next Steps:")
        print("1. Run the UI with this test database")
        print("2. Test the Generate Cycles button")
        print("3. Verify cycles appear in the schedule display")
    else:
        print("\n❌ Cycle generation test failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)