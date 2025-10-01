"""
Comprehensive Template Management Tests

This test suite covers all template functionality in the BIM Project Management System:
1. Loading templates from service_templates.json
2. Saving new templates
3. Save As functionality from existing services
4. Template validation and error handling
5. UI integration testing
6. File system operations (create, read, update)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import json
import tempfile
import shutil
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

def create_test_template_data():
    """Create sample template data for testing"""
    return {
        "templates": [
            {
                "name": "Test Template 1",
                "sector": "Education",
                "notes": "Test template for education projects",
                "items": [
                    {
                        "phase": "Phase 1 - Design",
                        "service_code": "DES001",
                        "service_name": "Design Review Service",
                        "unit_type": "review",
                        "default_units": 5,
                        "unit_rate": 2500.0,
                        "bill_rule": "per_unit_complete",
                        "notes": "Weekly design reviews"
                    },
                    {
                        "phase": "Phase 2 - Documentation", 
                        "service_code": "DOC001",
                        "service_name": "Documentation Review",
                        "unit_type": "lump_sum",
                        "default_units": 1,
                        "lump_sum_fee": 15000.0,
                        "bill_rule": "on_completion",
                        "notes": "Complete documentation package review"
                    }
                ]
            },
            {
                "name": "Test Template 2",
                "sector": "Commercial",
                "notes": "Commercial project template",
                "items": [
                    {
                        "phase": "Phase 1 - Coordination",
                        "service_code": "COORD",
                        "service_name": "BIM Coordination",
                        "unit_type": "review",
                        "default_units": 8,
                        "unit_rate": 3000.0,
                        "bill_rule": "per_unit_complete",
                        "notes": "Bi-weekly coordination meetings"
                    }
                ]
            }
        ]
    }

class TestTemplateManagement(unittest.TestCase):
    """Test all template management functionality"""
    
    def setUp(self):
        """Set up test environment with temporary template files"""
        # Create temporary directory for test templates
        self.temp_dir = tempfile.mkdtemp()
        self.temp_template_file = os.path.join(self.temp_dir, 'service_templates.json')
        
        # Create test template data
        self.test_data = create_test_template_data()
        with open(self.temp_template_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_data, f, indent=2)
        
        # Mock database connection
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
        
        # Create service instance with mocked template file path
        from review_management_service import ReviewManagementService
        self.service = ReviewManagementService(self.mock_db)
        
        # Patch the template file path to use our temp file
        self.template_path_patch = patch.object(
            self.service, 
            '_get_template_file_path',
            return_value=self.temp_template_file
        )
        self.template_path_patch.start()
    
    def tearDown(self):
        """Clean up test environment"""
        self.template_path_patch.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_load_existing_template(self):
        """Test loading an existing template by exact name"""
        print("\n🧪 Testing load_existing_template...")
        
        # Test loading exact template name
        template = self.service.load_template("Test Template 1")
        
        self.assertIsNotNone(template)
        self.assertEqual(template['name'], "Test Template 1")
        self.assertEqual(template['sector'], "Education")
        self.assertEqual(len(template['items']), 2)
        
        # Verify first item
        first_item = template['items'][0]
        self.assertEqual(first_item['service_code'], "DES001")
        self.assertEqual(first_item['unit_rate'], 2500.0)
        
        print("✅ Load existing template test passed")
    
    def test_load_template_fuzzy_matching(self):
        """Test loading template with fuzzy name matching"""
        print("\n🧪 Testing load_template_fuzzy_matching...")
        
        # Test partial name matching
        template = self.service.load_template("Test Template")
        self.assertIsNotNone(template)
        self.assertEqual(template['name'], "Test Template 1")  # Should match first one
        
        # Test case insensitive matching
        template = self.service.load_template("test template 2")
        self.assertIsNotNone(template)
        self.assertEqual(template['name'], "Test Template 2")
        
        print("✅ Fuzzy matching test passed")
    
    def test_load_nonexistent_template(self):
        """Test loading a template that doesn't exist"""
        print("\n🧪 Testing load_nonexistent_template...")
        
        template = self.service.load_template("Nonexistent Template")
        self.assertIsNone(template)
        
        print("✅ Nonexistent template test passed")
    
    def test_get_available_templates(self):
        """Test retrieving list of available templates"""
        print("\n🧪 Testing get_available_templates...")
        
        templates = self.service.get_available_templates()
        
        self.assertEqual(len(templates), 2)
        
        # Check first template summary
        template1 = templates[0]
        self.assertEqual(template1['name'], "Test Template 1")
        self.assertEqual(template1['sector'], "Education")
        self.assertIn('item_count', template1)
        self.assertEqual(template1['item_count'], 2)
        
        # Check second template summary
        template2 = templates[1]
        self.assertEqual(template2['name'], "Test Template 2")
        self.assertEqual(template2['sector'], "Commercial")
        self.assertEqual(template2['item_count'], 1)
        
        print("✅ Get available templates test passed")
    
    def test_save_new_template(self):
        """Test saving a new template"""
        print("\n🧪 Testing save_new_template...")
        
        # Create new template data
        new_items = [
            {
                "phase": "Phase 1 - Testing",
                "service_code": "TEST001",
                "service_name": "Testing Service",
                "unit_type": "hourly",
                "default_units": 40,
                "unit_rate": 150.0,
                "bill_rule": "monthly",
                "notes": "Quality assurance testing"
            }
        ]
        
        # Save new template
        result = self.service.save_template(
            template_name="New Test Template",
            sector="Technology",
            notes="Testing-focused template",
            items=new_items,
            overwrite=False
        )
        
        self.assertTrue(result)
        
        # Verify template was saved by loading it
        saved_template = self.service.load_template("New Test Template")
        self.assertIsNotNone(saved_template)
        self.assertEqual(saved_template['name'], "New Test Template")
        self.assertEqual(saved_template['sector'], "Technology")
        self.assertEqual(len(saved_template['items']), 1)
        
        print("✅ Save new template test passed")
    
    def test_save_template_overwrite_existing(self):
        """Test overwriting an existing template"""
        print("\n🧪 Testing save_template_overwrite_existing...")
        
        # Try to save with same name without overwrite flag
        new_items = [{"phase": "Updated Phase", "service_code": "UPD001"}]
        
        result = self.service.save_template(
            template_name="Test Template 1",  # Existing name
            sector="Updated Sector",
            notes="Updated notes",
            items=new_items,
            overwrite=False
        )
        
        # Should fail without overwrite flag
        self.assertFalse(result)
        
        # Now try with overwrite flag
        result = self.service.save_template(
            template_name="Test Template 1",
            sector="Updated Sector", 
            notes="Updated notes",
            items=new_items,
            overwrite=True
        )
        
        # Should succeed with overwrite flag
        self.assertTrue(result)
        
        # Verify template was updated
        updated_template = self.service.load_template("Test Template 1")
        self.assertEqual(updated_template['sector'], "Updated Sector")
        self.assertEqual(len(updated_template['items']), 1)
        
        print("✅ Template overwrite test passed")
    
    def test_template_validation(self):
        """Test template validation functionality"""
        print("\n🧪 Testing template_validation...")
        
        # Test with valid template data
        valid_template = self.test_data['templates'][0]
        
        from review_validation import validate_template
        
        # Valid template should pass (returns list of errors, empty = valid)
        errors = validate_template(valid_template)
        self.assertEqual(len(errors), 0, f"Valid template should have no errors, got: {[str(e) for e in errors]}")
        
        # Test with invalid template (missing required fields)
        invalid_template = {
            "name": "Invalid Template"
            # Missing sector, notes, items
        }
        
        errors = validate_template(invalid_template)
        self.assertGreater(len(errors), 0, "Invalid template should have validation errors")
        
        # Check that specific required fields are flagged
        error_fields = [error.field for error in errors]
        self.assertIn('sector', error_fields)
        self.assertIn('items', error_fields)
        
        print("✅ Template validation test passed")
    
    def test_template_file_error_handling(self):
        """Test error handling for file system issues"""
        print("\n🧪 Testing template_file_error_handling...")
        
        # Test with nonexistent file
        with patch.object(self.service, '_get_template_file_path', return_value="/nonexistent/path.json"):
            templates = self.service.get_available_templates()
            self.assertEqual(len(templates), 0)
        
        # Test with corrupted JSON file
        corrupted_file = os.path.join(self.temp_dir, 'corrupted.json')
        with open(corrupted_file, 'w') as f:
            f.write('{"invalid": json syntax')
        
        with patch.object(self.service, '_get_template_file_path', return_value=corrupted_file):
            templates = self.service.get_available_templates()
            self.assertEqual(len(templates), 0)
        
        print("✅ File error handling test passed")

