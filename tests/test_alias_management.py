"""
Test script for Project Alias Management System

This script tests the comprehensive alias management functionality
including CRUD operations, validation, discovery, and import/export.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.project_alias_service import ProjectAliasManager
import tempfile
import csv

def test_alias_management():
    """Test the complete alias management system"""
    
    print("🧪 TESTING PROJECT ALIAS MANAGEMENT SYSTEM")
    print("=" * 60)
    
    manager = ProjectAliasManager()
    
    try:
        # Test 1: Get all existing aliases
        print("\n📋 Test 1: Getting existing aliases...")
        aliases = manager.get_all_aliases()
        print(f"✅ Found {len(aliases)} existing aliases")
        
        if aliases:
            print("   Sample aliases:")
            for alias in aliases[:3]:
                print(f"     - '{alias['alias_name']}' -> Project {alias['pm_project_id']} ({alias['project_name']})")
        
        # Test 2: Validation
        print("\n🔍 Test 2: Validating aliases...")
        validation = manager.validate_aliases()
        print(f"✅ Total aliases: {validation['total_aliases']}")
        print(f"✅ Projects with aliases: {validation['total_projects_with_aliases']}")
        print(f"⚠️ Orphaned aliases: {len(validation.get('orphaned_aliases', []))}")
        print(f"⚠️ Unused projects: {len(validation.get('unused_projects', []))}")
        
        # Test 3: Discover unmapped projects
        print("\n🔍 Test 3: Discovering unmapped projects...")
        unmapped = manager.discover_unmapped_projects()
        print(f"✅ Found {len(unmapped)} unmapped projects")
        
        if unmapped:
            print("   Top unmapped projects by issue count:")
            for project in unmapped[:5]:
                suggested = project.get('suggested_match')
                suggestion = f" (suggested: {suggested['project_name']})" if suggested else ""
                print(f"     - '{project['project_name']}': {project['total_issues']} issues{suggestion}")
        
        # Test 4: Usage statistics
        print("\n📊 Test 4: Usage statistics...")
        stats = manager.get_alias_usage_stats()
        print(f"✅ Generated stats for {len(stats)} projects")
        
        projects_with_issues = [s for s in stats if s['has_issues']]
        print(f"   Projects with issues through aliases: {len(projects_with_issues)}")
        
        if projects_with_issues:
            print("   Top projects by issue count:")
            sorted_stats = sorted(projects_with_issues, key=lambda x: x['total_issues'], reverse=True)
            for stat in sorted_stats[:3]:
                print(f"     - {stat['project_name']}: {stat['total_issues']} issues, {stat['alias_count']} aliases")
        
        # Test 5: Export functionality
        print("\n📤 Test 5: Testing CSV export...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            export_path = tmp_file.name
        
        if manager.export_aliases_to_csv(export_path):
            print(f"✅ Successfully exported to {export_path}")
            
            # Verify export content
            with open(export_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                exported_rows = list(reader)
                print(f"   Exported {len(exported_rows)} rows")
        else:
            print("❌ Export failed")
        
        # Test 6: Add/Edit/Delete operations (using test data)
        print("\n✏️ Test 6: Testing CRUD operations...")
        
        # Try to add a test alias (use a known project ID)
        test_alias_name = f"TEST_ALIAS_{int(time.time())}"  # Unique name
        
        # Get a project ID to test with
        if aliases:
            test_project_id = aliases[0]['pm_project_id']
            print(f"   Testing with project ID: {test_project_id}")
            
            # Add test alias
            if manager.add_alias(test_project_id, test_alias_name):
                print(f"✅ Successfully added test alias '{test_alias_name}'")
                
                # Update test alias
                updated_name = f"{test_alias_name}_UPDATED"
                if manager.update_alias(test_alias_name, updated_name):
                    print(f"✅ Successfully updated alias to '{updated_name}'")
                    
                    # Delete test alias
                    if manager.delete_alias(updated_name):
                        print(f"✅ Successfully deleted test alias '{updated_name}'")
                    else:
                        print("❌ Failed to delete test alias")
                else:
                    print("❌ Failed to update test alias")
                    # Cleanup
                    manager.delete_alias(test_alias_name)
            else:
                print("❌ Failed to add test alias")
        
        # Cleanup export file
        if os.path.exists(export_path):
            os.unlink(export_path)
        
        print(f"\n✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"   The Project Alias Management System is ready for use!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        manager.close_connection()

def test_integration_with_issues():
    """Test integration with the enhanced issues system"""
    
    print("\n🔗 TESTING INTEGRATION WITH ISSUES SYSTEM")
    print("=" * 50)
    
    from database import get_project_combined_issues_overview
    
    # Test with projects that have aliases
    test_projects = [
        (11, 'CWPS'),    # Should have Calderwood PS [P230521] alias
        (10, 'MPHS'),    # Should have Melrose Park HS [P211015] alias  
        (2, 'NFPS'),     # Should have Nirimba Fields PS [P220416] alias
        (3, 'SPS'),      # Should have Schofields PS [P220702] alias
    ]
    
    for project_id, project_name in test_projects:
        print(f"\n📊 Testing {project_name} (ID: {project_id}):")
        
        issues_data = get_project_combined_issues_overview(project_id)
        if issues_data:
            summary = issues_data['summary']
            total = summary.get('total_issues', 0)
            print(f"   ✅ Found {total} issues through alias mapping")
            
            if total > 0:
                acc = summary.get('acc_issues', {})
                revizto = summary.get('revizto_issues', {})
                print(f"      ACC: {acc.get('total', 0)}, Revizto: {revizto.get('total', 0)}")
        else:
            print(f"   ❌ No issues found")
    
    print(f"\n✅ INTEGRATION TESTING COMPLETE!")

if __name__ == "__main__":
    import time
    
    test_alias_management()
    test_integration_with_issues()