import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

try:
    print('===== Checking for test data =====')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check projects
        cursor.execute('SELECT COUNT(*) FROM dbo.Projects')
        proj_count = cursor.fetchone()[0]
        print(f'Total Projects: {proj_count}')
        
        # Check services
        cursor.execute('SELECT COUNT(*) FROM dbo.ProjectServices')
        svc_count = cursor.fetchone()[0]
        print(f'Total Services: {svc_count}')
        
        # Check reviews
        cursor.execute('SELECT COUNT(*) FROM dbo.ServiceReviews')
        rev_count = cursor.fetchone()[0]
        print(f'Total Reviews: {rev_count}')
        
        # If reviews exist, show first one
        if rev_count > 0:
            cursor.execute('''
                SELECT TOP 1 sr.review_id, sr.invoice_date, sr.invoice_reference, sr.is_billed
                FROM dbo.ServiceReviews sr
            ''')
            row = cursor.fetchone()
            print(f'\nSample Review:')
            print(f'  Review ID: {row[0]}')
            print(f'  Invoice Date: {row[1]}')
            print(f'  Invoice Reference: {row[2]}')
            print(f'  Is Billed: {row[3]}')
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