class TestTemplateUIIntegration(unittest.TestCase):
    """Test template UI integration and workflows"""
    
    def setUp(self):
        """Set up UI test environment"""
        # Create mock UI components
        self.mock_ui = Mock()
        self.mock_ui.template_var = Mock()
        self.mock_ui.template_combo = Mock()
        self.mock_ui.current_project_id = 1
        
        # Mock review service
        self.mock_review_service = Mock()
        self.mock_ui.review_service = self.mock_review_service
        
        # Sample template data for UI tests
        self.sample_templates = [
            {"name": "UI Test Template 1", "sector": "Education", "item_count": 3},
            {"name": "UI Test Template 2", "sector": "Commercial", "item_count": 5}
        ]
        
        self.sample_services = [
            {
                'service_id': 1,
                'service_name': 'Test Service 1',
                'phase': 'Phase 1',
                'service_code': 'TS001',
                'unit_type': 'review',
                'unit_qty': 5,
                'unit_rate': 2000.0
            },
            {
                'service_id': 2,
                'service_name': 'Test Service 2', 
                'phase': 'Phase 2',
                'service_code': 'TS002',
                'unit_type': 'lump_sum',
                'lump_sum_fee': 10000.0
            }
        ]
    
    def test_load_template_ui_workflow(self):
        """Test the complete load template UI workflow"""
        print("\n🧪 Testing load_template_ui_workflow...")
        
        # Mock template selection
        self.mock_ui.template_var.get.return_value = "UI Test Template 1 (Education)"
        
        # Mock successful template loading
        expected_template = {
            "name": "UI Test Template 1",
            "sector": "Education", 
            "notes": "Test template",
            "items": [{"service_code": "TEST001", "service_name": "Test Service"}]
        }
        self.mock_review_service.load_template.return_value = expected_template
        
        # Import and test the actual UI method
        from phase1_enhanced_ui import ReviewManagementTab
        
        # Create mock frame for the tab
        mock_frame = Mock()
        
        # Create review management tab instance
        review_tab = ReviewManagementTab(mock_frame)
        review_tab.template_var = self.mock_ui.template_var
        review_tab.review_service = self.mock_review_service
        
        # Mock the show_template_details method to avoid UI popup
        review_tab.show_template_details = Mock()
        
        # Test load template workflow
        review_tab.load_template()
        
        # Verify service method was called with correct name
        self.mock_review_service.load_template.assert_called_with("UI Test Template 1")
        
        # Verify template details popup was shown
        review_tab.show_template_details.assert_called_with(expected_template)
        
        print("✅ Load template UI workflow test passed")
    
    def test_save_as_template_ui_workflow(self):
        """Test the save as template UI workflow"""
        print("\n🧪 Testing save_as_template_ui_workflow...")
        
        # Mock current project setup
        self.mock_review_service.get_project_services.return_value = self.sample_services
        
        # Import UI class
        from phase1_enhanced_ui import ReviewManagementTab
        
        # Create review tab instance
        mock_frame = Mock()
        review_tab = ReviewManagementTab(mock_frame)
        review_tab.current_project_id = 1
        review_tab.review_service = self.mock_review_service
        
        # Mock the save dialog to avoid UI popup
        review_tab.show_save_template_dialog = Mock()
        
        # Test save as template workflow
        review_tab.save_as_template()
        
        # Verify services were retrieved
        self.mock_review_service.get_project_services.assert_called_with(1)
        
        # Verify save dialog was shown with services
        review_tab.show_save_template_dialog.assert_called_with(self.sample_services)
        
        print("✅ Save as template UI workflow test passed")
    
    def test_template_loading_initialization(self):
        """Test template loading during UI initialization"""
        print("\n🧪 Testing template_loading_initialization...")
        
        # Mock available templates
        self.mock_review_service.get_available_templates.return_value = self.sample_templates
        
        # Import UI class
        from phase1_enhanced_ui import ReviewManagementTab
        
        # Create mock frame
        mock_frame = Mock()
        
        # Create review tab (this should trigger template loading)
        review_tab = ReviewManagementTab(mock_frame)
        review_tab.review_service = self.mock_review_service
        
        # Mock template combo
        review_tab.template_combo = Mock()
        
        # Simulate loading templates (usually called during initialization)
        review_tab.load_available_templates()
        
        # Verify templates were loaded
        self.mock_review_service.get_available_templates.assert_called()
        
        print("✅ Template loading initialization test passed")

