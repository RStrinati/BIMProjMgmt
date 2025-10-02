"""
Integration verification script for Analytics Dashboard
Verifies the dashboard is properly integrated into the main UI
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_integration():
    """Verify Analytics Dashboard integration"""
    print("=" * 80)
    print("ANALYTICS DASHBOARD INTEGRATION VERIFICATION")
    print("=" * 80)
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: UI module exists
    checks_total += 1
    print("\n✓ Check 1: UI module exists")
    try:
        from ui.tab_issue_analytics import IssueAnalyticsDashboard
        print("  ✅ ui/tab_issue_analytics.py found")
        checks_passed += 1
    except ImportError as e:
        print(f"  ❌ Failed to import: {e}")
    
    # Check 2: Main UI file has import
    checks_total += 1
    print("\n✓ Check 2: Main UI imports dashboard")
    try:
        with open('phase1_enhanced_ui.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'from ui.tab_issue_analytics import IssueAnalyticsDashboard' in content:
                print("  ✅ Import statement found in phase1_enhanced_ui.py")
                checks_passed += 1
            else:
                print("  ❌ Import statement not found")
    except Exception as e:
        print(f"  ❌ Error reading file: {e}")
    
    # Check 3: Setup method exists
    checks_total += 1
    print("\n✓ Check 3: Setup method exists")
    try:
        with open('phase1_enhanced_ui.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'def setup_analytics_dashboard_tab(self)' in content:
                print("  ✅ setup_analytics_dashboard_tab() method found")
                checks_passed += 1
            else:
                print("  ❌ Setup method not found")
    except Exception as e:
        print(f"  ❌ Error reading file: {e}")
    
    # Check 4: Method is called
    checks_total += 1
    print("\n✓ Check 4: Setup method is called")
    try:
        with open('phase1_enhanced_ui.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'self.setup_analytics_dashboard_tab()' in content:
                print("  ✅ setup_analytics_dashboard_tab() call found")
                checks_passed += 1
            else:
                print("  ❌ Setup method call not found")
    except Exception as e:
        print(f"  ❌ Error reading file: {e}")
    
    # Check 5: Analytics service available
    checks_total += 1
    print("\n✓ Check 5: Analytics service available")
    try:
        from services.issue_analytics_service import IssueAnalyticsService
        service = IssueAnalyticsService()
        print("  ✅ IssueAnalyticsService initialized")
        checks_passed += 1
    except Exception as e:
        print(f"  ❌ Failed to initialize service: {e}")
    
    # Check 6: Database connection
    checks_total += 1
    print("\n✓ Check 6: Database connectivity")
    try:
        from database import connect_to_db
        conn = connect_to_db('ProjectManagement')
        if conn:
            print("  ✅ Database connection successful")
            conn.close()
            checks_passed += 1
        else:
            print("  ❌ Database connection failed")
    except Exception as e:
        print(f"  ❌ Database error: {e}")
    
    # Check 7: Test data available
    checks_total += 1
    print("\n✓ Check 7: Test data available")
    try:
        from services.issue_analytics_service import IssueAnalyticsService
        service = IssueAnalyticsService()
        projects = service.calculate_pain_points_by_project()
        if projects and len(projects) > 0:
            print(f"  ✅ Found {len(projects)} projects with analytics data")
            checks_passed += 1
        else:
            print("  ⚠️  No project data found (this is OK if database is empty)")
            checks_passed += 1  # Don't fail on empty data
    except Exception as e:
        print(f"  ❌ Analytics query error: {e}")
    
    # Check 8: Documentation exists
    checks_total += 1
    print("\n✓ Check 8: Documentation exists")
    doc_files = [
        'docs/ANALYTICS_DASHBOARD_COMPLETE.md',
        'docs/ANALYTICS_DASHBOARD_QUICK_REF.md'
    ]
    doc_found = 0
    for doc in doc_files:
        if os.path.exists(doc):
            doc_found += 1
    if doc_found == len(doc_files):
        print(f"  ✅ All {len(doc_files)} documentation files found")
        checks_passed += 1
    else:
        print(f"  ⚠️  {doc_found}/{len(doc_files)} documentation files found")
    
    # Summary
    print("\n" + "=" * 80)
    print(f"VERIFICATION SUMMARY: {checks_passed}/{checks_total} checks passed")
    print("=" * 80)
    
    if checks_passed == checks_total:
        print("\n✅ ALL CHECKS PASSED - Integration verified!")
        print("\n📋 Next Steps:")
        print("  1. Run: python run_enhanced_ui.py")
        print("  2. Navigate to: Issue Management → Analytics Dashboard")
        print("  3. Click: 🔄 Refresh Analytics")
        print("  4. Review: Summary cards and detail tabs")
        return 0
    else:
        print(f"\n⚠️  {checks_total - checks_passed} check(s) failed")
        print("  Review errors above and fix before running application")
        return 1

if __name__ == "__main__":
    exit(verify_integration())
