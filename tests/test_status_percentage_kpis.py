"""
Test script to verify the status percentage and KPI dashboard implementations.

This test ensures that:
1. Service status percentages are correctly calculated based on review completion
2. KPI dashboard displays accurate metrics for project review status
3. Review planning sub-tab shows proper status percentages
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date, timedelta
from unittest.mock import Mock, MagicMock
import unittest

def test_service_status_percentage_calculation():
    """Test the service review status percentage calculation"""
    
    print("🧪 Testing Service Review Status Percentage Calculation")
    print("=" * 55)
    
    # Mock the database and service
    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.cursor.return_value = mock_cursor
    
    from review_management_service import ReviewManagementService
    
    # Create service instance
    service = ReviewManagementService(mock_db)
    service.cursor = mock_cursor
    
    # Test Case 1: Service with mixed review statuses
    print("Test Case 1: Service with mixed review statuses")
    print("-" * 45)
    
    # Mock data: 10 reviews with different statuses
    # 4 completed, 2 in_progress, 3 planned, 1 cancelled
    mock_cursor.fetchall.return_value = [
        ('completed', 4),
        ('in_progress', 2),
        ('planned', 3),
        ('cancelled', 1)
    ]
    
    result = service.calculate_service_review_completion_percentage(100)
    expected = ((4 * 1.0) + (2 * 0.5) + (3 * 0.0) + (1 * 0.0)) / 10 * 100  # 50%
    
    print(f"✅ Mixed statuses completion: {result}% (Expected: {expected}%)")
    assert result == expected, f"Expected {expected}%, got {result}%"
    
    # Test Case 2: All reviews completed
    print("\nTest Case 2: All reviews completed")
    print("-" * 35)
    
    mock_cursor.fetchall.return_value = [('completed', 5)]
    result = service.calculate_service_review_completion_percentage(101)
    expected = 100.0
    
    print(f"✅ All completed: {result}% (Expected: {expected}%)")
    assert result == expected, f"Expected {expected}%, got {result}%"
    
    # Test Case 3: No reviews yet
    print("\nTest Case 3: No reviews yet")
    print("-" * 25)
    
    mock_cursor.fetchall.return_value = []
    result = service.calculate_service_review_completion_percentage(102)
    expected = 0.0
    
    print(f"✅ No reviews: {result}% (Expected: {expected}%)")
    assert result == expected, f"Expected {expected}%, got {result}%"
    
    print("\n" + "=" * 55)
    print("🎉 Service status percentage calculation tests passed!")
    
    return True

def test_project_review_kpis():
    """Test the project review KPI calculation"""
    
    print("\n🧪 Testing Project Review KPIs")
    print("=" * 35)
    
    # Mock the database and service
    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.cursor.return_value = mock_cursor
    
    from review_management_service import ReviewManagementService
    
    service = ReviewManagementService(mock_db)
    service.cursor = mock_cursor
    
    # Mock fetchone and fetchall calls for different queries
    def mock_execute_side_effect(*args):
        query = args[0]
        
        # Service count query
        if "COUNT(*) FROM ProjectServices" in query:
            mock_cursor.fetchone.return_value = [5]  # 5 services
            
        # Review statistics query
        elif "sr.status, COUNT(*) as count" in query:
            mock_cursor.fetchall.return_value = [
                ('completed', 8, 0),     # 8 completed, 0 overdue
                ('in_progress', 4, 1),   # 4 in progress, 1 overdue
                ('planned', 6, 2)        # 6 planned, 2 overdue
            ]
            
        # Upcoming reviews query
        elif "sr.planned_date BETWEEN GETDATE()" in query:
            mock_cursor.fetchall.return_value = [
                (1, date.today() + timedelta(days=2), 'planned', 'Design Review'),
                (2, date.today() + timedelta(days=5), 'in_progress', 'Construction Review')
            ]
            
        # Overdue reviews query
        elif "sr.due_date < GETDATE()" in query:
            mock_cursor.fetchall.return_value = [
                (3, date.today() - timedelta(days=5), date.today() - timedelta(days=2), 'in_progress', 'Safety Review')
            ]
    
    mock_cursor.execute.side_effect = mock_execute_side_effect
    
    # Test KPI calculation
    kpis = service.get_project_review_kpis(1)
    
    print("KPI Results:")
    print(f"✅ Total Services: {kpis['total_services']} (Expected: 5)")
    print(f"✅ Total Reviews: {kpis['total_reviews']} (Expected: 18)")
    print(f"✅ Completed Reviews: {kpis['completed_reviews']} (Expected: 8)")
    print(f"✅ In Progress Reviews: {kpis['in_progress_reviews']} (Expected: 4)")
    print(f"✅ Planned Reviews: {kpis['planned_reviews']} (Expected: 6)")
    print(f"✅ Overdue Reviews: {kpis['overdue_reviews']} (Expected: 3)")
    print(f"✅ Overall Progress: {kpis['overall_completion_percentage']}% (Expected: 55.6%)")
    
    # Verify calculations
    assert kpis['total_services'] == 5
    assert kpis['total_reviews'] == 18
    assert kpis['completed_reviews'] == 8
    assert kpis['in_progress_reviews'] == 4
    assert kpis['planned_reviews'] == 6
    assert kpis['overdue_reviews'] == 3
    
    # Check overall progress calculation: (8 + 4*0.5) / 18 * 100 = 55.6%
    expected_progress = round((8 + 4 * 0.5) / 18 * 100, 1)
    assert kpis['overall_completion_percentage'] == expected_progress
    
    print(f"\n🎉 Project review KPI calculation tests passed!")
    
    return True

def test_service_review_status_summary():
    """Test the service review status summary"""
    
    print("\n🧪 Testing Service Review Status Summary")
    print("=" * 42)
    
    # Mock the database and service
    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.cursor.return_value = mock_cursor
    
    from review_management_service import ReviewManagementService
    
    service = ReviewManagementService(mock_db)
    service.cursor = mock_cursor
    
    # Mock the query result for service status summary
    # (total, completed, in_progress, planned, overdue)
    mock_cursor.fetchone.return_value = (10, 6, 2, 2, 1)
    
    # Mock the completion percentage calculation
    def mock_calculate_completion(*args):
        return 70.0  # 70% completion
    
    service.calculate_service_review_completion_percentage = mock_calculate_completion
    
    # Test the summary
    summary = service.get_service_review_status_summary(100)
    
    print("Service Status Summary:")
    print(f"✅ Total Reviews: {summary['total_reviews']} (Expected: 10)")
    print(f"✅ Completed: {summary['completed_reviews']} (Expected: 6)")
    print(f"✅ In Progress: {summary['in_progress_reviews']} (Expected: 2)")
    print(f"✅ Planned: {summary['planned_reviews']} (Expected: 2)")
    print(f"✅ Overdue: {summary['overdue_reviews']} (Expected: 1)")
    print(f"✅ Completion %: {summary['completion_percentage']} (Expected: 70.0)")
    print(f"✅ Status Display: {summary['status_display']} (Expected: '70.0%')")
    
    # Verify the results
    assert summary['total_reviews'] == 10
    assert summary['completed_reviews'] == 6
    assert summary['in_progress_reviews'] == 2
    assert summary['planned_reviews'] == 2
    assert summary['overdue_reviews'] == 1
    assert summary['completion_percentage'] == 70.0
    assert summary['status_display'] == "70.0%"
    
    print(f"\n🎉 Service review status summary tests passed!")
    
    return True

if __name__ == "__main__":
    try:
        # Run all tests
        test_service_status_percentage_calculation()
        test_project_review_kpis()
        test_service_review_status_summary()
        
        print("\n" + "=" * 60)
        print("🏆 ALL TESTS PASSED!")
        print("✅ Status percentage calculations working correctly")
        print("✅ KPI dashboard metrics working correctly")
        print("✅ Service review status summaries working correctly")
        print("\nThe implementations are ready for use in the UI!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)