class TestTemplateEndToEndWorkflows(unittest.TestCase):
    """Test complete end-to-end template workflows"""
    
    def setUp(self):
        """Set up end-to-end test environment"""
        # Create temporary environment
        self.temp_dir = tempfile.mkdtemp()
        self.temp_template_file = os.path.join(self.temp_dir, 'service_templates.json')
        
        # Initialize with empty template file
        initial_data = {"templates": []}
        with open(self.temp_template_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)
        
        # Mock database
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
        
        # Create service instance
        from review_management_service import ReviewManagementService
        self.service = ReviewManagementService(self.mock_db)
        
        # Patch template file path
        self.template_path_patch = patch.object(
            self.service,
            '_get_template_file_path', 
            return_value=self.temp_template_file
        )
        self.template_path_patch.start()
    
    def tearDown(self):
        """Clean up end-to-end test environment"""
        self.template_path_patch.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_complete_template_lifecycle(self):
        """Test complete template lifecycle: create -> save -> load -> modify -> save"""
        print("\n🧪 Testing complete_template_lifecycle...")
        
        # Step 1: Start with empty templates
        templates = self.service.get_available_templates()
        self.assertEqual(len(templates), 0)
        
        # Step 2: Create and save first template
        template1_items = [
            {
                "phase": "Phase 1",
                "service_code": "SVC001",
                "service_name": "Service 1",
                "unit_type": "review",
                "default_units": 3,
                "unit_rate": 1500.0,
                "bill_rule": "per_unit_complete",
                "notes": "First service"
            }
        ]
        
        result = self.service.save_template(
            template_name="Lifecycle Template",
            sector="Test Sector",
            notes="Template for lifecycle testing",
            items=template1_items
        )
        self.assertTrue(result)
        
        # Step 3: Verify template exists
        templates = self.service.get_available_templates()
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]['name'], "Lifecycle Template")
        
        # Step 4: Load and verify template content
        loaded_template = self.service.load_template("Lifecycle Template")
        self.assertIsNotNone(loaded_template)
        self.assertEqual(len(loaded_template['items']), 1)
        self.assertEqual(loaded_template['items'][0]['service_code'], "SVC001")
        
        # Step 5: Modify template (add service)
        modified_items = loaded_template['items'] + [
            {
                "phase": "Phase 2",
                "service_code": "SVC002", 
                "service_name": "Service 2",
                "unit_type": "lump_sum",
                "default_units": 1,
                "lump_sum_fee": 8000.0,
                "bill_rule": "on_completion",
                "notes": "Second service"
            }
        ]
        
        # Step 6: Save modified template
        result = self.service.save_template(
            template_name="Lifecycle Template",
            sector="Updated Sector",
            notes="Updated template with two services",
            items=modified_items,
            overwrite=True
        )
        self.assertTrue(result)
        
        # Step 7: Verify modifications
        updated_template = self.service.load_template("Lifecycle Template")
        self.assertEqual(len(updated_template['items']), 2)
        self.assertEqual(updated_template['sector'], "Updated Sector")
        self.assertEqual(updated_template['items'][1]['service_code'], "SVC002")
        
        print("✅ Complete template lifecycle test passed")
    
    def test_multiple_templates_workflow(self):
        """Test workflow with multiple templates"""
        print("\n🧪 Testing multiple_templates_workflow...")
        
        # Create multiple templates
        templates_to_create = [
            {
                "name": "Education Template",
                "sector": "Education",
                "notes": "For school projects",
                "items": [{"service_code": "EDU001", "service_name": "Education Service"}]
            },
            {
                "name": "Commercial Template", 
                "sector": "Commercial",
                "notes": "For commercial projects",
                "items": [{"service_code": "COM001", "service_name": "Commercial Service"}]
            },
            {
                "name": "Healthcare Template",
                "sector": "Healthcare", 
                "notes": "For hospital projects",
                "items": [{"service_code": "HLT001", "service_name": "Healthcare Service"}]
            }
        ]
        
        # Save all templates
        for template_data in templates_to_create:
            result = self.service.save_template(
                template_name=template_data["name"],
                sector=template_data["sector"],
                notes=template_data["notes"],
                items=template_data["items"]
            )
            self.assertTrue(result)
        
        # Verify all templates exist
        available_templates = self.service.get_available_templates()
        self.assertEqual(len(available_templates), 3)
        
        # Verify each template can be loaded
        for template_data in templates_to_create:
            loaded = self.service.load_template(template_data["name"])
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded['name'], template_data["name"])
            self.assertEqual(loaded['sector'], template_data["sector"])
        
        # Test fuzzy matching works with multiple templates
        edu_template = self.service.load_template("education")
        self.assertIsNotNone(edu_template)
        self.assertEqual(edu_template['name'], "Education Template")
        
        print("✅ Multiple templates workflow test passed")

