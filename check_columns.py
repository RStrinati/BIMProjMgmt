import pyodbc
from config import Config

conn_str = f'DRIVER={{{Config.DB_DRIVER}}};SERVER={Config.DB_SERVER};DATABASE={Config.PROJECT_MGMT_DB};UID={Config.DB_USER};PWD={Config.DB_PASSWORD}'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Check what columns exist in the projects table
cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'projects' ORDER BY COLUMN_NAME")
columns = [row[0] for row in cursor.fetchall()]
print('Current projects table columns:')
for col in columns:
    print(f'  {col}')

conn.close()