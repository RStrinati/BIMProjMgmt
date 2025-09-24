from database import connect_to_db

def analyze_project_aliases_relationship():
    """Analyze the relationship between projects and project_aliases tables"""
    conn = connect_to_db()
    if conn is None:
        print("❌ Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        print("🔍 ANALYZING PROJECT-ALIASES RELATIONSHIP")
        print("=" * 60)
        
        # Check the structure of project_aliases more carefully
        print("📋 Project Aliases Table Structure:")
        cursor.execute("SELECT * FROM project_aliases")
        alias_data = cursor.fetchall()
        print(f"Columns: alias_name, pm_project_id")
        print(f"Total aliases: {len(alias_data)}")
        
        print("\n📝 All Project Aliases:")
        print(f"{'Alias Name':<30} {'PM Project ID':<15}")
        print("-" * 50)
        for alias in alias_data:
            print(f"{alias[0]:<30} {alias[1]:<15}")
        
        # Try to match with projects table
        print(f"\n🎯 MATCHING WITH PROJECTS TABLE:")
        cursor.execute("""
            SELECT 
                p.project_id,
                p.project_name,
                pa.alias_name
            FROM projects p
            INNER JOIN project_aliases pa ON p.project_id = pa.pm_project_id
            ORDER BY p.project_id
        """)
        
        matches = cursor.fetchall()
        if matches:
            print(f"{'Project ID':<12} {'Project Name':<20} {'Alias Name':<30}")
            print("-" * 65)
            for match in matches:
                print(f"{match[0]:<12} {match[1]:<20} {match[2]:<30}")
        else:
            print("❌ No matches found")
            
        # Check which projects from issues view might have aliases
        print(f"\n🔍 CHECKING ISSUES VIEW PROJECT NAMES AGAINST ALIASES:")
        cursor.execute("SELECT DISTINCT project_name FROM vw_ProjectManagement_AllIssues ORDER BY project_name")
        issue_projects = [row[0] for row in cursor.fetchall()]
        
        alias_names = [alias[0] for alias in alias_data]
        
        print(f"Issues View Projects that match aliases:")
        for issue_project in issue_projects:
            if issue_project in alias_names:
                # Find the corresponding pm_project_id
                matching_alias = next(alias for alias in alias_data if alias[0] == issue_project)
                pm_id = matching_alias[1]
                
                # Get the actual project name
                cursor.execute("SELECT project_name FROM projects WHERE project_id = ?", (pm_id,))
                actual_project = cursor.fetchone()
                actual_name = actual_project[0] if actual_project else "NOT FOUND"
                
                print(f"  ✅ '{issue_project}' -> PM ID {pm_id} -> '{actual_name}'")
        
        # Check for partial matches or similar names
        print(f"\n🔍 LOOKING FOR PARTIAL MATCHES:")
        for issue_project in issue_projects:
            for alias in alias_data:
                alias_name = alias[0]
                if (issue_project.lower() in alias_name.lower() or 
                    alias_name.lower() in issue_project.lower()) and issue_project != alias_name:
                    pm_id = alias[1]
                    cursor.execute("SELECT project_name FROM projects WHERE project_id = ?", (pm_id,))
                    actual_project = cursor.fetchone()
                    actual_name = actual_project[0] if actual_project else "NOT FOUND"
                    print(f"  🔸 '{issue_project}' ~= '{alias_name}' -> PM ID {pm_id} -> '{actual_name}'")
                    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_project_aliases_relationship()