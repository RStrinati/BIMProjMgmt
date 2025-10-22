import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import connect_to_db

def check_service_reviews_table():
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'ServiceReviews'")
            result = cursor.fetchone()
            print('ServiceReviews table exists:', result is not None)
            if result:
                cursor.execute('SELECT COUNT(*) FROM dbo.ServiceReviews')
                count = cursor.fetchone()[0]
                print(f'Records in ServiceReviews: {count}')
            else:
                print('ServiceReviews table does not exist - need to create it')
        except Exception as e:
            print(f'Error checking table: {e}')
        finally:
            conn.close()
    else:
        print('Database connection failed')

if __name__ == '__main__':
    check_service_reviews_table()