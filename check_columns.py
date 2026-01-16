"""Check vw_LatestRvtFiles columns"""
from database_pool import get_db_connection

with get_db_connection("RevitHealthCheckDB") as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT TOP 1 * FROM vw_LatestRvtFiles')
    cols = [desc[0] for desc in cursor.description]
    print('Actual columns in vw_LatestRvtFiles:')
    for i, col in enumerate(cols, 1):
        print(f'{i:2d}. [{col}]')
    
    # Also show one sample row
    cursor.execute('SELECT TOP 1 * FROM vw_LatestRvtFiles')
    row = cursor.fetchone()
    if row:
        print('\nSample row values:')
        for col, val in zip(cols, row):
            print(f'  {col}: {val}')
    
    cursor.close()
