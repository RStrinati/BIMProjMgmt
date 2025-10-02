"""Quick check of Projects table schema"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db
from config import Config

conn = connect_to_db(Config.PROJECT_MGMT_DB)
cursor = conn.cursor()

print("\n" + "="*60)
print("PROJECTS TABLE SCHEMA")
print("="*60)
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'Projects' 
    ORDER BY ORDINAL_POSITION
""")

for row in cursor:
    if row[2]:
        print(f"{row[0]}: {row[1]}({row[2]})")
    else:
        print(f"{row[0]}: {row[1]}")

print("\n" + "="*60)
print("CLIENTS TABLE SCHEMA")
print("="*60)
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'Clients' 
    ORDER BY ORDINAL_POSITION
""")

for row in cursor:
    if row[2]:
        print(f"{row[0]}: {row[1]}({row[2]})")
    else:
        print(f"{row[0]}: {row[1]}")

conn.close()
