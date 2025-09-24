#!/usr/bin/env python3
"""
Enhanced test script for MEL01CD project issue debugging
Focused on understanding the alias mapping and issues data
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_project_combined_issues_overview, get_project_issues_by_status

# Test with the matching project MEL01CD (ID 13)
print("=== Testing with MEL01CD Project (ID 13) ===")

project_id = 13
print(f"Testing project ID: {project_id}")

try:
    issues_data = get_project_combined_issues_overview(project_id)
    if issues_data:
        summary = issues_data['summary']
        total_issues = summary.get('total_issues', 0)
        print(f"✅ Total issues: {total_issues}")
        
        if total_issues > 0:
            acc = summary.get('acc_issues', {})
            revizto = summary.get('revizto_issues', {})
            overall = summary.get('overall', {})
            
            print(f"📊 ACC: {acc.get('total', 0)} (Open: {acc.get('open', 0)}, Closed: {acc.get('closed', 0)})")
            print(f"📊 Revizto: {revizto.get('total', 0)} (Open: {revizto.get('open', 0)}, Closed: {revizto.get('closed', 0)})")
            print(f"📊 Overall: Open: {overall.get('open', 0)}, Closed: {overall.get('closed', 0)}")
            print(f"📝 Recent issues count: {len(issues_data.get('recent_issues', []))}")
            
            # Show sample recent issues
            recent = issues_data.get('recent_issues', [])[:5]
            if recent:
                print("\n🔍 Recent issues:")
                for i, issue in enumerate(recent, 1):
                    status_icon = "🔴" if issue['status'] == 'open' else "🟢"
                    print(f"  {i}. {status_icon} [{issue['source']}] {issue['issue_id']}: {issue['title'][:60]}...")
                    if issue.get('assignee'):
                        print(f"     👤 Assigned to: {issue['assignee']}")
                    print(f"     📅 Created: {issue.get('created_at', 'N/A')}")
            
            # Test detailed status views
            print(f"\n=== Testing Detailed Views ===")
            open_issues = get_project_issues_by_status(project_id, 'open')
            closed_issues = get_project_issues_by_status(project_id, 'closed')
            print(f"Open issues detailed: {len(open_issues)}")
            print(f"Closed issues detailed: {len(closed_issues)}")
            
        else:
            print("No issues found for this project")
    else:
        print("No data returned")
        
except Exception as e:
    print(f"❌ Error testing project: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")