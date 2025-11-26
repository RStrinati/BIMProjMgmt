"""
Show which projects have custom attributes and their coverage.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_pool import get_db_connection

def show_attributes_by_project():
    """Show custom attribute usage by project."""
    
    with get_db_connection('acc_data_schema') as conn:
    cursor = conn.cursor()
    
    print('=' * 100)
    print('CUSTOM ATTRIBUTES BY PROJECT')
    print('=' * 100)
    
    cursor.execute("""
        SELECT 
            COALESCE(project_name, 'NULL') as project_name,
            COUNT(CASE WHEN Building_Level IS NOT NULL THEN 1 END) as building,
            COUNT(CASE WHEN Clash_Level IS NOT NULL THEN 1 END) as clash,
            COUNT(CASE WHEN Location IS NOT NULL THEN 1 END) as location,
            COUNT(CASE WHEN Phase IS NOT NULL THEN 1 END) as phase,
            COUNT(CASE WHEN Priority IS NOT NULL THEN 1 END) as priority,
            COUNT(*) as total
        FROM dbo.vw_issues_expanded
        GROUP BY project_name
        ORDER BY project_name
    """)
    
    print()
    print(f"{'Project':<40} {'Building':>10} {'Clash':>10} {'Location':>10} {'Phase':>10} {'Priority':>10} {'Total':>10}")
    print('-' * 100)
    
    for row in cursor.fetchall():
        has_attrs = any([row[1], row[2], row[3], row[4], row[5]])
        marker = '✅' if has_attrs else '  '
        proj = row[0][:38]
        print(f'{marker} {proj:<38} {row[1]:>10} {row[2]:>10} {row[3]:>10} {row[4]:>10} {row[5]:>10} {row[6]:>10}')
    
    print()
    print('=' * 100)
    print('SAMPLE ISSUES WITH CUSTOM ATTRIBUTES')
    print('=' * 100)
    
    cursor.execute("""
        SELECT TOP 10
            project_name,
            display_id,
            title,
            Building_Level,
            Clash_Level,
            Location,
            Phase,
            Priority
        FROM dbo.vw_issues_expanded
        WHERE Building_Level IS NOT NULL
           OR Clash_Level IS NOT NULL
           OR Location IS NOT NULL
           OR Phase IS NOT NULL
           OR Priority IS NOT NULL
        ORDER BY project_name, display_id
    """)
    
    print()
    for row in cursor.fetchall():
        print(f'\nProject: {row[0]}')
        print(f'  Issue #{row[1]}: {row[2][:50]}...')
        if row[3]: print(f'    Building Level: {row[3]}')
        if row[4]: print(f'    Clash Level: {row[4]}')
        if row[5]: print(f'    Location: {row[5]}')
        if row[6]: print(f'    Phase: {row[6]}')
        if row[7]: print(f'    Priority: {row[7]}')

if __name__ == '__main__':
    show_attributes_by_project()
