#!/usr/bin/env python3
"""
Test script for the new combined issues overview functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_project_combined_issues_overview, get_project_issues_by_status, get_projects

def test_combined_issues_view():
    """Test the combined issues overview functionality"""
    print("🧪 Testing Combined Issues Overview Functionality")
    print("=" * 60)
    
    # First, get available projects
    print("\n1. Getting available projects...")
    try:
        projects = get_projects()
        if not projects:
            print("❌ No projects found in database")
            return False
        
        print(f"✅ Found {len(projects)} projects:")
        for project in projects[:3]:  # Show first 3
            print(f"   - {project[0]} - {project[1]}")
        
        # Test with first project
        first_project_id = projects[0][0]
        first_project_name = projects[0][1]
        print(f"\n2. Testing with project: {first_project_id} - {first_project_name}")
        
    except Exception as e:
        print(f"❌ Error getting projects: {e}")
        return False
    
    # Test combined issues overview
    print("\n3. Testing combined issues overview...")
    try:
        issues_data = get_project_combined_issues_overview(first_project_id)
        
        if not issues_data:
            print("⚠️ No issues data returned")
            return True
        
        print("✅ Issues overview retrieved successfully!")
        
        # Display summary
        summary = issues_data.get('summary', {})
        print(f"\nIssues Summary:")
        print(f"   Total Issues: {summary.get('total_issues', 0)}")
        
        acc_stats = summary.get('acc_issues', {})
        print(f"   ACC Issues: {acc_stats.get('total', 0)} (Open: {acc_stats.get('open', 0)}, Closed: {acc_stats.get('closed', 0)})")
        
        revizto_stats = summary.get('revizto_issues', {})
        print(f"   Revizto Issues: {revizto_stats.get('total', 0)} (Open: {revizto_stats.get('open', 0)}, Closed: {revizto_stats.get('closed', 0)})")
        
        # Display recent issues
        recent_issues = issues_data.get('recent_issues', [])
        print(f"\nRecent Issues ({len(recent_issues)}):")
        for i, issue in enumerate(recent_issues[:5]):  # Show first 5
            print(f"   {i+1}. [{issue['source']}] {issue['title'][:50]}{'...' if len(issue['title']) > 50 else ''}")
            print(f"      Status: {issue['status']}, Created: {issue['created_at']}")
        
    except Exception as e:
        print(f"❌ Error testing combined issues overview: {e}")
        return False
    
    # Test issues by status
    print("\n4. Testing issues by status...")
    try:
        open_issues = get_project_issues_by_status(first_project_id, 'open')
        closed_issues = get_project_issues_by_status(first_project_id, 'closed')
        
        print(f"✅ Open issues: {len(open_issues)}")
        print(f"✅ Closed issues: {len(closed_issues)}")
        
        if open_issues:
            print(f"\nFirst open issue:")
            issue = open_issues[0]
            print(f"   ID: {issue['issue_id']}")
            print(f"   Title: {issue['title']}")
            print(f"   Source: {issue['source']}")
            print(f"   Assignee: {issue['assignee']}")
        
    except Exception as e:
        print(f"❌ Error testing issues by status: {e}")
        return False
    
    print("\n🎉 All tests passed! Combined issues functionality is working.")
    return True

if __name__ == "__main__":
    if test_combined_issues_view():
        print("\n✅ Ready to test in the UI!")
        sys.exit(0)
    else:
        print("\n💥 Tests failed! Check the implementation.")
        sys.exit(1)