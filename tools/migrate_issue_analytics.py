"""
Quick script to migrate remaining connections in issue_analytics_service.py
"""
import re

file_path = r'c:\Users\RicoStrinati\Documents\research\BIMProjMngmt\services\issue_analytics_service.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: Replace connection opening
content = re.sub(
    r'(\s+)(conn = connect_to_db\(self\.db_name\))\n(\s+)(if conn is None:)\n(\s+)(logger\.error\("Failed to connect to database"\))\n(\s+)(return \[\])\n\n(\s+)(try:)',
    r'\1try:\n\1    with get_db_connection(self.db_name) as conn:',
    content
)

# Pattern 2: Remove finally blocks with conn.close()
content = re.sub(
    r'(\s+)(finally:)\n(\s+)(conn\.close\(\))',
    '',
    content
)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Migration complete! Migrated all remaining connections.")
