"""
Show issues that SHOULD have custom attributes based on the 
issues_custom_attributes table.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import connect_to_db

def show_issues_with_attributes():
    """Show which issues have custom attributes."""
    
    conn = connect_to_db('acc_data_schema')
    cursor = conn.cursor()
    
    print('=' * 80)
    print('ISSUES WITH CUSTOM ATTRIBUTES IN SOURCE TABLE')
    print('=' * 80)
    
    # Get sample issues that SHOULD have attributes
    cursor.execute("""
        SELECT DISTINCT TOP 10
            ica.issue_id,
            i.display_id,
            i.title
        FROM dbo.issues_custom_attributes ica
        JOIN dbo.issues_issues i ON i.issue_id = ica.issue_id
        WHERE ica.attribute_title IN ('Clash Level', 'Building Level', 'Location', 'Phase')
        ORDER BY i.display_id
    """)
    
    issue_ids = []
    print('\nIssues that have custom attributes in dbo.issues_custom_attributes:')
    for row in cursor.fetchall():
        issue_ids.append(str(row[0]))
        print(f'  Issue #{row[1]}: {row[2][:60]}...')
        print(f'    ID: {row[0]}')
    
    # Now check these same issues in the VIEW
    print('\n' + '=' * 80)
    print('CHECKING THESE SAME ISSUES IN THE VIEW')
    print('=' * 80)
    
    for issue_id in issue_ids[:5]:  # Check first 5
        cursor.execute(f"""
            SELECT 
                issue_id,
                display_id,
                title,
                Building_Level,
                Clash_Level,
                Location,
                Phase,
                Priority,
                custom_attributes_json
            FROM dbo.vw_issues_expanded
            WHERE issue_id = '{issue_id}'
        """)
        
        row = cursor.fetchone()
        if row:
            print(f'\nIssue #{row[1]}: {row[2][:50]}...')
            print(f'  Building Level:  {row[3] if row[3] else "❌ NULL"}')
            print(f'  Clash Level:     {row[4] if row[4] else "❌ NULL"}')
            print(f'  Location:        {row[5] if row[5] else "❌ NULL"}')
            print(f'  Phase:           {row[6] if row[6] else "❌ NULL"}')
            print(f'  Priority:        {row[7] if row[7] else "NULL (ok)"}')
            
            if row[8]:
                json_preview = row[8][:200]
                print(f'  JSON: {json_preview}...')
            else:
                print(f'  JSON: ❌ NULL - THIS IS THE PROBLEM!')
        else:
            print(f'\n❌ Issue {issue_id} NOT FOUND in view!')
    
    # Count comparison
    print('\n' + '=' * 80)
    print('COUNT COMPARISON')
    print('=' * 80)
    
    cursor.execute("""
        SELECT COUNT(DISTINCT issue_id) 
        FROM dbo.issues_custom_attributes
        WHERE attribute_title IN ('Clash Level', 'Building Level', 'Location', 'Phase')
    """)
    attr_count = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*)
        FROM dbo.vw_issues_expanded
        WHERE Building_Level IS NOT NULL
           OR Clash_Level IS NOT NULL
           OR Location IS NOT NULL
           OR Phase IS NOT NULL
    """)
    view_count = cursor.fetchone()[0]
    
    print(f'\nIssues with custom attributes in source table: {attr_count}')
    print(f'Issues with custom attributes in VIEW:         {view_count}')
    
    if attr_count != view_count:
        print(f'\n❌ MISMATCH! {attr_count - view_count} issues missing from view!')
    else:
        print(f'\n✅ COUNTS MATCH!')
    
    conn.close()

if __name__ == '__main__':
    show_issues_with_attributes()
