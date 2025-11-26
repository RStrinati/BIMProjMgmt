"""
Deep analysis of custom attributes relationships:
- issues_custom_attributes (the VALUES for each issue)
- issues_custom_attributes_mappings (the DEFINITIONS of attributes per project)
- issues_custom_attribute_list_values (the LOOKUP values for list-type attributes)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

def main():
    with get_db_connection('acc_data_schema') as conn:
    if not conn:
        print("Failed to connect to acc_data_schema")
        return
    
    cursor = conn.cursor()
    
    print("=" * 120)
    print("CUSTOM ATTRIBUTES RELATIONSHIP ANALYSIS")
    print("=" * 120)
    
    # 1. Show the relationship structure
    print("\n1. TABLE STRUCTURE OVERVIEW:")
    print("-" * 120)
    print("""
    issues_custom_attributes_mappings (DEFINITIONS)
    ├── id (mapping_id) - Primary Key
    ├── bim360_project_id - Which project
    ├── title - Attribute name (e.g., "Priority", "Location")
    ├── data_type - "list", "text", "number", etc.
    └── mapped_item_type - Usually "issueSubtype"
    
    issues_custom_attribute_list_values (LOOKUP VALUES for list types)
    ├── attribute_mappings_id - FK to mappings.id
    ├── list_id - UUID for this value option
    └── list_value - The human-readable label (e.g., "Major", "Minor")
    
    issues_custom_attributes (ACTUAL VALUES per issue)
    ├── issue_id - Which issue
    ├── attribute_mapping_id - FK to mappings.id (which attribute)
    └── attribute_value - Either:
        • list_id (UUID) if data_type = 'list' → join to list_values.list_id
        • direct value if data_type = 'text', 'number', etc.
    """)
    
    # 2. Find all attribute definitions
    print("\n2. ALL CUSTOM ATTRIBUTE DEFINITIONS BY PROJECT:")
    print("-" * 120)
    
    query = """
    SELECT 
        bim360_project_id,
        title,
        data_type,
        mapped_item_type,
        id AS mapping_id,
        is_required
    FROM dbo.issues_custom_attributes_mappings
    ORDER BY title, bim360_project_id
    """
    
    cursor.execute(query)
    mappings = cursor.fetchall()
    
    print(f"{'PROJECT ID':<38} | {'ATTRIBUTE NAME':<30} | {'TYPE':<10} | {'REQUIRED':<8} | {'MAPPING ID'}")
    print("-" * 120)
    
    current_attr = None
    for row in mappings:
        proj_id = row[0]
        attr_name = row[1]
        
        # Visual separator between different attributes
        if current_attr and current_attr != attr_name:
            print("-" * 120)
        current_attr = attr_name
        
        print(f"{proj_id:<38} | {attr_name:<30} | {row[2]:<10} | {str(row[5]):<8} | {row[4]}")
    
    # 3. Show list values for each attribute
    print("\n\n3. LIST VALUES FOR EACH ATTRIBUTE:")
    print("-" * 120)
    
    query2 = """
    SELECT 
        icam.title AS attribute_name,
        icam.bim360_project_id,
        lv.list_id,
        lv.list_value
    FROM dbo.issues_custom_attributes_mappings icam
    INNER JOIN dbo.issues_custom_attribute_list_values lv
        ON icam.id = lv.attribute_mappings_id
    WHERE icam.data_type = 'list'
    ORDER BY icam.title, icam.bim360_project_id, lv.list_value
    """
    
    cursor.execute(query2)
    list_vals = cursor.fetchall()
    
    current_attr = None
    current_proj = None
    
    for row in list_vals:
        attr_name = row[0]
        proj_id = row[1]
        
        # Header for each new attribute
        if current_attr != attr_name:
            print(f"\n{'='*120}")
            print(f"ATTRIBUTE: {attr_name}")
            print(f"{'='*120}")
            current_attr = attr_name
            current_proj = None
        
        # Sub-header for each project
        if current_proj != proj_id:
            print(f"\n  Project: {proj_id}")
            print(f"  {'-'*116}")
            current_proj = proj_id
        
        print(f"    • {row[3]:<50} (ID: {row[2]})")
    
    # 4. Show actual usage - how many issues use each attribute
    print("\n\n4. ATTRIBUTE USAGE BY PROJECT:")
    print("-" * 120)
    
    query3 = """
    SELECT 
        icam.title AS attribute_name,
        icam.bim360_project_id,
        COUNT(DISTINCT ica.issue_id) AS issue_count,
        COUNT(DISTINCT ica.attribute_value) AS unique_values
    FROM dbo.issues_custom_attributes_mappings icam
    LEFT JOIN dbo.issues_custom_attributes ica
        ON icam.id = ica.attribute_mapping_id
    GROUP BY icam.title, icam.bim360_project_id
    HAVING COUNT(DISTINCT ica.issue_id) > 0
    ORDER BY icam.title, COUNT(DISTINCT ica.issue_id) DESC
    """
    
    cursor.execute(query3)
    usage = cursor.fetchall()
    
    print(f"{'ATTRIBUTE NAME':<30} | {'PROJECT ID':<38} | {'ISSUES':<10} | {'UNIQUE VALUES'}")
    print("-" * 120)
    
    for row in usage:
        print(f"{row[0]:<30} | {row[1]:<38} | {row[2]:<10} | {row[3]}")
    
    # 5. Sample of actual values
    print("\n\n5. SAMPLE ACTUAL VALUES (with resolution):")
    print("-" * 120)
    
    query4 = """
    SELECT TOP 20
        ica.issue_id,
        icam.title AS attribute_name,
        icam.data_type,
        ica.attribute_value AS raw_value,
        lv.list_value AS resolved_value
    FROM dbo.issues_custom_attributes ica
    INNER JOIN dbo.issues_custom_attributes_mappings icam
        ON ica.attribute_mapping_id = icam.id
    LEFT JOIN dbo.issues_custom_attribute_list_values lv
        ON ica.attribute_value = lv.list_id
        AND lv.attribute_mappings_id = icam.id
    ORDER BY icam.title, ica.created_at DESC
    """
    
    cursor.execute(query4)
    samples = cursor.fetchall()
    
    print(f"{'ISSUE ID':<38} | {'ATTRIBUTE':<20} | {'TYPE':<10} | {'RAW VALUE':<38} | {'RESOLVED VALUE'}")
    print("-" * 150)
    
    for row in samples:
        raw = str(row[3])[:36] if row[3] else 'NULL'
        resolved = str(row[4])[:30] if row[4] else 'NULL'
        print(f"{row[0]:<38} | {row[1]:<20} | {row[2]:<10} | {raw:<38} | {resolved}")
    
    # 6. Check for attributes with same name but different projects
    print("\n\n6. ATTRIBUTES THAT APPEAR IN MULTIPLE PROJECTS:")
    print("-" * 120)
    
    query5 = """
    SELECT 
        title,
        COUNT(DISTINCT bim360_project_id) AS project_count,
        STRING_AGG(CAST(bim360_project_id AS NVARCHAR(MAX)), ', ') AS project_ids
    FROM dbo.issues_custom_attributes_mappings
    GROUP BY title
    HAVING COUNT(DISTINCT bim360_project_id) > 1
    ORDER BY COUNT(DISTINCT bim360_project_id) DESC, title
    """
    
    cursor.execute(query5)
    multi_proj = cursor.fetchall()
    
    print(f"{'ATTRIBUTE NAME':<30} | {'# PROJECTS':<12} | {'PROJECT IDs'}")
    print("-" * 120)
    
    for row in multi_proj:
        # Truncate project IDs list if too long
        proj_ids = row[2][:80] + '...' if len(row[2]) > 80 else row[2]
        print(f"{row[0]:<30} | {row[1]:<12} | {proj_ids}")
    
    # 7. Special focus on "Priority" attribute
    print("\n\n7. DETAILED 'PRIORITY' ATTRIBUTE ANALYSIS:")
    print("-" * 120)
    
    query6 = """
    SELECT 
        icam.bim360_project_id,
        icam.title AS exact_attribute_name,
        icam.data_type,
        COUNT(DISTINCT lv.list_value) AS num_options,
        STRING_AGG(lv.list_value, ', ') AS available_options,
        COUNT(DISTINCT ica.issue_id) AS issues_using_it
    FROM dbo.issues_custom_attributes_mappings icam
    LEFT JOIN dbo.issues_custom_attribute_list_values lv
        ON icam.id = lv.attribute_mappings_id
    LEFT JOIN dbo.issues_custom_attributes ica
        ON icam.id = ica.attribute_mapping_id
    WHERE LOWER(icam.title) LIKE '%priority%'
    GROUP BY icam.bim360_project_id, icam.title, icam.data_type
    ORDER BY icam.title
    """
    
    cursor.execute(query6)
    priority_details = cursor.fetchall()
    
    if priority_details:
        print(f"{'PROJECT ID':<38} | {'EXACT NAME':<20} | {'TYPE':<10} | {'# OPTIONS':<10} | {'ISSUES':<10} | {'AVAILABLE OPTIONS'}")
        print("-" * 150)
        
        for row in priority_details:
            options = row[4][:50] + '...' if row[4] and len(row[4]) > 50 else (row[4] or 'N/A')
            print(f"{row[0]:<38} | {row[1]:<20} | {row[2]:<10} | {row[3] or 0:<10} | {row[5] or 0:<10} | {options}")
    else:
        print("No 'Priority' attributes found")
    print("\n" + "=" * 120)
    print("ANALYSIS COMPLETE")
    print("=" * 120)

if __name__ == "__main__":
    main()
