"""
Quick check to see what values are actually in the view.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_pool import get_db_connection

def quick_check_view():
    """Quick check of view values."""
    
    with get_db_connection('acc_data_schema') as conn:
    cursor = conn.cursor()
    
    print('=' * 80)
    print('CHECKING VIEW: First 20 rows')
    print('=' * 80)
    cursor.execute("""
        SELECT TOP 20
            issue_id,
            display_id,
            title,
            Building_Level,
            Clash_Level,
            Location,
            Phase,
            Priority
        FROM dbo.vw_issues_expanded
        ORDER BY display_id
    """)
    
    print('\nFirst 20 issues in view:')
    null_count = 0
    for row in cursor.fetchall():
        has_attrs = any([row[3], row[4], row[5], row[6], row[7]])
        status = '✅' if has_attrs else '❌ ALL NULL'
        
        if not has_attrs:
            null_count += 1
        
        print(f'\n  Issue #{row[1]}: {row[2][:50]}... {status}')
        print(f'    Building: {row[3] if row[3] else "NULL"}')
        print(f'    Clash:    {row[4] if row[4] else "NULL"}')
        print(f'    Location: {row[5] if row[5] else "NULL"}')
        print(f'    Phase:    {row[6] if row[6] else "NULL"}')
        print(f'    Priority: {row[7] if row[7] else "NULL"}')
    
    print(f'\n{null_count}/20 issues have NO custom attributes')
    
    # Check if view was actually updated
    print('\n' + '=' * 80)
    print('CHECKING: Was view actually updated?')
    print('=' * 80)
    cursor.execute("""
        SELECT 
            OBJECT_DEFINITION(OBJECT_ID('dbo.vw_issues_expanded'))
    """)
    view_def = cursor.fetchone()[0]
    
    if 'CAST(lv.list_id AS NVARCHAR(MAX))' in view_def:
        print('✅ View contains the CAST fix')
    else:
        print('❌ View does NOT contain the CAST fix - update failed!')
        print('   Looking for: CAST(lv.list_id AS NVARCHAR(MAX))')
    
    if 'Building_Level' in view_def:
        print('✅ View contains Building_Level column')
    else:
        print('❌ View does NOT contain Building_Level column')
    
    # Check the JSON
    print('\n' + '=' * 80)
    print('CHECKING: custom_attributes_json content')
    print('=' * 80)
    cursor.execute("""
        SELECT TOP 3
            issue_id,
            display_id,
            custom_attributes_json
        FROM dbo.vw_issues_expanded
        WHERE custom_attributes_json IS NOT NULL
    """)
    
    print('\nSample JSON from view:')
    for row in cursor.fetchall():
        print(f'\nIssue #{row[1]}:')
        if row[2]:
            json_preview = row[2][:300] if len(row[2]) > 300 else row[2]
            print(f'  JSON: {json_preview}...')
        else:
            print('  JSON: NULL')

if __name__ == '__main__':
    quick_check_view()
