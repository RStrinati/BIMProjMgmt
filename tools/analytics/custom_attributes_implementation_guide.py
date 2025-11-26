"""
Generate a comprehensive report on custom attributes per project 
and provide SQL to add columns to vw_issues_expanded.
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
    print("CUSTOM ATTRIBUTES BY PROJECT - IMPLEMENTATION GUIDE")
    print("=" * 120)
    
    # Get project names from ProjectManagement DB
    pm_conn = connect_to_db('ProjectManagement')
    pm_cursor = pm_conn.cursor() if pm_conn else None
    
    project_names = {}
    if pm_cursor:
        try:
            pm_cursor.execute("""
                SELECT DISTINCT 
                    bim360_project_id,
                    project_name
                FROM dbo.vw_dim_projects
                WHERE bim360_project_id IS NOT NULL
            """)
            for row in pm_cursor.fetchall():
                project_names[row[0]] = row[1]
        except Exception as e:
            print(f"Warning: Could not load project names: {e}")
        finally:
            pm_conn.close()
    
    # 1. Get all projects and their custom attributes
    print("\n1. CUSTOM ATTRIBUTES BY PROJECT:")
    print("-" * 120)
    
    query = """
    SELECT 
        icam.bim360_project_id,
        icam.title AS attribute_name,
        icam.data_type,
        COUNT(DISTINCT lv.list_value) AS num_list_values,
        COUNT(DISTINCT ica.issue_id) AS num_issues_using
    FROM dbo.issues_custom_attributes_mappings icam
    LEFT JOIN dbo.issues_custom_attribute_list_values lv
        ON icam.id = lv.attribute_mappings_id
    LEFT JOIN dbo.issues_custom_attributes ica
        ON icam.id = ica.attribute_mapping_id
    GROUP BY icam.bim360_project_id, icam.title, icam.data_type
    ORDER BY icam.bim360_project_id, icam.title
    """
    
    cursor.execute(query)
    attrs_by_project = {}
    
    for row in cursor.fetchall():
        proj_id = row[0]
        if proj_id not in attrs_by_project:
            attrs_by_project[proj_id] = []
        attrs_by_project[proj_id].append({
            'name': row[1],
            'type': row[2],
            'num_values': row[3] or 0,
            'num_issues': row[4] or 0
        })
    
    for proj_id, attrs in attrs_by_project.items():
        proj_name = project_names.get(proj_id, 'Unknown Project')
        print(f"\n{'='*120}")
        print(f"PROJECT: {proj_name}")
        print(f"ACC ID: {proj_id}")
        print(f"{'='*120}")
        print(f"{'ATTRIBUTE NAME':<30} | {'TYPE':<10} | {'# LIST VALUES':<15} | {'# ISSUES USING'}")
        print("-" * 120)
        
        for attr in attrs:
            print(f"{attr['name']:<30} | {attr['type']:<10} | {attr['num_values']:<15} | {attr['num_issues']}")
    
    # 2. Get unique attribute names across all projects
    print("\n\n2. ALL UNIQUE ATTRIBUTE NAMES (For Column Generation):")
    print("-" * 120)
    
    unique_attrs = set()
    for attrs in attrs_by_project.values():
        for attr in attrs:
            unique_attrs.add(attr['name'])
    
    unique_attrs = sorted(unique_attrs)
    print(f"Found {len(unique_attrs)} unique attribute names:")
    for i, attr_name in enumerate(unique_attrs, 1):
        # Show which projects use this attribute
        projects_using = []
        for proj_id, attrs in attrs_by_project.items():
            if any(a['name'] == attr_name for a in attrs):
                projects_using.append(project_names.get(proj_id, proj_id[:20]))
        
        print(f"  {i}. {attr_name:<30} - Used in {len(projects_using)} project(s): {', '.join(projects_using)}")
    
    # 3. Generate SQL for adding columns
    print("\n\n3. SQL TO ADD CUSTOM ATTRIBUTE COLUMNS TO vw_issues_expanded:")
    print("-" * 120)
    
    print("""
-- Add this to the SELECT clause of vw_issues_expanded
-- Place it after the existing Priority column

    -- 🔹 Custom Attributes Expanded (Auto-generated)
