#!/usr/bin/env python3
"""Test script for bookmark functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database import get_project_bookmarks, add_bookmark, get_projects
    print("✅ Database imports successful")

    # Test getting projects
    projects = get_projects()
    print(f"✅ Found {len(projects)} projects")

    if projects:
        project_id = projects[0][0]
        print(f"Testing with project ID: {project_id}")

        # Test getting bookmarks
        bookmarks = get_project_bookmarks(project_id)
        print(f"✅ Found {len(bookmarks)} bookmarks for project {project_id}")

        # Test adding a bookmark
        success = add_bookmark(project_id, "Test Bookmark", "https://example.com", "Test description", "Test Category")
        if success:
            print("✅ Successfully added test bookmark")

            # Check if it was added
            bookmarks = get_project_bookmarks(project_id)
            print(f"✅ Now found {len(bookmarks)} bookmarks after adding")

        else:
            print("❌ Failed to add bookmark")

    print("✅ All bookmark tests passed!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()