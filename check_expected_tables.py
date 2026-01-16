#!/usr/bin/env python3
import pyodbc
from config import Config

cfg = Config()
conn = pyodbc.connect(
    f'Driver={{{cfg.DB_DRIVER}}};'
    f'Server={cfg.DB_SERVER};'
    f'Database={cfg.PROJECT_MGMT_DB};'
    f'UID={cfg.DB_USER};'
    f'PWD={cfg.DB_PASSWORD}'
)

try:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA='dbo' 
        AND TABLE_NAME IN ('ExpectedModels', 'ExpectedModelAliases', 'ExpectedModelVersions')
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    if tables:
        print("✓ Expected tables found:")
        for t in tables:
            print(f"  - {t}")
    else:
        print("✗ NO ExpectedModels tables found - migration not applied")
        
finally:
    conn.close()
