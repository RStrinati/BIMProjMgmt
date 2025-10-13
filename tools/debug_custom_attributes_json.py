"""
Debug custom attributes JSON structure to understand why extraction is failing.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from database_pool import get_db_connection
from config import ACC_DB

def analyze_json_structure():
    """Examine the actual JSON structure in detail."""
    with get_db_connection(ACC_DB) as conn:
    if conn is None:
        print("❌ Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        print("="*70)
        print("🔍 EXAMINING CUSTOM_ATTRIBUTES_JSON STRUCTURE")
        print("="*70)
        
        cursor.execute("""
            SELECT TOP 10 
                issue_id,
                display_id,
                custom_attributes_json
            FROM [dbo].[vw_issues_expanded]
            WHERE custom_attributes_json IS NOT NULL
                AND custom_attributes_json != ''
                AND custom_attributes_json != 'null'
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("\n⚠️  No non-null custom_attributes_json found!")
            return
        
        print(f"\n📊 Found {len(rows)} sample rows\n")
        
        for i, row in enumerate(rows, 1):
            issue_id = row[0]
            display_id = row[1]
            json_str = row[2]
            
            print(f"\n{'='*70}")
            print(f"SAMPLE {i}: Issue {display_id} (ID: {issue_id})")
            print(f"{'='*70}")
            
            print(f"\nRAW JSON STRING:")
            print(f"{json_str[:500]}...")  # First 500 chars
            
            try:
                parsed = json.loads(json_str)
                print(f"\nJSON TYPE: {type(parsed)}")
                print(f"\nPARSED STRUCTURE:")
                print(json.dumps(parsed, indent=2)[:1000])  # Pretty print first 1000 chars
                
                # Try to find Priority in different ways
                print(f"\n🔍 SEARCHING FOR 'Priority':")
                
                if isinstance(parsed, dict):
                    print(f"  - Direct key lookup: {parsed.get('Priority', 'NOT FOUND')}")
                    print(f"  - Available keys: {list(parsed.keys())}")
                    
                    # Check if it's nested
                    for key, value in parsed.items():
                        if isinstance(value, dict) or isinstance(value, list):
                            print(f"  - Nested in '{key}': {value}")
                
                elif isinstance(parsed, list):
                    print(f"  - Array length: {len(parsed)}")
                    for idx, item in enumerate(parsed):
                        print(f"  - Item {idx}: {item}")
                        if isinstance(item, dict):
                            if 'name' in item and item['name'] == 'Priority':
                                print(f"    ✅ FOUND Priority: {item}")
                            elif 'Priority' in item:
                                print(f"    ✅ FOUND Priority key: {item['Priority']}")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON PARSE ERROR: {e}")
            
            if i >= 3:  # Show first 3 samples in detail
                break
        
        # Now test various JSON path expressions
        print("\n" + "="*70)
        print("🧪 TESTING JSON PATH EXPRESSIONS")
        print("="*70)
        
        test_paths = [
            "$.Priority",
            "$[0].Priority",
            "$[0].value",
            "$[0].name",
            "$.attributes.Priority",
            "$.customAttributes.Priority",
        ]
        
        for path in test_paths:
            cursor.execute(f"""
                SELECT TOP 5
                    display_id,
                    JSON_VALUE(custom_attributes_json, '{path}') AS extracted_value
                FROM [dbo].[vw_issues_expanded]
                WHERE custom_attributes_json IS NOT NULL
            """)
            
            results = cursor.fetchall()
            non_null = [r for r in results if r[1] is not None]
            
            print(f"\nPath: {path}")
            if non_null:
                print(f"  ✅ SUCCESS! Found {len(non_null)} non-null values")
                for r in non_null[:3]:
                    print(f"     Issue {r[0]}: {r[1]}")
            else:
                print(f"  ❌ All NULL")
        
    finally:

if __name__ == '__main__':
    analyze_json_structure()
