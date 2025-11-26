"""
Check if custom attributes are in the issues_issues table.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

with get_db_connection('acc_data_schema') as conn:
cursor = conn.cursor()

# Get all columns from issues_issues
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'issues_issues'
    ORDER BY ORDINAL_POSITION
""")

cols = cursor.fetchall()

print("ALL COLUMNS IN issues_issues:")
print("-" * 80)
custom_cols = []
for col in cols:
    print(f"{col[0]:<40} {col[1]:<20} {col[2] if col[2] else 'N/A'}")
    if 'custom' in col[0].lower() or 'attribute' in col[0].lower():
        custom_cols.append(col[0])

if custom_cols:
    print("\n" + "=" * 80)
    print("FOUND CUSTOM ATTRIBUTE COLUMNS:")
    for col in custom_cols:
        print(f"  - {col}")
        
        # Sample data
        cursor.execute(f"SELECT TOP 3 id, {col} FROM dbo.issues_issues WHERE {col} IS NOT NULL")
        samples = cursor.fetchall()
        if samples:
            for sample in samples:
                print(f"    Issue {sample[0][:20]}...: {str(sample[1])[:100]}")
else:
    print("\n❌ No custom attribute columns found in issues_issues")
