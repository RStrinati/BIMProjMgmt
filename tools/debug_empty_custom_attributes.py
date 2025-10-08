"""
Debug tool to investigate why custom attribute values are not being populated.
Checks the data flow from staging to final tables.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db

def main():
    conn = connect_to_db('acc_data_schema')
    if not conn:
        print("❌ Failed to connect")
        return
    
    cursor = conn.cursor()
    
    print("=" * 120)
    print("CUSTOM ATTRIBUTES DATA FLOW INVESTIGATION")
    print("=" * 120)
    
    # Check specific issues mentioned in the user's data
    test_issues = [
        '3eddd8c2-c798-4f63-b5cf-979d445f67c7',
        '5a126ab8-df62-4f8c-9c77-fb9a1ee68f4d'
    ]
    
    test_project = '648afd41-a9ba-4909-8d4f-8f4477fe3ae8'
    
    print("\n1. STAGING TABLE - issues_custom_attributes (Source Data)")
    print("-" * 120)
    
    query1 = """
    SELECT TOP 10
        issue_id,
        bim360_project_id,
        attribute_mapping_id,
        attribute_title,
        attribute_data_type,
        attribute_value,
        LEN(attribute_value) AS value_length
    FROM acc_data_schema.staging.issues_custom_attributes
    WHERE bim360_project_id = ?
    ORDER BY issue_id
    """
    
    try:
        cursor.execute(query1, test_project)
        rows = cursor.fetchall()
        
        if rows:
            print(f"{'ISSUE ID':<38} | {'ATTRIBUTE':<20} | {'TYPE':<10} | {'VALUE':<38} | {'LEN'}")
            print("-" * 120)
            for row in rows:
                val = row[5] if row[5] else 'NULL'
                val_display = val[:36] if isinstance(val, str) else str(val)
                print(f"{row[0]:<38} | {row[3]:<20} | {row[4]:<10} | {val_display:<38} | {row[6] or 0}")
        else:
            print(f"⚠️  No staging data found for project {test_project}")
    except Exception as e:
        print(f"❌ Error querying staging: {e}")
    
    print("\n2. TARGET TABLE - dbo.issues_custom_attributes (After Merge)")
    print("-" * 120)
    
    query2 = """
    SELECT TOP 10
        issue_id,
        bim360_project_id,
        attribute_mapping_id,
        attribute_title,
        attribute_data_type,
        attribute_value,
        LEN(attribute_value) AS value_length,
        created_at
    FROM acc_data_schema.dbo.issues_custom_attributes
    WHERE bim360_project_id = ?
    ORDER BY created_at DESC
    """
    
    try:
        cursor.execute(query2, test_project)
        rows = cursor.fetchall()
        
        if rows:
            print(f"{'ISSUE ID':<38} | {'ATTRIBUTE':<20} | {'VALUE':<38} | {'LEN':5} | {'CREATED'}")
            print("-" * 120)
            for row in rows:
                val = row[5] if row[5] else 'NULL'
                val_display = val[:36] if isinstance(val, str) else str(val)
                print(f"{row[0]:<38} | {row[3]:<20} | {val_display:<38} | {row[6] or 0:5} | {row[7]}")
        else:
            print(f"⚠️  No dbo data found for project {test_project}")
    except Exception as e:
        print(f"❌ Error querying dbo: {e}")
    
    print("\n3. LIST VALUES TABLE (Available Options)")
    print("-" * 120)
    
    query3 = """
    SELECT 
        lv.attribute_mappings_id,
        lv.bim360_project_id,
        lv.list_id,
        lv.list_value
    FROM acc_data_schema.dbo.issues_custom_attribute_list_values lv
    WHERE lv.bim360_project_id = ?
    AND lv.attribute_mappings_id IN (
        SELECT DISTINCT attribute_mapping_id 
        FROM acc_data_schema.dbo.issues_custom_attributes
        WHERE bim360_project_id = ?
    )
    ORDER BY lv.list_value
    """
    
    try:
        cursor.execute(query3, test_project, test_project)
        rows = cursor.fetchall()
        
        if rows:
            print(f"{'MAPPING ID':<38} | {'LIST ID':<38} | {'LIST VALUE'}")
            print("-" * 120)
            for row in rows:
                print(f"{row[0]:<38} | {row[2]:<38} | {row[3]}")
        else:
            print(f"⚠️  No list values found for project {test_project}")
    except Exception as e:
        print(f"❌ Error querying list values: {e}")
    
    print("\n4. SPECIFIC TEST ISSUES (From User's Data)")
    print("-" * 120)
    
    for issue_id in test_issues:
        print(f"\nISSUE: {issue_id}")
        
        # Check in staging
        cursor.execute("""
            SELECT attribute_title, attribute_value
            FROM acc_data_schema.staging.issues_custom_attributes
            WHERE issue_id = ?
        """, issue_id)
        staging_row = cursor.fetchone()
        
        if staging_row:
            print(f"  STAGING: {staging_row[0]} = '{staging_row[1] or 'EMPTY'}'")
        else:
            print(f"  STAGING: ❌ Not found")
        
        # Check in dbo
        cursor.execute("""
            SELECT attribute_title, attribute_value
            FROM acc_data_schema.dbo.issues_custom_attributes
            WHERE issue_id = ?
        """, issue_id)
        dbo_row = cursor.fetchone()
        
        if dbo_row:
            print(f"  DBO: {dbo_row[0]} = '{dbo_row[1] or 'EMPTY'}'")
        else:
            print(f"  DBO: ❌ Not found")
    
    print("\n5. MAPPING TABLE CHECK")
    print("-" * 120)
    
    query5 = """
    SELECT TOP 5
        id,
        bim360_project_id,
        title,
        data_type,
        mapped_item_type
    FROM acc_data_schema.dbo.issues_custom_attributes_mappings
    WHERE bim360_project_id = ?
    """
    
    try:
        cursor.execute(query5, test_project)
        rows = cursor.fetchall()
        
        if rows:
            print(f"{'MAPPING ID':<38} | {'TITLE':<20} | {'TYPE':<10} | {'ITEM TYPE'}")
            print("-" * 120)
            for row in rows:
                print(f"{row[0]:<38} | {row[2]:<20} | {row[3]:<10} | {row[4]}")
        else:
            print(f"⚠️  No mappings found for project {test_project}")
    except Exception as e:
        print(f"❌ Error querying mappings: {e}")
    
    print("\n6. ROOT CAUSE ANALYSIS")
    print("-" * 120)
    
    # Count empty vs populated attribute_value
    query6 = """
    SELECT 
        attribute_title,
        COUNT(*) AS total_rows,
        SUM(CASE WHEN attribute_value IS NULL OR attribute_value = '' THEN 1 ELSE 0 END) AS empty_values,
        SUM(CASE WHEN attribute_value IS NOT NULL AND attribute_value <> '' THEN 1 ELSE 0 END) AS populated_values
    FROM acc_data_schema.dbo.issues_custom_attributes
    WHERE bim360_project_id = ?
    GROUP BY attribute_title
    """
    
    try:
        cursor.execute(query6, test_project)
        rows = cursor.fetchall()
        
        if rows:
            print(f"{'ATTRIBUTE':<30} | {'TOTAL':>10} | {'EMPTY':>10} | {'POPULATED':>10} | {'STATUS'}")
            print("-" * 120)
            for row in rows:
                attr_name = row[0] or 'NULL'
                total = row[1]
                empty = row[2]
                populated = row[3]
                status = "✅ OK" if populated > 0 else "❌ ALL EMPTY"
                print(f"{attr_name:<30} | {total:>10} | {empty:>10} | {populated:>10} | {status}")
        else:
            print(f"⚠️  No data found")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n7. DIAGNOSIS")
    print("-" * 120)
    
    print("""
    POSSIBLE CAUSES FOR EMPTY attribute_value:
    
    1. ❌ CSV SOURCE DATA IS MISSING VALUES
       → The ACC export doesn't include the actual selected values
       → Only includes the attribute definitions
       → Check the source CSV file: does attribute_value column have data?
    
    2. ❌ ACC EXPORT IS INCOMPLETE
       → The export from Autodesk ACC may not include custom attribute values
       → Only structure/definitions are exported, not actual issue data
    
    3. ❌ ISSUES DON'T HAVE VALUES ASSIGNED
       → Users haven't actually set these custom attributes on the issues
       → The attributes exist (definitions) but no values have been selected
    
    4. ❌ WRONG CSV FILE OR TABLE
       → The custom attribute values might be in a different CSV file
       → Check for: issues.csv, issues_attributes.csv, or similar
    
    RECOMMENDED ACTIONS:
    
    1. Check the SOURCE CSV file (issues_custom_attributes.csv):
       → Open in Excel and verify attribute_value column has data
       → If empty → ACC export is incomplete or values not set
    
    2. Check the main ISSUES CSV (issues_issues.csv):
       → Custom attributes might be embedded in a JSON column
       → Look for columns like: custom_attributes, attributes, customFields
    
    3. Re-export from ACC:
       → Make sure to include "Custom Attributes" in export options
       → Verify export settings include field values, not just definitions
    
    4. Check ACC UI:
       → Open one of the test issues in ACC web interface
       → Verify Building Level actually has a value selected
       → If not set → that's why it's empty (user hasn't filled it in)
    """)
    
    conn.close()
    print("=" * 120)

if __name__ == "__main__":
    main()
