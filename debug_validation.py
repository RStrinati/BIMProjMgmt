"""Debug validation mapping"""
from database_pool import get_db_connection

with get_db_connection("RevitHealthCheckDB") as conn:
    cursor = conn.cursor()
    
    # Check actual values with the JOIN
    cursor.execute('''
        SELECT TOP 5
            h.strRvtFileName,
            hp.validation_status,
            CASE WHEN hp.validation_status IS NULL THEN 'NULL' ELSE 'NOT NULL' END as is_null
        FROM vw_LatestRvtFiles h
        LEFT JOIN (
            SELECT 
                strRvtFileName,
                validation_status,
                ROW_NUMBER() OVER (PARTITION BY strRvtFileName ORDER BY validated_date DESC, nId DESC) as rn
            FROM tblRvtProjHealth
        ) hp
            ON h.strRvtFileName = hp.strRvtFileName
            AND hp.rn = 1
        WHERE h.pm_project_id = 2
    ''')
    
    for row in cursor.fetchall():
        val_status = row[1]
        if val_status:
            print(f'{row[0]}: validation_status="{val_status}" (type: {type(val_status).__name__})')
        else:
            print(f'{row[0]}: validation_status=NULL')
    
    cursor.close()
