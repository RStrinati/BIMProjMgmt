import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

try:
    print('===== Verifying ServiceReviews column =====')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'ServiceReviews' AND COLUMN_NAME = 'invoice_date'
        ''')
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f'  Column: {row[0]}, Type: {row[1]}, Nullable: {row[2]}')
        else:
            print('  ERROR: Column not found!')
    
    print('\n===== Verifying ServiceItems column =====')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'ServiceItems' AND COLUMN_NAME = 'invoice_date'
        ''')
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f'  Column: {row[0]}, Type: {row[1]}, Nullable: {row[2]}')
        else:
            print('  ERROR: Column not found!')
    
    print('\n===== Verification complete =====')
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
