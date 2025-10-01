#!/usr/bin/env python3
"""
Debug script to investigate template lookup issues
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from database import connect_to_db
from review_management_service import ReviewManagementService

def debug_template_lookup():
    """Debug template lookup issues"""
    print("🔍 Debugging template lookup...")
    
    # Connect to database
    conn = connect_to_db()
    if conn is None:
        print("❌ Failed to connect to database")
        return
    
    try:
        service = ReviewManagementService(conn)
        
        # 1. Check what templates are available
        print("\n1. Available templates in JSON:")
        templates = service.get_available_templates()
        for i, template in enumerate(templates):
            print(f"  {i+1}. '{template.get('name', 'Unknown')}'")
        
        # 2. Check what template names are stored in database
        print("\n2. Template names referenced in database:")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT template_name 
            FROM ProjectServices 
            WHERE template_name IS NOT NULL 
            AND template_name != ''
        """)
        db_templates = cursor.fetchall()
        
        for template in db_templates:
            template_name = template[0]
            print(f"  DB: '{template_name}'")
            
            # Try to load this template
            loaded = service.get_template_by_name(template_name)
            if loaded:
                print(f"    ✅ Successfully loaded")
            else:
                print(f"    ❌ Failed to load")
                
                # Try fuzzy matching
                print(f"    🔍 Looking for similar names...")
                for avail_template in templates:
                    avail_name = avail_template.get('name', '')
                    if template_name.lower() in avail_name.lower() or avail_name.lower() in template_name.lower():
                        print(f"      📍 Similar: '{avail_name}'")
        
        # 3. Test exact character comparison
        print("\n3. Character-by-character analysis:")
        problem_template = "AWS – MEL081 STOCKMAN"
        json_template = "AWS – MEL081 STOCKMAN (Day 1)"
        
        print(f"Searching for: '{problem_template}' (len: {len(problem_template)})")
        print(f"JSON contains:  '{json_template}' (len: {len(json_template)})")
        
        print("Character comparison:")
        for i, (c1, c2) in enumerate(zip(problem_template, json_template)):
            if c1 != c2:
                print(f"  Diff at pos {i}: search='{c1}' (ord:{ord(c1)}) vs json='{c2}' (ord:{ord(c2)})")
            else:
                print(f"  Match pos {i}: '{c1}'")
        
        if len(problem_template) != len(json_template):
            print(f"  Length difference: search={len(problem_template)} vs json={len(json_template)}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    debug_template_lookup()