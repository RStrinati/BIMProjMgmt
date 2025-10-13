#!/usr/bin/env python3
"""
Script to check name matches between projects and issues
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection, get_projects

with get_db_connection() as conn:
cursor = conn.cursor()

print("=== Project Name Comparison ===")

# Get project names from Projects table
projects = get_projects()
print("Projects table:")
for pid, pname in projects[:10]:
    print(f"  ID {pid}: '{pname}'")

print("\nProjects with issues in view:")
cursor.execute("SELECT DISTINCT project_name FROM vw_ProjectManagement_AllIssues ORDER BY project_name")
issue_project_names = [row[0] for row in cursor.fetchall()]
for pname in issue_project_names:
    print(f"  '{pname}'")

print("\n=== Looking for matches ===")
project_names_from_table = [pname for pid, pname in projects]
for issue_project in issue_project_names:
    if issue_project in project_names_from_table:
        # Find the ID
        project_id = next(pid for pid, pname in projects if pname == issue_project)
        print(f"✅ MATCH: '{issue_project}' -> ID {project_id}")
    else:
        print(f"❌ NO MATCH: '{issue_project}'")