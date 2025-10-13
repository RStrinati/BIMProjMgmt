from database import get_project_combined_issues_overview, get_projects, get_db_connection

# First check what's in the view
with get_db_connection() as conn:
    cursor = conn.cursor()
    
    print("=== Checking Combined Issues View ===")
    cursor.execute("SELECT COUNT(*) FROM vw_ProjectManagement_AllIssues")
    total_count = cursor.fetchone()[0]
    print(f"Total issues in view: {total_count}")
    
    if total_count > 0:
        cursor.execute("SELECT DISTINCT project_name FROM vw_ProjectManagement_AllIssues ORDER BY project_name")
        project_names = [row[0] for row in cursor.fetchall()]
        print(f"Projects with issues: {project_names}")
        
        # Show sample data
        cursor.execute("SELECT TOP 5 project_name, source, issue_id, title, status FROM vw_ProjectManagement_AllIssues")
        sample_issues = cursor.fetchall()
        print("\nSample issues:")
        for issue in sample_issues:
            print(f"  {issue[0]} | {issue[1]} | {issue[2]} | {issue[3][:50]}... | {issue[4]}")
            
        # Test our function with a project that has issues
        cursor.execute("SELECT TOP 1 project_id FROM vw_ProjectManagement_AllIssues")
        result = cursor.fetchone()
        if result:
            test_project_id = result[0]
            print(f"\nTesting with project ID: {test_project_id}")
            issues_data = get_project_combined_issues_overview(test_project_id)
            if issues_data:
                summary = issues_data['summary']
                print(f"Total issues: {summary['total_issues']}")
                if summary['total_issues'] > 0:
                    acc = summary.get('acc_issues', {})
                    revizto = summary.get('revizto_issues', {})
                    print(f"ACC: {acc.get('total', 0)} (Open: {acc.get('open', 0)}, Closed: {acc.get('closed', 0)})")
                    print(f"Revizto: {revizto.get('total', 0)} (Open: {revizto.get('open', 0)}, Closed: {revizto.get('closed', 0)})")
                    print(f"Recent issues count: {len(issues_data['recent_issues'])}")

print("\n=== Testing Complete ===")