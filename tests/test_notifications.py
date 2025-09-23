#!/usr/bin/env python3
"""Test script to verify project creation notifications work"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import insert_project_full
from phase1_enhanced_ui import project_notification_system

# Create a mock observer to test notifications
class MockObserver:
    def __init__(self):
        self.project_list_changed_called = False
        self.project_changed_called = False

    def on_project_list_changed(self):
        self.project_list_changed_called = True
        print("✅ MockObserver: on_project_list_changed() was called")

    def on_project_changed(self, project):
        self.project_changed_called = True
        print(f"✅ MockObserver: on_project_changed({project}) was called")

# Register mock observer
mock_observer = MockObserver()
project_notification_system.register_observer(mock_observer)

print("Testing project creation notification system...")

# Create a test project
test_data = {
    'project_name': 'Notification Test Project',
    'client_id': 1,
    'status': 'Planning',
    'priority': 'Medium',
    'start_date': '2025-01-01',
    'end_date': '2025-12-31'
}

print("Creating project...")
success = insert_project_full(test_data)

if success:
    print("✅ Project created successfully")

    # Check if notification was sent
    if mock_observer.project_list_changed_called:
        print("✅ Project list change notification was sent correctly")
    else:
        print("❌ Project list change notification was NOT sent")

    # Test project change notification too
    print("Testing project change notification...")
    project_notification_system.notify_project_changed("1 - Test Project")

    if mock_observer.project_changed_called:
        print("✅ Project change notification works")
    else:
        print("❌ Project change notification failed")

else:
    print("❌ Project creation failed")