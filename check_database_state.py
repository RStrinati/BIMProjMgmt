#!/usr/bin/env python3
"""Simple test to check ServiceReviews table vs service unit_qty"""

import sqlite3
import pyodbc
from database import connect_to_db

try:
    print("🔍 Checking ServiceReviews vs ProjectServices unit_qty...")
    
    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        
        # Get services for project 2 (NEPS)
        print("\n1. Getting NEPS project services with unit_type='review'...")
        cursor.execute("""
            SELECT service_id, service_name, unit_qty, unit_type,
                   phase, schedule_start, schedule_end, schedule_frequency
            FROM ProjectServices ps
            LEFT JOIN ServiceScheduleSettings sss ON ps.service_id = sss.service_id
            WHERE ps.project_id = 2 AND ps.unit_type = 'review'
            ORDER BY ps.service_name
        """)
        
        services = cursor.fetchall()
        print(f"Found {len(services)} review services:")
        
        total_expected_cycles = 0
        for service in services:
            service_id, name, unit_qty, unit_type, phase, start, end, freq = service
            unit_qty = unit_qty or 0
            total_expected_cycles += unit_qty
            
            print(f"  Service {service_id}: {name}")
            print(f"    - Unit Qty: {unit_qty}")
            print(f"    - Start: {start}")
            print(f"    - End: {end}")
            print(f"    - Frequency: {freq}")
            
            # Count actual reviews for this service
            cursor.execute("SELECT COUNT(*) FROM ServiceReviews WHERE service_id = ?", (service_id,))
            actual_count = cursor.fetchone()[0]
            print(f"    - Actual Reviews: {actual_count}")
            
            if actual_count != unit_qty:
                print(f"    ❌ MISMATCH: Expected {unit_qty}, got {actual_count}")
            else:
                print(f"    ✅ CORRECT: {unit_qty} reviews match")
        
        print(f"\n2. Summary:")
        print(f"   Total expected cycles from services: {total_expected_cycles}")
        
        # Count total reviews for project 2
        cursor.execute("""
            SELECT COUNT(*)
            FROM ServiceReviews sr
            LEFT JOIN ProjectServices ps ON sr.service_id = ps.service_id
            WHERE ps.project_id = 2
        """)
        total_actual = cursor.fetchone()[0]
        print(f"   Total actual review cycles: {total_actual}")
        
        if total_actual != total_expected_cycles:
            print(f"   ❌ OVERALL MISMATCH: Expected {total_expected_cycles}, got {total_actual}")
        else:
            print(f"   ✅ OVERALL CORRECT: {total_expected_cycles} cycles match")
        
        # Show some sample review cycles
        print(f"\n3. Sample review cycles:")
        cursor.execute("""
            SELECT sr.review_id, ps.service_name, sr.cycle_no, sr.planned_date, sr.status
            FROM ServiceReviews sr
            LEFT JOIN ProjectServices ps ON sr.service_id = ps.service_id
            WHERE ps.project_id = 2
            ORDER BY sr.planned_date, sr.cycle_no
            LIMIT 10
        """)
        
        cycles = cursor.fetchall()
        for cycle in cycles:
            print(f"   Review {cycle[0]}: {cycle[1]} - Cycle {cycle[2]} on {cycle[3]} ({cycle[4]})")
        
        conn.close()
        print("\n✅ Database check completed!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()