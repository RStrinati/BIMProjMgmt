"""
Check if MEL071 and MEL081 custom attribute data exists in staging.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import connect_to_db

def check_staging_for_mel071_mel081():
    """Check staging table for MEL071 and MEL081 data."""
    
    conn = connect_to_db('acc_data_schema')
    cursor = conn.cursor()
    
    print('=' * 80)
    print('STAGING: Custom attributes for MEL071 and MEL081')
    print('=' * 80)
    
    # MEL071
    cursor.execute("""
        SELECT COUNT(*) as total,
               COUNT(DISTINCT issue_id) as unique_issues
        FROM staging.issues_custom_attributes
        WHERE bim360_project_id = '648AFD41-A9BA-4909-8D4F-8F4477FE3AE8'
    """)
    row = cursor.fetchone()
    print(f'\nMEL071 (648AFD41...): {row[0]} rows, {row[1]} unique issues')
    
    # MEL081
    cursor.execute("""
        SELECT COUNT(*) as total,
               COUNT(DISTINCT issue_id) as unique_issues
        FROM staging.issues_custom_attributes
        WHERE bim360_project_id = 'B6706F13-8A3A-4C98-9382-1148051059E7'
    """)
    row = cursor.fetchone()
    print(f'MEL081 (B6706F13...): {row[0]} rows, {row[1]} unique issues')
    
    print('\n' + '=' * 80)
    print('ALL PROJECTS in staging.issues_custom_attributes')
    print('=' * 80)
    cursor.execute("""
        SELECT 
            bim360_project_id,
            COUNT(*) as total,
            COUNT(DISTINCT issue_id) as unique_issues,
            COUNT(DISTINCT attribute_title) as unique_attrs
        FROM staging.issues_custom_attributes
        GROUP BY bim360_project_id
        ORDER BY total DESC
    """)
    
    print()
    for row in cursor.fetchall():
        print(f'  Project {row[0]}: {row[1]} rows, {row[2]} issues, {row[3]} attributes')
    
    print('\n' + '=' * 80)
    print('RECOMMENDATION')
    print('=' * 80)
    
    cursor.execute("""
        SELECT COUNT(*) FROM staging.issues_custom_attributes
        WHERE bim360_project_id IN (
            '648AFD41-A9BA-4909-8D4F-8F4477FE3AE8',  -- MEL071
            'B6706F13-8A3A-4C98-9382-1148051059E7'   -- MEL081
        )
    """)
    count = cursor.fetchone()[0]
    
    if count == 0:
        print('\n❌ MEL071 and MEL081 custom attribute data NOT in staging!')
        print('\nPossible reasons:')
        print('  1. Data was never imported from ACC CSV export')
        print('  2. CSV file is missing custom_attributes data')
        print('  3. Import script filtered out these projects')
        print('\nNext steps:')
        print('  1. Check if ACC CSV export includes issues_custom_attributes.csv')
        print('  2. Re-run ACC import for MEL071 and MEL081')
        print('  3. Verify custom attributes are set in ACC web interface')
    else:
        print(f'\n✅ {count} rows found in staging - run merge again!')
    
    conn.close()

if __name__ == '__main__':
    check_staging_for_mel071_mel081()
