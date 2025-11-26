"""
Import MEL071 and MEL081 ACC data to populate custom attributes.

This will:
1. Import ACC ZIP files for MEL071 and MEL081
2. Merge custom attributes from staging to dbo
3. Verify data appears in the view
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.acc_handler import import_acc_data
from database_pool import get_db_connection

def import_mel071_mel081():
    """Import MEL071 and MEL081 data."""
    
    print('=' * 80)
    print('IMPORTING MEL071 AND MEL081 ACC DATA')
    print('=' * 80)
    
    # MEL071 - use today's export
    mel071_zip = r"C:\Users\RicoStrinati\Downloads\autodesk_data_extract_MEL071-251008.zip"
    
    # MEL081 - you'll need to specify the path
    # Find it with: Get-ChildItem -Path "C:\Users\RicoStrinati\iimbe" -Recurse -Filter "*MEL081*.zip"
    mel081_zip = r"C:\Users\RicoStrinati\iimbe\D3_252347_MEL081_AWS_LL_STOCKMAN - Documents\Delivery\03_Dashboard\08_ACCExport\autodesk_data_extract_MEL081-LATEST.zip"
    
    print(f'\n1. Importing MEL071...')
    print(f'   Source: {mel071_zip}')
    
    if os.path.exists(mel071_zip):
        try:
            import_acc_data(mel071_zip)
            print('   ✅ MEL071 imported successfully')
        except Exception as e:
            print(f'   ❌ MEL071 import failed: {e}')
    else:
        print(f'   ❌ File not found!')
    
    print(f'\n2. Importing MEL081...')
    print(f'   Source: {mel081_zip}')
    print('   ⚠️  UPDATE THE PATH ABOVE WITH ACTUAL MEL081 ZIP FILE')
    
    # Uncomment when you have the correct path:
    # if os.path.exists(mel081_zip):
    #     try:
    #         import_acc_data(mel081_zip)
    #         print('   ✅ MEL081 imported successfully')
    #     except Exception as e:
    #         print(f'   ❌ MEL081 import failed: {e}')
    # else:
    #     print(f'   ❌ File not found!')
    
    # Verify
    print('\n' + '=' * 80)
    print('VERIFYING CUSTOM ATTRIBUTES')
    print('=' * 80)
    
    with get_db_connection('acc_data_schema') as conn:
        cursor = conn.cursor()
        
        # Check MEL071
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM dbo.issues_custom_attributes
            WHERE bim360_project_id = '648AFD41-A9BA-4909-8D4F-8F4477FE3AE8'
        """)
        mel071_count = cursor.fetchone()[0]
        print(f'\nMEL071 custom attributes: {mel071_count} rows')
        
        # Check MEL081
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM dbo.issues_custom_attributes
            WHERE bim360_project_id = 'B6706F13-8A3A-4C98-9382-1148051059E7'
        """)
        mel081_count = cursor.fetchone()[0]
        print(f'MEL081 custom attributes: {mel081_count} rows')
        
        # Check view
        cursor.execute("""
            SELECT 
                project_name,
                COUNT(CASE WHEN Clash_Level IS NOT NULL THEN 1 END) as clash_count
            FROM dbo.vw_issues_expanded
            WHERE project_name IN ('MEL071 - Site A', 'MEL081 - Site A')
            GROUP BY project_name
        """)
        
        print('\nView verification:')
        for row in cursor.fetchall():
            print(f'  {row[0]}: {row[1]} issues with Clash Level')
    
    print('\n' + '=' * 80)
    print('NEXT STEPS')
    print('=' * 80)
    print('\n1. Update mel081_zip path in this script')
    print('2. Uncomment the MEL081 import code')
    print('3. Run this script again')
    print('\nThen your custom attributes will be populated!')

if __name__ == '__main__':
    import_mel071_mel081()
