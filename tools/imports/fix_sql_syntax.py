#!/usr/bin/env python3
"""
Quick fix for SQL Server syntax in review_management_service.py
"""

import re

def fix_sql_syntax():
    """Fix LIMIT 1 to TOP 1 and add missing parameter"""
    
    with open("review_management_service.py", "r") as f:
        content = f.read()
    
    # Fix the SQL query
    old_pattern = r'self\.cursor\.execute\("""\s*SELECT TOP 1 regeneration_signature FROM ServiceReviews\s*WHERE service_id = \?\s*LIMIT 1\s*"""\)'
    new_pattern = 'self.cursor.execute("""\n                SELECT TOP 1 regeneration_signature FROM ServiceReviews \n                WHERE service_id = ?\n            """, (service_id,))'
    
    content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE | re.DOTALL)
    
    with open("review_management_service.py", "w") as f:
        f.write(content)
    
    print("✅ Fixed SQL syntax in review_management_service.py")

if __name__ == "__main__":
    fix_sql_syntax()