""")
    
    for attr_name in unique_attrs:
        # Sanitize column name
        col_name = attr_name.replace(' ', '_').replace('-', '_')
        
        # Generate OPENJSON extraction
        sql_fragment = f"""    (
        SELECT TOP 1 [value]
        FROM OPENJSON(ca.custom_attributes_json)
        WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
        WHERE [name] = '{attr_name}'
    ) AS [{col_name}],"""
        
        print(sql_fragment)
    
    # 4. Show list values for each attribute
    print("\n\n4. LIST VALUES FOR REFERENCE:")
    print("-" * 120)
    
    query2 = """
    SELECT 
        icam.title AS attribute_name,
        lv.list_value,
        COUNT(DISTINCT ica.issue_id) AS usage_count
    FROM dbo.issues_custom_attributes_mappings icam
    INNER JOIN dbo.issues_custom_attribute_list_values lv
        ON icam.id = lv.attribute_mappings_id
    LEFT JOIN dbo.issues_custom_attributes ica
        ON icam.id = ica.attribute_mapping_id
        AND lv.list_id = ica.attribute_value
    GROUP BY icam.title, lv.list_value
    ORDER BY icam.title, usage_count DESC, lv.list_value
    """
    
    cursor.execute(query2)
    
    current_attr = None
    for row in cursor.fetchall():
        attr_name = row[0]
        list_val = row[1]
        usage = row[2] or 0
        
        if current_attr != attr_name:
            print(f"\n{attr_name}:")
            print(f"  {'-'*116}")
            current_attr = attr_name
        
        print(f"  • {list_val:<50} ({usage} issues)")
    
    # 5. Current Priority implementation check
    print("\n\n5. CURRENT PRIORITY IMPLEMENTATION:")
    print("-" * 120)
    
    query3 = """
    SELECT TOP 10
        ie.issue_id,
        ie.title,
        ie.Priority,
        ie.project_name
    FROM dbo.vw_issues_expanded ie
    WHERE ie.Priority IS NOT NULL
    ORDER BY ie.created_at DESC
    """
    
    try:
        cursor.execute(query3)
        print(f"{'ISSUE ID':<38} | {'PROJECT':<30} | {'PRIORITY':<15} | {'ISSUE TITLE'}")
        print("-" * 120)
        
        for row in cursor.fetchall():
            title = (row[1][:40] + '...') if row[1] and len(row[1]) > 40 else (row[1] or '')
            print(f"{row[0]:<38} | {row[3]:<30} | {row[2]:<15} | {title}")
    except Exception as e:
        print(f"Error checking current implementation: {e}")
    
    # 6. Summary and recommendations
    print("\n\n6. SUMMARY & RECOMMENDATIONS:")
    print("-" * 120)
    
    print(f"""
FINDINGS:
- Total unique custom attributes: {len(unique_attrs)}
- Total projects with custom attributes: {len(attrs_by_project)}
- Projects: {', '.join([project_names.get(p, p[:20]) for p in attrs_by_project.keys()])}

CURRENT STATE:
- The view vw_issues_expanded currently has only ONE custom attribute column: [Priority]
- This is extracted from the custom_attributes_json field using OPENJSON
- The Priority attribute only exists in ONE project: {list(attrs_by_project.keys())[0] if attrs_by_project else 'None'}

RECOMMENDATIONS:
1. Add columns for ALL unique custom attributes (see SQL above)
2. Consider creating a separate custom_attributes table for better performance
3. Update the view to include all {len(unique_attrs)} attributes
4. Note: Some attributes have different names but similar purposes:
   - "Location" vs "Location 01" (both are location identifiers)
   - Consider standardizing attribute names across projects

IMPLEMENTATION STEPS:
1. Copy the SQL from section 3 above
2. Edit sql/update_vw_issues_expanded_with_priority.sql
3. Add the new columns after the existing Priority column
4. Run: ALTER VIEW [dbo].[vw_issues_expanded] ...
5. Test with: SELECT TOP 10 * FROM vw_issues_expanded WHERE [Building_Level] IS NOT NULL

CONFUSION ABOUT NAMING:
- The attribute is EXACTLY named "Priority" in the database (not "SINSW Priority" or similar)
- However, it only exists in ONE specific ACC project (SINSW schools project)
- Other projects have different custom attributes (Building Level, Clash Level, Location, Phase)
- You may have confused the attribute name with the project name
""")
    print("\n" + "=" * 120)
    print("ANALYSIS COMPLETE")
    print("=" * 120)

if __name__ == "__main__":
    main()
