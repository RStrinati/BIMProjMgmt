"""Check project type assignments"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_projects_full

projects = get_projects_full()
print(f'\nTotal projects: {len(projects)}\n')

for p in projects[:10]:
    print(f"ID: {p['project_id']}, Name: {p['project_name']}, Type ID: {p.get('type_id')}, Type Name: {p.get('project_type')}")
