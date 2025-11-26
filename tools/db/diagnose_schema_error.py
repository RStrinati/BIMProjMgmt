"""
Diagnose ProcessedIssues Schema Error
Identifies the column causing arithmetic overflow error
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyodbc
from config import Config

def diagnose_schema():
    """Check ProcessedIssues table schema"""
    conn = pyodbc.connect(
        f'DRIVER={Config.DB_DRIVER};SERVER={Config.DB_SERVER};DATABASE={Config.PROJECT_MGMT_DB};'
        f'UID={Config.DB_USER};PWD={Config.DB_PASSWORD}'
    )
    
    try:
        cursor = conn.cursor()
        
        # Get table schema
        print("\n" + "="*60)
        print("PROCESSEDISSUES TABLE SCHEMA")
        print("="*60)
        
        cursor.execute("""
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'ProcessedIssues' 
            ORDER BY ORDINAL_POSITION
        """)
        
        for row in cursor:
            if row.DATA_TYPE in ('varchar', 'nvarchar'):
                print(f"{row.COLUMN_NAME}: {row.DATA_TYPE}({row.CHARACTER_MAXIMUM_LENGTH})")
            elif row.DATA_TYPE in ('decimal', 'numeric'):
                print(f"{row.COLUMN_NAME}: {row.DATA_TYPE}({row.NUMERIC_PRECISION},{row.NUMERIC_SCALE})")
            else:
                print(f"{row.COLUMN_NAME}: {row.DATA_TYPE}")
        
        # Check for any numeric columns
        print("\n" + "="*60)
        print("NUMERIC COLUMNS")
        print("="*60)
        
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, NUMERIC_PRECISION, NUMERIC_SCALE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'ProcessedIssues' 
            AND DATA_TYPE IN ('decimal', 'numeric', 'int', 'bigint', 'float', 'real')
            ORDER BY ORDINAL_POSITION
        """)
        
        for row in cursor:
            print(f"{row.COLUMN_NAME}: {row.DATA_TYPE}({row.NUMERIC_PRECISION},{row.NUMERIC_SCALE})")
        
        # Sample a row from the view to see data types
        print("\n" + "="*60)
        print("SAMPLE DATA FROM SOURCE VIEW")
        print("="*60)
        
        cursor.execute("SELECT TOP 1 * FROM vw_ProjectManagement_AllIssues")
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        
        if row:
            for col, val in zip(columns, row):
                print(f"{col}: {type(val).__name__} = {repr(val)[:100]}")
        
    finally:

if __name__ == "__main__":
    diagnose_schema()
