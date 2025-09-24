from database import get_project_combined_issues_overview, get_project_issues_by_status

def test_projects_with_aliases():
    """Test the enhanced functions with projects that have aliases"""
    
    # Projects that have aliases based on our analysis:
    # CWPS (ID 11) -> 'Calderwood PS [P230521]'
    # MPHS (ID 10) -> 'Melrose Park HS [P211015]' 
    # NFPS (ID 2) -> 'Nirimba Fields PS [P220416]'
    # SPS (ID 3) -> 'Schofields PS [P220702]'
    
    test_projects = [
        (11, 'CWPS', 'Calderwood PS [P230521]'),
        (10, 'MPHS', 'Melrose Park HS [P211015]'),
        (2, 'NFPS', 'Nirimba Fields PS [P220416]'),
        (3, 'SPS', 'Schofields PS [P220702]')
    ]
    
    print("🧪 TESTING ENHANCED PROJECT ISSUES FUNCTIONS")
    print("=" * 70)
    
    for project_id, project_name, expected_alias in test_projects:
        print(f"\n🔍 Testing Project: {project_name} (ID: {project_id})")
        print(f"   Expected alias: {expected_alias}")
        print("-" * 50)
        
        try:
            issues_data = get_project_combined_issues_overview(project_id)
            if issues_data:
                summary = issues_data['summary']
                total_issues = summary.get('total_issues', 0)
                print(f"✅ Total issues found: {total_issues}")
                
                if total_issues > 0:
                    acc = summary.get('acc_issues', {})
                    revizto = summary.get('revizto_issues', {})
                    overall = summary.get('overall', {})
                    
                    print(f"   📊 ACC: {acc.get('total', 0)} (Open: {acc.get('open', 0)}, Closed: {acc.get('closed', 0)})")
                    print(f"   📊 Revizto: {revizto.get('total', 0)} (Open: {revizto.get('open', 0)}, Closed: {revizto.get('closed', 0)})")
                    print(f"   📊 Overall: Open: {overall.get('open', 0)}, Closed: {overall.get('closed', 0)}")
                    
                    recent_issues = issues_data.get('recent_issues', [])
                    print(f"   📝 Recent issues: {len(recent_issues)}")
                    
                    if recent_issues:
                        print(f"   🎯 Sample recent issues:")
                        for i, issue in enumerate(recent_issues[:3], 1):
                            status_icon = "🔴" if issue['status'] == 'open' else "🟢"
                            print(f"      {i}. {status_icon} [{issue['source']}] {issue['issue_id']}: {issue['title'][:40]}...")
                    
                    # Test detailed views
                    open_count = len(get_project_issues_by_status(project_id, 'open'))
                    closed_count = len(get_project_issues_by_status(project_id, 'closed'))
                    print(f"   🔍 Detailed view verification: Open={open_count}, Closed={closed_count}")
                    
                else:
                    print(f"   ⚠️ No issues found for this project")
            else:
                print(f"   ❌ No data returned")
                
        except Exception as e:
            print(f"   ❌ Error testing project {project_id}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ ENHANCED FUNCTION TESTING COMPLETE")

if __name__ == "__main__":
    test_projects_with_aliases()