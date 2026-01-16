import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

# Apply the first migration
migration_sql_reviews = '''
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_NAME = 'ServiceReviews' AND COLUMN_NAME = 'invoice_date'
)
BEGIN
  ALTER TABLE dbo.ServiceReviews
  ADD invoice_date DATE NULL;
  PRINT 'Column invoice_date added to dbo.ServiceReviews.';
END
ELSE
BEGIN
  PRINT 'Column invoice_date already exists on dbo.ServiceReviews.';
END;

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes 
  WHERE NAME = 'idx_ServiceReviews_invoice_date' AND object_id = OBJECT_ID('dbo.ServiceReviews')
)
BEGIN
  CREATE NONCLUSTERED INDEX idx_ServiceReviews_invoice_date
    ON dbo.ServiceReviews(invoice_date);
  PRINT 'Index idx_ServiceReviews_invoice_date created.';
END;

SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'ServiceReviews' AND COLUMN_NAME = 'invoice_date';
'''

migration_sql_items = '''
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_NAME = 'ServiceItems' AND COLUMN_NAME = 'invoice_date'
)
BEGIN
  ALTER TABLE dbo.ServiceItems
  ADD invoice_date DATE NULL;
  PRINT 'Column invoice_date added to dbo.ServiceItems.';
END
ELSE
BEGIN
  PRINT 'Column invoice_date already exists on dbo.ServiceItems.';
END;

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes 
  WHERE NAME = 'idx_ServiceItems_invoice_date' AND object_id = OBJECT_ID('dbo.ServiceItems')
)
BEGIN
  CREATE NONCLUSTERED INDEX idx_ServiceItems_invoice_date
    ON dbo.ServiceItems(invoice_date);
  PRINT 'Index idx_ServiceItems_invoice_date created.';
END;

SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'ServiceItems' AND COLUMN_NAME = 'invoice_date';
'''

try:
    print('===== Applying ServiceReviews migration =====')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(migration_sql_reviews)
        try:
            rows = cursor.fetchall()
            for row in rows:
                print(f'  {row}')
        except:
            pass  # ALTER TABLE doesn't return results
        conn.commit()
    print('SUCCESS: ServiceReviews migration applied\n')
    
    print('===== Applying ServiceItems migration =====')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(migration_sql_items)
        try:
            rows = cursor.fetchall()
            for row in rows:
                print(f'  {row}')
        except:
            pass  # ALTER TABLE doesn't return results
        conn.commit()
    print('SUCCESS: ServiceItems migration applied')
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
