#!/usr/bin/env python3
"""
Simulate the Generate Cycles button functionality to debug the issue
This tests the exact code path without needing a GUI
"""

import sqlite3
import os
from datetime import datetime, timedelta

def simulate_generate_cycles_button():
    """Simulate clicking the Generate Cycles button"""
    print("🔄 Simulating Generate Cycles Button Click...")
    
    try:
        # Import the necessary components
        from review_management_service import ReviewManagementService
        from database import connect_to_db
        
        # Simulate the UI state
        class MockUI:
            def __init__(self):
                # Initialize like the real UI does
                db_conn = connect_to_db()
                if db_conn:
                    self.review_service = ReviewManagementService(db_conn)
                    print("✅ ReviewManagementService initialized (same as UI)")
                else:
                    self.review_service = None
                    print("❌ Failed to initialize ReviewManagementService")
                    return
                
                self.current_project_id = 1  # Simulate project selection
                print(f"✅ Current project ID set to: {self.current_project_id}")
                
                # Simulate the schedule tree
                self.schedule_tree_items = []
            
            def load_project_schedule(self):
                """Simulate the load_project_schedule method"""
                print("\n📊 Loading project schedule (same as UI)...")
                
                # Clear existing items (like UI does)
                self.schedule_tree_items.clear()
                
                if not self.review_service or not self.current_project_id:
                    print("❌ Missing review_service or current_project_id")
                    return
                
                try:
                    services = self.review_service.get_project_services(self.current_project_id)
                    print(f"✅ Found {len(services)} services")
                    
                    for service in services:
                        if service['unit_type'] == 'review':
                            print(f"   📋 Processing review service: {service['service_name']}")
                            reviews = self.review_service.get_service_reviews(service['service_id'])
                            print(f"   📅 Found {len(reviews)} review cycles")
                            
                            for review in reviews:
                                # Format display values (like UI does)
                                evidence = "Yes" if review['evidence_links'] else "No"
                                
                                # Simulate adding to schedule tree
                                schedule_item = {
                                    'cycle': f"{review['cycle_no']}/{len(reviews)}",
                                    'service': service['service_name'][:20] + "...",
                                    'planned_date': review['planned_date'],
                                    'due_date': review['due_date'],
                                    'disciplines': review['disciplines'],
                                    'status': review['status'],
                                    'weight_factor': f"{review['weight_factor']:.1f}",
                                    'evidence': evidence,
                                    'action': "Mark Issued" if review['status'] == 'planned' else "View"
                                }
                                
                                self.schedule_tree_items.append(schedule_item)
                                print(f"      ➕ Added to schedule: Cycle {review['cycle_no']} - {review['planned_date']} ({review['status']})")
                    
                    print(f"✅ Schedule loaded with {len(self.schedule_tree_items)} items total")
                    
                except Exception as e:
                    print(f"❌ Error loading schedule: {e}")
                    import traceback
                    traceback.print_exc()
            
            def generate_cycles_simulation(self):
                """Simulate the generate_cycles function from the dialog"""
                print("\n🔄 Simulating cycle generation...")
                
                # Get eligible services (like the dialog does)
                services = self.review_service.get_project_services(self.current_project_id)
                eligible_services = [s for s in services if s['unit_type'] in ['review', 'audit']]
                
                if not eligible_services:
                    print("❌ No eligible services found")
                    return False
                
                print(f"✅ Found {len(eligible_services)} eligible services")
                
                # Simulate user selections (select first service)
                selected_service = eligible_services[0]
                service_id = selected_service['service_id']
                
                # Simulate parameter inputs
                start_date = datetime.now()
                end_date = start_date + timedelta(days=90)
                disciplines = "Architecture,Structure,Services"
                
                print(f"📋 Generating cycles for: {selected_service['service_name']}")
                print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                
                # Clear existing cycles (like the dialog does when clear_existing is True)
                self.review_service.cursor.execute(
                    "DELETE FROM ServiceReviews WHERE service_id = ?", 
                    (service_id,)
                )
                self.review_service.db.commit()
                print("✅ Cleared existing cycles")
                
                # Generate new cycles (exact same call as in the dialog)
                cycles = self.review_service.generate_review_cycles(
                    service_id=service_id,
                    unit_qty=int(selected_service['unit_qty'] or 1),
                    start_date=start_date,
                    end_date=end_date,
                    cadence='weekly',
                    disciplines=disciplines
                )
                
                print(f"✅ Generated {len(cycles)} cycles")
                for cycle in cycles:
                    print(f"   📅 Cycle {cycle['cycle_no']}: {cycle['planned_date']} → {cycle['due_date']}")
                
                # Refresh the schedule view (like the dialog does)
                print("\n🔄 Refreshing schedule display...")
                self.load_project_schedule()
                
                return True
        
        # Create mock UI and run simulation
        ui = MockUI()
        
        if ui.review_service:
            # First, show current state
            print("\n📊 Initial Schedule State:")
            ui.load_project_schedule()
            
            # Then simulate generating cycles
            success = ui.generate_cycles_simulation()
            
            if success:
                print("\n🎉 Cycle generation simulation completed successfully!")
                print(f"📊 Final schedule has {len(ui.schedule_tree_items)} items")
                return True
            else:
                print("\n❌ Cycle generation simulation failed!")
                return False
        else:
            print("❌ Could not initialize UI simulation")
            return False
            
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Testing Generate Cycles Button Simulation")
    print("=" * 50)
    
    success = simulate_generate_cycles_button()
    
    if success:
        print("\n✅ SUCCESS: The Generate Cycles functionality is working correctly!")
        print("🔍 The issue is likely in the UI display layer or project selection.")
    else:
        print("\n❌ FAILURE: Found the issue in the cycle generation logic!")
    
    return success

if __name__ == "__main__":
    main()