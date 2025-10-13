import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

with get_db_connection('ProjectManagement') as conn:
cursor = conn.cursor()

# Check columns in the view
cursor.execute("SELECT TOP 1 * FROM vw_ProjectManagement_AllIssues")
columns = [col[0] for col in cursor.description]

print("Columns in vw_ProjectManagement_AllIssues:")
for col in columns:
    print(f"  - {col}")

# Check ProcessedIssues table
try:
    cursor.execute("SELECT TOP 0 * FROM ProcessedIssues")
    columns = [col[0] for col in cursor.description]
    print("\nColumns in ProcessedIssues:")
    for col in columns:
        print(f"  - {col}")
except Exception as e:
    print(f"\nProcessedIssues table check failed: {e}")
