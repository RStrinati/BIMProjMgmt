#!/usr/bin/env python3
"""
Test script to verify the fixed combined issues functionality
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_project_combined_issues_overview, get_projects

# Test the fixed function
print("=== Testing Fixed Combined Issues Function ===")

# Get available projects
projects = get_projects()
print(f"Available projects: {len(projects)}")

# Test with first few projects to find one with issues
for i, project in enumerate(projects[:5]):
    project_id, project_name = project[0], project[1]
    print(f"\n--- Testing Project {i+1}: {project_name} (ID: {project_id}) ---")
    
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
                
                print(f"   ACC: {acc.get('total', 0)} (Open: {acc.get('open', 0)}, Closed: {acc.get('closed', 0)})")
                print(f"   Revizto: {revizto.get('total', 0)} (Open: {revizto.get('open', 0)}, Closed: {revizto.get('closed', 0)})")
                print(f"   Overall: Open: {overall.get('open', 0)}, Closed: {overall.get('closed', 0)}")
                print(f"   Recent issues count: {len(issues_data.get('recent_issues', []))}")
                
                # Show sample recent issues
                recent = issues_data.get('recent_issues', [])[:3]
                if recent:
                    print("   Sample recent issues:")
                    for issue in recent:
                        print(f"     - {issue['source']}: {issue['title'][:50]}... [{issue['status']}]")
                
                break  # Found a project with issues, stop testing
            else:
                print(f"   No issues found for this project")
        else:
            print(f"   No data returned")
            
    except Exception as e:
        print(f"❌ Error testing project {project_id}: {str(e)}")

print("\n=== Test Complete ===")