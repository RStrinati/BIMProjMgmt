#!/usr/bin/env python3
"""Check ServiceScheduleSettings table and fix review generation"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db

def check_schedule_table():
    """Check ServiceScheduleSettings table structure"""
    
    db = connect_to_db()
    if not db:
        print("❌ Failed to connect to database")
        return
    
    cursor = db.cursor()
    
    # Check ServiceScheduleSettings schema
    print("🔍 Checking ServiceScheduleSettings table schema...")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'ServiceScheduleSettings'
        ORDER BY ORDINAL_POSITION
    """)
    
    columns = cursor.fetchall()
    
    if columns:
        print(f"\n📋 ServiceScheduleSettings table has {len(columns)} columns:")
        for col in columns:
            col_name, data_type, nullable, default = col
            default_str = f" (default: {default})" if default else ""
            nullable_str = "NULL" if nullable == 'YES' else "NOT NULL"
            print(f"  📄 {col_name}: {data_type} {nullable_str}{default_str}")
        
        # Check sample data
        print("\n📊 Sample data from ServiceScheduleSettings:")
        cursor.execute("SELECT TOP 10 * FROM ServiceScheduleSettings")
        rows = cursor.fetchall()
        
        if rows:
            # Get column names
            col_names = [desc[0] for desc in cursor.description]
            print(f"  📋 Columns: {', '.join(col_names)}")
            
            for i, row in enumerate(rows):
                print(f"  📄 Row {i+1}: {dict(zip(col_names, row))}")
        else:
            print("  ⚠️ No data found in ServiceScheduleSettings")
    
    else:
        print("\n❌ ServiceScheduleSettings table not found")
    
    # Also check what services exist
    print("\n🔍 Checking existing services...")
    cursor.execute("""
        SELECT TOP 5 service_id, project_id, service_name, unit_type, unit_qty
        FROM ProjectServices
        WHERE unit_type = 'review'
        ORDER BY service_id
    """)
    
    services = cursor.fetchall()
    
    if services:
        print(f"\n📋 Review services found:")
        for service in services:
            service_id, project_id, name, unit_type, qty = service
            print(f"  📄 Service {service_id} (Project {project_id}): {name} - {qty} {unit_type}")
    else:
        print(f"\n⚠️ No services with unit_type='review' found")
        
        # Check all services
        cursor.execute("SELECT TOP 10 service_id, unit_type, unit_qty FROM ProjectServices")
        all_services = cursor.fetchall()
        print(f"\n📋 Sample of all services:")
        for service in all_services:
            service_id, unit_type, qty = service
            print(f"  📄 Service {service_id}: {unit_type or 'None'} (qty: {qty or 0})")
    
    cursor.close()
    db.close()

if __name__ == "__main__":
    check_schedule_table()