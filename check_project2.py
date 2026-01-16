"""Check what's happening with project 2 data"""
from database_pool import get_db_connection

with get_db_connection("RevitHealthCheckDB") as conn:
    cursor = conn.cursor()
    
    # Check how many rows vw_LatestRvtFiles has for project 2
    cursor.execute('SELECT COUNT(*) FROM vw_LatestRvtFiles WHERE pm_project_id = 2')
    count = cursor.fetchone()[0]
    print(f'Project 2 in vw_LatestRvtFiles: {count} rows')
    
    # Check for duplicates in vw_LatestRvtFiles
    cursor.execute('''
        SELECT strRvtFileName, COUNT(*) as cnt
        FROM vw_LatestRvtFiles
        WHERE pm_project_id = 2
        GROUP BY strRvtFileName
        HAVING COUNT(*) > 1
    ''')
    dupes = cursor.fetchall()
    print(f'\nDuplicate files in vw_LatestRvtFiles: {len(dupes)}')
    for dupe in dupes[:5]:
        print(f'  {dupe[0]} appears {dupe[1]} times')
    
    # Check tblRvtProjHealth for project 2
    cursor.execute('''
        SELECT COUNT(*) FROM tblRvtProjHealth hp
        WHERE EXISTS (
            SELECT 1 FROM vw_LatestRvtFiles h
            WHERE hp.strRvtFileName = h.strRvtFileName
            AND h.pm_project_id = 2
        )
    ''')
    health_count = cursor.fetchone()[0]
    print(f'\ntblRvtProjHealth records matching vw_LatestRvtFiles for project 2: {health_count}')
    
    # Check validation_status values
    cursor.execute('''
        SELECT DISTINCT validation_status FROM tblRvtProjHealth
        WHERE validation_status IS NOT NULL
    ''')
    statuses = cursor.fetchall()
    print(f'\nValidation status values in tblRvtProjHealth:')
    for status in statuses:
        print(f'  "{status[0]}"')
    
    cursor.close()
