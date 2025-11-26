"""
Check schema compatibility between source view and ProcessedIssues table
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

with get_db_connection('ProjectManagement') as conn:
cursor = conn.cursor()

print("="*70)
print("SCHEMA COMPATIBILITY CHECK")
print("="*70)

# Check source view columns and types
print("\n1. Source View (vw_ProjectManagement_AllIssues):")
print("-"*70)
cursor.execute("""
    SELECT TOP 1 
        issue_id,
        project_id,
        source
    FROM vw_ProjectManagement_AllIssues
""")

row = cursor.fetchone()
if row:
    print(f"Sample issue_id: {row[0]} (type: {type(row[0]).__name__})")
    print(f"Sample project_id: {row[1]} (type: {type(row[1]).__name__})")
    print(f"Sample source: {row[2]} (type: {type(row[2]).__name__})")

# Check ProcessedIssues table schema
print("\n2. ProcessedIssues Table Schema:")
print("-"*70)
cursor.execute("""
    SELECT 
        COLUMN_NAME, 
        DATA_TYPE, 
        CHARACTER_MAXIMUM_LENGTH,
        IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ProcessedIssues'
    AND COLUMN_NAME IN ('source_issue_id', 'project_id', 'source')
    ORDER BY ORDINAL_POSITION
""")

for row in cursor.fetchall():
    max_len = f"({row[2]})" if row[2] else ""
    nullable = "NULL" if row[3] == 'YES' else "NOT NULL"
    print(f"  {row[0]:25s} {row[1]}{max_len:15s} {nullable}")

# Check for foreign key constraints
print("\n3. Foreign Key Constraints:")
print("-"*70)
cursor.execute("""
    SELECT 
        fk.name AS constraint_name,
        OBJECT_NAME(fk.parent_object_id) AS table_name,
        COL_NAME(fc.parent_object_id, fc.parent_column_id) AS column_name,
        OBJECT_NAME(fk.referenced_object_id) AS referenced_table,
        COL_NAME(fc.referenced_object_id, fc.referenced_column_id) AS referenced_column
    FROM sys.foreign_keys AS fk
    INNER JOIN sys.foreign_key_columns AS fc 
        ON fk.object_id = fc.constraint_object_id
    WHERE OBJECT_NAME(fk.parent_object_id) = 'ProcessedIssues'
    AND COL_NAME(fc.parent_object_id, fc.parent_column_id) IN ('project_id', 'source_issue_id')
""")

fks = cursor.fetchall()
if fks:
    for fk in fks:
        print(f"  {fk[0]}: {fk[1]}.{fk[2]} -> {fk[3]}.{fk[4]}")
else:
    print("  No foreign key constraints on project_id or source_issue_id")

# Check projects table schema
print("\n4. Projects Table Schema (for reference):")
print("-"*70)
cursor.execute("""
    SELECT 
        COLUMN_NAME, 
        DATA_TYPE, 
        CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'projects'
    AND COLUMN_NAME = 'project_id'
""")

row = cursor.fetchone()
if row:
    max_len = f"({row[2]})" if row[2] else ""
    print(f"  {row[0]:25s} {row[1]}{max_len}")

print("\n" + "="*70)
print("RECOMMENDED FIXES")
print("="*70)

# Determine what changes are needed
cursor.execute("""
    SELECT DATA_TYPE 
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ProcessedIssues' AND COLUMN_NAME = 'source_issue_id'
""")
source_issue_type = cursor.fetchone()

cursor.execute("""
    SELECT DATA_TYPE 
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ProcessedIssues' AND COLUMN_NAME = 'project_id'
""")
project_id_type = cursor.fetchone()

print("\nRequired Changes:")
if source_issue_type and source_issue_type[0] not in ['nvarchar', 'varchar', 'uniqueidentifier']:
    print("  ⚠️  source_issue_id should be NVARCHAR(255) or UNIQUEIDENTIFIER")
    
if project_id_type and project_id_type[0] not in ['uniqueidentifier', 'nvarchar']:
    print("  ⚠️  project_id should be UNIQUEIDENTIFIER (to match projects table)")

print("\n✓ Run the generated SQL script to fix the schema")
print("="*70)
