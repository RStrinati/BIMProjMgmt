"""
Deep investigation: Why aren't MEL071 and MEL081 showing custom attributes?
Check if the data exists but isn't joining correctly.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import connect_to_db

def investigate_mel071_mel081():
    """Investigate MEL071 and MEL081 custom attributes."""
    
    conn = connect_to_db('acc_data_schema')
    cursor = conn.cursor()
    
    print('=' * 80)
    print('STEP 1: Find project IDs for MEL071 and MEL081')
    print('=' * 80)
    
    cursor.execute("""
        SELECT DISTINCT
            project_name,
            project_id
        FROM dbo.vw_issues_expanded
        WHERE project_name LIKE '%MEL071%'
           OR project_name LIKE '%MEL081%'
    """)
    
    print('\nProject IDs from view:')
    project_ids = {}
    for row in cursor.fetchall():
        project_ids[row[0]] = row[1]
        print(f'  {row[0]}: {row[1]}')
    
    print('\n' + '=' * 80)
    print('STEP 2: Check if custom attributes EXIST for these projects')
    print('=' * 80)
    
    for proj_name, proj_id in project_ids.items():
        print(f'\n{proj_name} ({proj_id}):')
        
        # Check mappings
        cursor.execute(f"""
            SELECT 
                title,
                id,
                data_type
            FROM dbo.issues_custom_attributes_mappings
            WHERE bim360_project_id = '{proj_id}'
        """)
        
        mappings = cursor.fetchall()
        if mappings:
            print(f'  ✅ Mappings found: {len(mappings)}')
            for m in mappings:
                print(f'     - {m[0]} ({m[2]}) ID: {m[1]}')
        else:
            print(f'  ❌ NO MAPPINGS FOUND')
        
        # Check actual attribute data
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT issue_id) as unique_issues,
                COUNT(DISTINCT attribute_title) as unique_attrs
            FROM dbo.issues_custom_attributes
            WHERE bim360_project_id = '{proj_id}'
        """)
        
        row = cursor.fetchone()
        print(f'  Custom attributes data: {row[0]} rows, {row[1]} issues, {row[2]} unique attributes')
        
        if row[0] > 0:
            cursor.execute(f"""
                SELECT 
                    attribute_title,
                    COUNT(*) as count
                FROM dbo.issues_custom_attributes
                WHERE bim360_project_id = '{proj_id}'
                GROUP BY attribute_title
            """)
            print(f'  Breakdown by attribute:')
            for r in cursor.fetchall():
                print(f'     - {r[0]}: {r[1]} issues')
    
    print('\n' + '=' * 80)
    print('STEP 3: Check if issues from these projects are in the view')
    print('=' * 80)
    
    for proj_name, proj_id in project_ids.items():
        cursor.execute(f"""
            SELECT COUNT(*) as total
            FROM dbo.vw_issues_expanded
            WHERE project_name = '{proj_name}'
        """)
        view_count = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT COUNT(*) as total
            FROM dbo.issues_issues
            WHERE bim360_project_id = '{proj_id}'
        """)
        source_count = cursor.fetchone()[0]
        
        print(f'\n{proj_name}:')
        print(f'  Issues in source table: {source_count}')
        print(f'  Issues in view:         {view_count}')
        
        if source_count != view_count:
            print(f'  ⚠️  MISMATCH! {source_count - view_count} issues missing from view')
    
    print('\n' + '=' * 80)
    print('STEP 4: Sample issue from MEL071 - trace through the join')
    print('=' * 80)
    
    # Get a sample issue from MEL071
    mel071_id = None
    for proj_name, proj_id in project_ids.items():
        if 'MEL071' in proj_name:
            mel071_id = proj_id
            break
    
    if mel071_id:
        cursor.execute(f"""
            SELECT TOP 1
                issue_id,
                display_id,
                title,
                bim360_project_id,
                bim360_account_id
            FROM dbo.issues_issues
            WHERE bim360_project_id = '{mel071_id}'
        """)
        
        issue = cursor.fetchone()
        if issue:
            issue_id = issue[0]
            print(f'\nSample issue: #{issue[1]} - {issue[2][:50]}...')
            print(f'  Issue ID: {issue_id}')
            print(f'  Project ID: {issue[3]}')
            print(f'  Account ID: {issue[4]}')
            
            # Check if this issue has custom attributes in the table
            cursor.execute(f"""
                SELECT 
                    attribute_title,
                    attribute_value,
                    attribute_mapping_id,
                    bim360_project_id,
                    bim360_account_id
                FROM dbo.issues_custom_attributes
                WHERE issue_id = '{issue_id}'
            """)
            
            attrs = cursor.fetchall()
            if attrs:
                print(f'\n  ✅ Found {len(attrs)} custom attributes in dbo.issues_custom_attributes:')
                for attr in attrs:
                    print(f'     - {attr[0]}: {attr[1][:36]}...')
                    print(f'       Mapping ID: {attr[2]}')
                    print(f'       Project ID: {attr[3]}')
                    print(f'       Account ID: {attr[4]}')
            else:
                print(f'\n  ❌ NO custom attributes found in dbo.issues_custom_attributes')
            
            # Check what the view shows for this issue
            cursor.execute(f"""
                SELECT 
                    Building_Level,
                    Clash_Level,
                    Location,
                    Phase,
                    Priority,
                    custom_attributes_json
                FROM dbo.vw_issues_expanded
                WHERE issue_id = '{issue_id}'
            """)
            
            view_row = cursor.fetchone()
            if view_row:
                print(f'\n  View output for this issue:')
                print(f'    Building Level: {view_row[0] if view_row[0] else "NULL"}')
                print(f'    Clash Level:    {view_row[1] if view_row[1] else "NULL"}')
                print(f'    Location:       {view_row[2] if view_row[2] else "NULL"}')
                print(f'    Phase:          {view_row[3] if view_row[3] else "NULL"}')
                print(f'    Priority:       {view_row[4] if view_row[4] else "NULL"}')
                if view_row[5]:
                    print(f'    JSON:           {view_row[5][:200]}...')
                else:
                    print(f'    JSON:           NULL')
    
    conn.close()

if __name__ == '__main__':
    investigate_mel071_mel081()
