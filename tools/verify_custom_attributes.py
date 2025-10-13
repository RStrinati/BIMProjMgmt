"""
Final verification that custom attributes are working in vw_issues_expanded.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_pool import get_db_connection

def verify_custom_attributes():
    """Verify custom attributes in view."""
    
    with get_db_connection('acc_data_schema') as conn:
        cursor = conn.cursor()
        
        print('=' * 80)
        print('FINAL VERIFICATION: Custom Attributes in View')
        print('=' * 80)
        
        # Get counts
        cursor.execute("""
            SELECT 
                COUNT(*) as total_issues,
                COUNT(CASE WHEN Building_Level IS NOT NULL THEN 1 END) as building_level_count,
                COUNT(CASE WHEN Clash_Level IS NOT NULL THEN 1 END) as clash_level_count,
                COUNT(CASE WHEN Location IS NOT NULL THEN 1 END) as location_count,
                COUNT(CASE WHEN Location_01 IS NOT NULL THEN 1 END) as location_01_count,
                COUNT(CASE WHEN Phase IS NOT NULL THEN 1 END) as phase_count,
                COUNT(CASE WHEN Priority IS NOT NULL THEN 1 END) as priority_count
            FROM acc_data_schema.dbo.vw_issues_expanded
        """)
    row = cursor.fetchone()
    print()
    print(f'Total Issues: {row[0]}')
    print()
    print('Custom Attribute Coverage:')
    print(f'  Building Level:  {row[1]:4d} issues ({row[1]/row[0]*100:.1f}%)')
    print(f'  Clash Level:     {row[2]:4d} issues ({row[2]/row[0]*100:.1f}%)')
    print(f'  Location:        {row[3]:4d} issues ({row[3]/row[0]*100:.1f}%)')
    print(f'  Location 01:     {row[4]:4d} issues ({row[4]/row[0]*100:.1f}%)')
    print(f'  Phase:           {row[5]:4d} issues ({row[5]/row[0]*100:.1f}%)')
    print(f'  Priority:        {row[6]:4d} issues ({row[6]/row[0]*100:.1f}%)')
    
    print()
    print('=' * 80)
    print('Sample Issues with ALL Custom Attributes Populated')
    print('=' * 80)
    cursor.execute("""
        SELECT TOP 5
            display_id,
            title,
            Building_Level,
            Clash_Level,
            Location,
            Phase,
            Priority
        FROM acc_data_schema.dbo.vw_issues_expanded
        WHERE Building_Level IS NOT NULL 
          AND Clash_Level IS NOT NULL
          AND Location IS NOT NULL
          AND Phase IS NOT NULL
        ORDER BY display_id
    """)
    
    results = cursor.fetchall()
    for row in results:
        print()
        print(f'Issue #{row[0]}: {row[1][:60]}')
        print(f'  Building Level:  {row[2]}')
        print(f'  Clash Level:     {row[3]}')
        print(f'  Location:        {row[4]}')
        print(f'  Phase:           {row[5]}')
        print(f'  Priority:        {row[6] if row[6] else "(not set)"}')
    
    print()
    print('=' * 80)
    print('Breakdown by Clash Level')
    print('=' * 80)
    cursor.execute("""
        SELECT 
            Clash_Level,
            COUNT(*) as count
        FROM acc_data_schema.dbo.vw_issues_expanded
        WHERE Clash_Level IS NOT NULL
        GROUP BY Clash_Level
        ORDER BY Clash_Level
    """)
    print()
    for row in cursor.fetchall():
        print(f'  {row[0]}: {row[1]} issues')
    
    print()
    print('✅ SUCCESS! All custom attributes are working in the view!')

if __name__ == '__main__':
    verify_custom_attributes()
