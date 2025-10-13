#!/usr/bin/env python3
"""
Test script to validate one-off frequency functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from review_management_service import ReviewManagementService
from database import get_db_connection
from datetime import datetime, timedelta

def test_oneoff_frequency():
    """Test that one-off frequency creates exactly one review cycle"""
    print("Testing one-off frequency functionality...")
    
    # Connect to database
    try:
        with get_db_connection() as conn:
            service = ReviewManagementService(conn)
            
            # Test data for one-off review
            start_date = datetime.now()
            end_date = start_date + timedelta(days=30)
            
            # Generate review cycles for one-off frequency
            cycles = service.generate_review_cycles(
                service_id=1,  # Test service ID
                unit_qty=1,
                cadence='one-off',
                start_date=start_date,
                end_date=end_date
            )
            
            print(f"Generated {len(cycles)} cycle(s) for one-off frequency")
            
            # Verify exactly one cycle is created
            assert len(cycles) == 1, f"Expected 1 cycle for one-off, got {len(cycles)}"
            
            # Verify the cycle details
            cycle = cycles[0]
            print(f"Cycle details:")
            print(f"  Description: {cycle.get('description', 'N/A')}")
            print(f"  Start Date: {cycle.get('start_date', 'N/A')}")
            print(f"  End Date: {cycle.get('end_date', 'N/A')}")
            
            # Compare different frequencies
            print("\nComparing frequencies:")
            
            # Weekly (should create multiple cycles)
            weekly_cycles = service.generate_review_cycles(
                service_id=1,
                unit_qty=1,
                cadence='weekly',
                start_date=start_date,
                end_date=end_date
            )
            print(f"Weekly frequency: {len(weekly_cycles)} cycles")
            
            # Monthly (should create multiple cycles for 30+ day period)
            monthly_cycles = service.generate_review_cycles(
                service_id=1,
                unit_qty=1,
                cadence='monthly',
                start_date=start_date,
                end_date=end_date
            )
            print(f"Monthly frequency: {len(monthly_cycles)} cycles")
            
            # One-off should always be 1 regardless of duration
            oneoff_long = service.generate_review_cycles(
                service_id=1,
                unit_qty=1,
                cadence='one-off',
                start_date=start_date,
                end_date=start_date + timedelta(days=365)  # 1 year
            )
            print(f"One-off (1 year duration): {len(oneoff_long)} cycle(s)")
            
            assert len(oneoff_long) == 1, "One-off should always create exactly 1 cycle regardless of duration"
            
            print("\n✓ One-off frequency test passed!")
            return True
    
    except Exception as e:
        print(f"❌ Error during test: {e}")
        raise

if __name__ == "__main__":
    try:
        test_oneoff_frequency()
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)