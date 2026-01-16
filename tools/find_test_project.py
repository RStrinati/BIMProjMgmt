import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

try:
    print('===== Finding a project with reviews =====')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT TOP 1 ps.project_id
            FROM dbo.ProjectServices ps
            JOIN dbo.ServiceReviews sr ON ps.service_id = sr.service_id
            ORDER BY ps.project_id
        ''')
        row = cursor.fetchone()
        if row:
            project_id = row[0]
            print(f'Found Project ID: {project_id}')
            
            # Now get the reviews for this project
            cursor.execute(f'''
                SELECT TOP 1
                    sr.review_id,
                    sr.service_id,
                    ps.project_id,
                    sr.cycle_no,
                    sr.planned_date,
                    sr.due_date,
                    sr.status,
                    sr.disciplines,
                    sr.deliverables,
                    sr.is_billed,
                    sr.billing_amount,
                    sr.invoice_reference,
                    sr.invoice_date,
                    ps.service_name,
                    ps.service_code,
                    ps.phase
                FROM dbo.ServiceReviews sr
                JOIN dbo.ProjectServices ps ON sr.service_id = ps.service_id
                WHERE ps.project_id = {project_id}
            ''')
            review_row = cursor.fetchone()
            if review_row:
                print(f'\\n===== Review Fields =====')
                print(f'review_id: {review_row[0]}')
                print(f'service_id: {review_row[1]}')
                print(f'project_id: {review_row[2]}')
                print(f'cycle_no: {review_row[3]}')
                print(f'planned_date: {review_row[4]}')
                print(f'due_date: {review_row[5]}')
                print(f'status: {review_row[6]}')
                print(f'disciplines: {review_row[7]}')
                print(f'deliverables: {review_row[8]}')
                print(f'is_billed: {review_row[9]}')
                print(f'billing_amount: {review_row[10]}')
                print(f'invoice_reference: {review_row[11]}')
                print(f'invoice_date: {review_row[12]}')
                print(f'service_name: {review_row[13]}')
                print(f'service_code: {review_row[14]}')
                print(f'phase: {review_row[15]}')
                
                print(f'\\n===== Test URL =====')
                print(f'http://localhost:5000/api/projects/{project_id}/reviews')
        else:
            print('No projects with reviews found')
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
