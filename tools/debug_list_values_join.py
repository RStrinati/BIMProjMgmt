"""
Debug the ListValues join in vw_issues_expanded.

The view joins issues_custom_attributes.attribute_value to 
issues_custom_attribute_list_values.list_id to get display values.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import connect_to_db

def debug_list_values_join():
    """Debug the ListValues join."""
    
    conn = connect_to_db('acc_data_schema')
    cursor = conn.cursor()
    
    print('=' * 80)
    print('SCHEMA CHECK')
    print('=' * 80)
    
    cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo'
        AND TABLE_NAME = 'issues_custom_attribute_list_values'
        ORDER BY ORDINAL_POSITION
    """)
    print('\nissues_custom_attribute_list_values columns:')
    for row in cursor.fetchall():
        print(f'  {row[1]} ({row[2]})')
    
    print('\n' + '=' * 80)
    print('SAMPLE DATA: issues_custom_attributes')
    print('=' * 80)
    cursor.execute("""
        SELECT TOP 3
            issue_id,
            attribute_title,
            attribute_value,
            attribute_data_type,
            attribute_mapping_id
        FROM dbo.issues_custom_attributes
        WHERE attribute_title = 'Clash Level'
    """)
    print('\nSample Clash Level attributes:')
    for row in cursor.fetchall():
        print(f'  Issue: {row[0]}')
        print(f'    Title: {row[1]}')
        print(f'    Value (UUID): {row[2]}')
        print(f'    Mapping ID: {row[4]}')
    
    print('\n' + '=' * 80)
    print('SAMPLE DATA: issues_custom_attribute_list_values')
    print('=' * 80)
    cursor.execute("""
        SELECT TOP 10 *
        FROM dbo.issues_custom_attribute_list_values
    """)
    columns = [desc[0] for desc in cursor.description]
    print(f'\nColumns: {", ".join(columns)}')
    print('\nSample rows:')
    for row in cursor.fetchall()[:3]:
        print(f'  {row}')
    
    print('\n' + '=' * 80)
    print('JOIN TEST: Does attribute_value match list_id?')
    print('=' * 80)
    cursor.execute("""
        SELECT TOP 5
            ica.issue_id,
            ica.attribute_title,
            ica.attribute_value AS attr_value_uuid,
            lv.list_id AS list_value_uuid,
            lv.list_value AS display_value,
            CASE 
                WHEN ica.attribute_value = lv.list_id THEN 'MATCH ✅'
                ELSE 'NO MATCH ❌'
            END AS join_status
        FROM dbo.issues_custom_attributes ica
        LEFT JOIN dbo.issues_custom_attribute_list_values lv
            ON lv.list_id = ica.attribute_value
           AND lv.attribute_mappings_id = ica.attribute_mapping_id
        WHERE ica.attribute_title = 'Clash Level'
    """)
    print('\nJoin results:')
    for row in cursor.fetchall():
        print(f'\n  Issue: {row[0]}')
        print(f'  Attribute: {row[1]}')
        print(f'  Attr Value: {row[2]}')
        print(f'  List ID: {row[3] if row[3] else "❌ NULL"}')
        print(f'  Display: {row[4] if row[4] else "❌ NULL"}')
        print(f'  Status: {row[5]}')
    
    print('\n' + '=' * 80)
    print('DATA TYPE CHECK: GUID vs NVARCHAR')
    print('=' * 80)
    cursor.execute("""
        SELECT 
            DATA_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'issues_custom_attributes'
        AND COLUMN_NAME = 'attribute_value'
    """)
    attr_value_type = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT 
            DATA_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'issues_custom_attribute_list_values'
        AND COLUMN_NAME = 'list_id'
    """)
    list_id_type = cursor.fetchone()[0]
    
    print(f'\nissues_custom_attributes.attribute_value: {attr_value_type}')
    print(f'issues_custom_attribute_list_values.list_id: {list_id_type}')
    
    if attr_value_type != list_id_type:
        print(f'\n⚠️  DATA TYPE MISMATCH!')
        print(f'   This could prevent the join from working!')
    
    conn.close()

if __name__ == '__main__':
    debug_list_values_join()