def run_comprehensive_template_tests():
    """Run all template tests with detailed reporting"""
    
    print("🚀 COMPREHENSIVE TEMPLATE MANAGEMENT TESTING")
    print("=" * 60)
    print(f"📅 Test Run Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateUIIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateEndToEndWorkflows))
    
    # Run tests with custom result handler
    class DetailedTestResult(unittest.TextTestResult):
        def __init__(self, stream, descriptions, verbosity):
            super().__init__(stream, descriptions, verbosity)
            self.test_results = []
        
        def addSuccess(self, test):
            super().addSuccess(test)
            self.test_results.append(('PASS', test._testMethodName, None))
        
        def addError(self, test, err):
            super().addError(test, err)
            self.test_results.append(('ERROR', test._testMethodName, str(err[1])))
        
        def addFailure(self, test, err):
            super().addFailure(test, err)
            self.test_results.append(('FAIL', test._testMethodName, str(err[1])))
    
    # Run tests
    runner = unittest.TextTestRunner(resultclass=DetailedTestResult, verbosity=2)
    result = runner.run(suite)
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📋 COMPREHENSIVE TEMPLATE TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    passed_tests = total_tests - len(result.failures) - len(result.errors)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    # Detailed results
    print(f"\n📊 TEST COVERAGE AREAS:")
    print("✅ Template Loading (exact name, fuzzy matching)")
    print("✅ Template Saving (new templates, overwrite existing)")
    print("✅ Template Validation (valid/invalid data)")
    print("✅ File System Operations (read, write, error handling)")
    print("✅ UI Integration (load workflow, save workflow)")
    print("✅ End-to-End Workflows (complete lifecycle, multiple templates)")
    
    if result.failures:
        print(f"\n❌ FAILED TESTS:")
        for test, error in result.failures:
            print(f"   • {test}: {error}")
    
    if result.errors:
        print(f"\n💥 ERROR TESTS:")
        for test, error in result.errors:
            print(f"   • {test}: {error}")
    
    # Final assessment
    if len(result.failures) == 0 and len(result.errors) == 0:
        print(f"\n🎉 ALL TEMPLATE TESTS PASSED!")
        print("✅ Template loading and saving functionality working correctly")
        print("✅ UI integration validated")
        print("✅ Error handling robust")
        print("✅ End-to-end workflows operational")
        print("✅ Template management system ready for production")
        return True
    else:
        print(f"\n⚠️ SOME TESTS FAILED")
        print("Please review the failed tests above and fix issues.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_template_tests()
    
    if success:
        print(f"\n🎯 Template management system fully validated!")
    else:
        print(f"\n❌ Template management system needs attention")
        sys.exit(1)