"""Check tblRvtProjHealth columns and check what we need for joining"""
from database_pool import get_db_connection

print("=== tblRvtProjHealth sample data ===")
with get_db_connection("RevitHealthCheckDB") as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT TOP 3 strRvtFileName, strProjectName, strClientName, discipline_full_name, validation_status, ConvertedExportedDate FROM tblRvtProjHealth ORDER BY validated_date DESC')
    
    rows = cursor.fetchall()
    for row in rows:
        print(f'File: {row[0]}, Project: {row[1]}, Client: {row[2]}, Disc: {row[3]}, Validation: {row[4]}, Date: {row[5]}')
    cursor.close()

print("\n=== vw_LatestRvtFiles sample data ===")
with get_db_connection("RevitHealthCheckDB") as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT TOP 3 strRvtFileName, project_name, discipline_full_name, ConvertedExportedDate, pm_project_id FROM vw_LatestRvtFiles')
    
    rows = cursor.fetchall()
    for row in rows:
        print(f'File: {row[0]}, Project: {row[1]}, Disc: {row[2]}, Date: {row[3]}, pm_project_id: {row[4]}')
    cursor.close()

print("\n=== Test JOIN ===")
with get_db_connection("RevitHealthCheckDB") as conn:
    cursor = conn.cursor()
    cursor.execute('''
        SELECT TOP 1
            h.strRvtFileName,
            h.project_name,
            hp.validation_status
        FROM vw_LatestRvtFiles h
        LEFT JOIN tblRvtProjHealth hp
            ON h.strRvtFileName = hp.strRvtFileName
    ''')
    
    row = cursor.fetchone()
    if row:
        print(f'File: {row[0]}, Project: {row[1]}, Validation: {row[2]}')
    cursor.close()
