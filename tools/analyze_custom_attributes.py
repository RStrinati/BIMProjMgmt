"""
Analyze custom attributes in ACC database and generate SQL view with expanded columns.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from database import connect_to_db
from config import ACC_DB

def get_all_custom_attribute_names():
    """Extract all unique custom attribute names from the ACC database."""
    conn = connect_to_db(ACC_DB)
    if conn is None:
        print("❌ Failed to connect to database")
        return []
    
    try:
        cursor = conn.cursor()
        print("📊 Analyzing custom_attributes_json in vw_issues_expanded...")
        
        cursor.execute("""
            SELECT custom_attributes_json
            FROM [dbo].[vw_issues_expanded]
            WHERE custom_attributes_json IS NOT NULL
        """)
        
        all_attrs = set()
        sample_values = {}
        row_count = 0
        
        for row in cursor.fetchall():
            row_count += 1
            try:
                attrs = json.loads(row[0])
                if isinstance(attrs, dict):
                    for key, value in attrs.items():
                        all_attrs.add(key)
                        if key not in sample_values:
                            sample_values[key] = value
                elif isinstance(attrs, list):
                    for item in attrs:
                        if isinstance(item, dict):
                            if 'name' in item:
                                all_attrs.add(item['name'])
                                if item['name'] not in sample_values:
                                    sample_values[item['name']] = item.get('value', '')
                            else:
                                for key, value in item.items():
                                    all_attrs.add(key)
                                    if key not in sample_values:
                                        sample_values[key] = value
            except (json.JSONDecodeError, TypeError) as e:
                continue
        
        print(f"✅ Analyzed {row_count} rows with custom attributes")
        return sorted(all_attrs), sample_values
    finally:
        conn.close()

def sanitize_column_name(name):
    """Sanitize attribute name for SQL column usage."""
    # Replace spaces and special characters with underscores
    sanitized = name.replace(' ', '_').replace('-', '_').replace('.', '_')
    sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '_')
    
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = 'attr_' + sanitized
    
    return sanitized

def generate_sql_view(attribute_names):
    """Generate SQL to create/alter view with custom attribute columns."""
    
    column_definitions = []
    for attr_name in attribute_names:
        col_name = sanitize_column_name(attr_name)
        # JSON structure is an array: [{"name":"Priority","value":"Major"}]
        # Use JSON_QUERY + OPENJSON to extract value where name matches
        column_definitions.append(f"""    (
        SELECT TOP 1 [value]
        FROM OPENJSON(i.custom_attributes_json)
        WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
        WHERE [name] = '{attr_name}'
    ) AS [{col_name}]""")
    
    sql = f"""-- Auto-generated view with custom attributes expanded
-- Generated: {os.path.basename(__file__)}
-- JSON Structure: Array of objects with 'name' and 'value' properties

CREATE OR ALTER VIEW [dbo].[vw_issues_expanded_custom_attrs] AS
SELECT 
    i.[issue_id],
    i.[display_id],
    i.[title],
    i.[status],
    i.[due_date],
    i.[description],
    i.[created_at],
    i.[closed_at],
    i.[clash_group_id],
    i.[clash_test_id],
    i.[clash_status],
    i.[clash_created_at],
    i.[clash_title],
    i.[clash_description],
    i.[latest_comment],
    i.[latest_comment_by],
    i.[latest_comment_at],
    i.[location_id],
    i.[location_name],
    i.[location_parent_id],
    i.[location_tree_name],
    i.[building_name],
    i.[level_name],
    i.[root_location],
    i.[created_week_start],
    i.[created_week_label],
    i.[closed_week_start],
    i.[closed_week_label],
    i.[raw_level],
    i.[normalized_level],
    i.[is_active_issue],
    i.[is_active_over_30_days],
    i.[is_closed_last_14_days],
    i.[is_closed_last_7_days],
    i.[is_opened_this_week],
    i.[is_closed_this_week],
    i.[assignee_display_name],
    i.[Discipline],
    i.[Company],
    i.[project_id],
    i.[project_name],
    i.[pm_project_id],
    i.[custom_attributes_json],
    i.[assignee_id],
    -- Custom Attributes Expanded
{',\n'.join(column_definitions)}
FROM [dbo].[vw_issues_expanded] i;
"""
    return sql

def create_view_in_database(sql):
    """Execute the SQL to create the view in the database."""
    conn = connect_to_db(ACC_DB)
    if conn is None:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        print("\n🔧 Creating/updating view [dbo].[vw_issues_expanded_custom_attrs]...")
        cursor.execute(sql)
        conn.commit()
        print("✅ View created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating view: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("="*70)
    print("🔍 CUSTOM ATTRIBUTES ANALYZER")
    print("="*70)
    
    attrs, sample_values = get_all_custom_attribute_names()
    
    if not attrs:
        print("\n⚠️  No custom attributes found in the database.")
        sys.exit(1)
    
    print(f"\n📋 Found {len(attrs)} unique custom attributes:\n")
    for i, attr in enumerate(attrs, 1):
        sample = sample_values.get(attr, 'N/A')
        # Truncate long samples
        if isinstance(sample, str) and len(sample) > 50:
            sample = sample[:47] + "..."
        print(f"  {i:2d}. {attr:30s} (sample: {sample})")
    
    print("\n" + "="*70)
    print("📝 GENERATING SQL VIEW")
    print("="*70)
    
    sql = generate_sql_view(attrs)
    
    # Save SQL to file
    sql_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                            'sql', 'create_vw_issues_expanded_custom_attrs.sql')
    os.makedirs(os.path.dirname(sql_file), exist_ok=True)
    
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(sql)
    
    print(f"\n💾 SQL saved to: {sql_file}")
    print("\nSQL Preview:")
    print("-" * 70)
    # Show first 20 lines of SQL
    lines = sql.split('\n')
    for line in lines[:20]:
        print(line)
    if len(lines) > 20:
        print(f"... ({len(lines) - 20} more lines)")
    
    print("\n" + "="*70)
    response = input("\n❓ Create/update this view in the database? (y/n): ")
    
    if response.lower() == 'y':
        if create_view_in_database(sql):
            print("\n" + "="*70)
            print("✅ SUCCESS!")
            print("="*70)
            print("\nYou can now query the new view:")
            print("  SELECT * FROM [acc_data_schema].[dbo].[vw_issues_expanded_custom_attrs]")
            print("\nCustom attribute columns are now available as regular columns!")
        else:
            print("\n❌ Failed to create view. Check the SQL file and run manually if needed.")
    else:
        print("\n⏭️  Skipped database update. SQL file is ready for manual execution.")
