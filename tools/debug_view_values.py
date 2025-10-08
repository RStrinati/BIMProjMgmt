"""
Debug why custom attribute columns in vw_issues_expanded are NULL.

Traces data flow from:
1. dbo.issues_custom_attributes table
2. custom_attributes_json CTE
3. OPENJSON extraction in view
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import connect_to_db

def debug_view_values():
    """Debug the view value extraction."""
    
    conn = connect_to_db('acc_data_schema')
    cursor = conn.cursor()
    
    print('=' * 80)
    print('STEP 1: Check dbo.issues_custom_attributes table')
    print('=' * 80)
    cursor.execute("""
        SELECT TOP 5
            ica.issue_id,
            ica.attribute_title,
            ica.attribute_value,
            ica.attribute_data_type
        FROM dbo.issues_custom_attributes ica
        WHERE ica.attribute_title = 'Clash Level'
        ORDER BY ica.issue_id
    """)
    print('\nSample Clash Level data in dbo.issues_custom_attributes:')
    for row in cursor.fetchall():
        print(f'  Issue: {row[0]} | Title: {row[1]} | Value: {row[2]} | Type: {row[3]}')
    
    print('\n' + '=' * 80)
    print('STEP 2: Check if attribute_value is the list_id UUID')
    print('=' * 80)
    cursor.execute("""
        SELECT TOP 5
            ica.issue_id,
            ica.attribute_title,
            ica.attribute_value,
            icalv.value as actual_display_value
        FROM dbo.issues_custom_attributes ica
        LEFT JOIN dbo.issues_custom_attribute_list_values icalv
            ON ica.attribute_value = CAST(icalv.list_id AS NVARCHAR(MAX))
        WHERE ica.attribute_title = 'Clash Level'
        ORDER BY ica.issue_id
    """)
    print('\nJoining to list_values to get display value:')
    for row in cursor.fetchall():
        display = row[3] if row[3] else '❌ NULL - NO MATCH'
        print(f'  Issue: {str(row[0])[:36]}... | UUID: {row[2][:36]}... | Display: {display}')
    
    print('\n' + '=' * 80)
    print('STEP 3: Check custom_attributes_json structure')
    print('=' * 80)
    cursor.execute("""
        SELECT TOP 2
            i.issue_id,
            i.title,
            (
                SELECT 
                    ica.attribute_title as [name],
                    ica.attribute_data_type as [type],
                    icalv.value as [value],
                    ica.is_required,
                    ica.created_at
                FROM dbo.issues_custom_attributes ica
                LEFT JOIN dbo.issues_custom_attribute_list_values icalv
                    ON ica.attribute_value = CAST(icalv.list_id AS NVARCHAR(MAX))
                WHERE ica.issue_id = i.issue_id
                FOR JSON PATH
            ) AS custom_attributes_json
        FROM dbo.issues_issues i
        WHERE EXISTS (
            SELECT 1 FROM dbo.issues_custom_attributes ica2
            WHERE ica2.issue_id = i.issue_id
            AND ica2.attribute_title = 'Clash Level'
        )
    """)
    print('\nJSON structure for sample issues:')
    for row in cursor.fetchall():
        print(f'\nIssue: {row[1][:60]}...')
        if row[2]:
            json_str = row[2][:500]
            print(f'JSON: {json_str}...')
        else:
            print('JSON: ❌ NULL')
    
    print('\n' + '=' * 80)
    print('STEP 4: Test OPENJSON extraction directly')
    print('=' * 80)
    cursor.execute("""
        SELECT TOP 3
            i.issue_id,
            i.title,
            (
                SELECT TOP 1 [value]
                FROM OPENJSON((
                    SELECT 
                        ica.attribute_title as [name],
                        ica.attribute_data_type as [type],
                        icalv.value as [value],
                        ica.is_required,
                        ica.created_at
                    FROM dbo.issues_custom_attributes ica
                    LEFT JOIN dbo.issues_custom_attribute_list_values icalv
                        ON ica.attribute_value = CAST(icalv.list_id AS NVARCHAR(MAX))
                    WHERE ica.issue_id = i.issue_id
                    FOR JSON PATH
                ))
                WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
                WHERE [name] = 'Clash Level'
            ) AS extracted_clash_level
        FROM dbo.issues_issues i
        WHERE EXISTS (
            SELECT 1 FROM dbo.issues_custom_attributes ica2
            WHERE ica2.issue_id = i.issue_id
            AND ica2.attribute_title = 'Clash Level'
        )
    """)
    print('\nDirect OPENJSON extraction test:')
    for row in cursor.fetchall():
        value = row[2] if row[2] else '❌ NULL'
        print(f'  Issue: {row[1][:50]}... | Clash Level: {value}')
    
    print('\n' + '=' * 80)
    print('STEP 5: Compare with view output')
    print('=' * 80)
    cursor.execute("""
        SELECT TOP 5
            issue_id,
            title,
            Clash_Level,
            Building_Level,
            Location,
            Phase
        FROM dbo.vw_issues_expanded
        WHERE issue_id IN (
            SELECT TOP 5 issue_id 
            FROM dbo.issues_custom_attributes 
            WHERE attribute_title = 'Clash Level'
        )
    """)
    print('\nActual view output:')
    for row in cursor.fetchall():
        print(f'  Issue: {row[1][:50]}...')
        print(f'    Clash Level: {row[2] if row[2] else "❌ NULL"}')
        print(f'    Building Level: {row[3] if row[3] else "NULL"}')
        print(f'    Location: {row[4] if row[4] else "NULL"}')
        print(f'    Phase: {row[5] if row[5] else "NULL"}')
    
    conn.close()

if __name__ == '__main__':
    debug_view_values()
