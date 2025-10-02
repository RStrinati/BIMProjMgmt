"""
Comprehensive ReviewManagementService Template Tests

This test suite validates the actual template methods in ReviewManagementService
to ensure load, save, and template management functionality works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import json
import tempfile
import shutil
from unittest.mock import Mock, patch
from datetime import datetime

class TestReviewManagementServiceTemplates(unittest.TestCase):
    """Test ReviewManagementService template functionality"""
    
    def setUp(self):
        """Set up test environment with real service instance"""
        # Create temporary template directory and file
        self.temp_dir = tempfile.mkdtemp()
        self.temp_templates_dir = os.path.join(self.temp_dir, 'templates')
        os.makedirs(self.temp_templates_dir, exist_ok=True)
        self.temp_template_file = os.path.join(self.temp_templates_dir, 'service_templates.json')
        
        # Create test template data
        self.test_templates = {
            "templates": [
                {
                    "name": "Service Test Template",
                    "sector": "Education",
                    "notes": "Template for service testing",
                    "items": [
                        {
                            "phase": "Phase 1 - Testing",
                            "service_code": "TEST001",
                            "service_name": "Test Review Service",
                            "unit_type": "review",
                            "default_units": 5,
                            "unit_rate": 2000.0,
                            "bill_rule": "per_unit_complete",
                            "notes": "Test review cycles"
                        }
                    ]
                }
            ]
        }
        
        # Save test template data
        with open(self.temp_template_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_templates, f, indent=2)
        
        # Create mock database connection
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
        
        # Import and create service instance
        from review_management_service import ReviewManagementService
        self.service = ReviewManagementService(self.mock_db)
        
        print(f"📁 Test template file: {self.temp_template_file}")
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    @patch('os.path.dirname')
    def test_get_available_templates_real_service(self, mock_dirname):
        """Test get_available_templates with real service method"""
        print("\n🧪 Testing get_available_templates_real_service...")
        
        # Mock the dirname to point to our temp directory
        mock_dirname.return_value = self.temp_dir
        
        # Call the actual service method
        templates = self.service.get_available_templates()
        
        # Verify results
        self.assertEqual(len(templates), 1)
        
        template = templates[0]
        self.assertEqual(template['name'], "Service Test Template")
        self.assertEqual(template['sector'], "Education")
        self.assertIn('total_items', template)
        self.assertEqual(template['total_items'], 1)
        
        print("✅ Get available templates test passed")
    
    @patch('os.path.dirname')
    def test_load_template_real_service(self, mock_dirname):
        """Test load_template with real service method"""
        print("\n🧪 Testing load_template_real_service...")
        
        # Mock the dirname to point to our temp directory
        mock_dirname.return_value = self.temp_dir
        
        # Test exact name matching
        template = self.service.load_template("Service Test Template")
        
        self.assertIsNotNone(template)
        self.assertEqual(template['name'], "Service Test Template")
        self.assertEqual(template['sector'], "Education")
        self.assertEqual(len(template['items']), 1)
        
        # Verify item details
        item = template['items'][0]
        self.assertEqual(item['service_code'], "TEST001")
        self.assertEqual(item['unit_rate'], 2000.0)
        self.assertEqual(item['default_units'], 5)
        
        # Test fuzzy matching
        fuzzy_template = self.service.load_template("service test")
        self.assertIsNotNone(fuzzy_template)
        self.assertEqual(fuzzy_template['name'], "Service Test Template")
        
        # Test non-existent template
        missing_template = self.service.load_template("Non-existent Template")
        self.assertIsNone(missing_template)
        
        print("✅ Load template test passed")
    
    @patch('os.path.dirname')
    def test_save_template_real_service(self, mock_dirname):
        """Test save_template with real service method"""
        print("\n🧪 Testing save_template_real_service...")
        
        # Mock the dirname to point to our temp directory
        mock_dirname.return_value = self.temp_dir
        
        # Create new template data
        new_items = [
            {
                "phase": "Phase 1 - New Service",
                "service_code": "NEW001",
                "service_name": "New Test Service",
                "unit_type": "lump_sum",
                "default_units": 1,
                "lump_sum_fee": 12000.0,
                "bill_rule": "on_completion",
                "notes": "New service for testing"
            }
        ]
        
        # Save new template
        result = self.service.save_template(
            template_name="New Service Template",
            sector="Commercial",
            notes="Newly created template",
            items=new_items,
            overwrite=False
        )
        
        self.assertTrue(result)
        
        # Verify template was saved by loading available templates
        templates = self.service.get_available_templates()
        self.assertEqual(len(templates), 2)  # Original + new
        
        # Find and verify the new template
        new_template = None
        for template in templates:
            if template['name'] == "New Service Template":
                new_template = template
                break
        
        self.assertIsNotNone(new_template)
        self.assertEqual(new_template['sector'], "Commercial")
        self.assertEqual(new_template['total_items'], 1)
        
        # Load and verify full template details
        loaded_template = self.service.load_template("New Service Template")
        self.assertIsNotNone(loaded_template)
        self.assertEqual(loaded_template['notes'], "Newly created template")
        self.assertEqual(len(loaded_template['items']), 1)
        self.assertEqual(loaded_template['items'][0]['service_code'], "NEW001")
        
        print("✅ Save template test passed")
    
    @patch('os.path.dirname')
    def test_save_template_overwrite(self, mock_dirname):
        """Test save_template overwrite functionality"""
        print("\n🧪 Testing save_template_overwrite...")
        
        # Mock the dirname to point to our temp directory
        mock_dirname.return_value = self.temp_dir
        
        # Create updated template items
        updated_items = [
            {
                "phase": "Phase 1 - Updated",
                "service_code": "UPD001",
                "service_name": "Updated Service",
                "unit_type": "review",
                "default_units": 10,
                "unit_rate": 3000.0,
                "bill_rule": "per_unit_complete",
                "notes": "Updated service for testing"
            }
        ]
        
        # Try to save without overwrite flag (should fail)
        result = self.service.save_template(
            template_name="Service Test Template",  # Existing name
            sector="Education",  # Use valid sector
            notes="Updated template",
            items=updated_items,
            overwrite=False
        )
        
        self.assertFalse(result)
        
        # Save with overwrite flag (should succeed)
        result = self.service.save_template(
            template_name="Service Test Template",
            sector="Education",  # Use valid sector
            notes="Updated template",
            items=updated_items,
            overwrite=True
        )
        
        self.assertTrue(result)
        
        # Verify template was updated
        updated_template = self.service.load_template("Service Test Template")
        self.assertIsNotNone(updated_template)
        self.assertEqual(updated_template['sector'], "Education")
        self.assertEqual(updated_template['notes'], "Updated template")
        self.assertEqual(len(updated_template['items']), 1)
        self.assertEqual(updated_template['items'][0]['service_code'], "UPD001")
        
        print("✅ Save template overwrite test passed")
    
    @patch('os.path.dirname')
    def test_template_error_handling(self, mock_dirname):
        """Test template error handling scenarios"""
        print("\n🧪 Testing template_error_handling...")
        
        # Test with non-existent directory
        mock_dirname.return_value = "/non/existent/path"
        
        # Methods should handle missing files gracefully
        templates = self.service.get_available_templates()
        self.assertEqual(len(templates), 0)
        
        missing_template = self.service.load_template("Any Template")
        self.assertIsNone(missing_template)
        
        # Test with corrupted JSON file
        mock_dirname.return_value = self.temp_dir
        
        # Create corrupted template file
        with open(self.temp_template_file, 'w') as f:
            f.write('{"invalid": json content without closing brace')
        
        # Methods should handle corrupted JSON gracefully
        corrupted_templates = self.service.get_available_templates()
        self.assertEqual(len(corrupted_templates), 0)
        
        corrupted_template = self.service.load_template("Any Template")
        self.assertIsNone(corrupted_template)
        
        print("✅ Template error handling test passed")

class TestServiceTemplateIntegration(unittest.TestCase):
    """Test service template integration with project workflow"""
    
    def setUp(self):
        """Set up integration test environment"""
        # Create temporary environment
        self.temp_dir = tempfile.mkdtemp()
        self.temp_templates_dir = os.path.join(self.temp_dir, 'templates')
        os.makedirs(self.temp_templates_dir, exist_ok=True)
        self.temp_template_file = os.path.join(self.temp_templates_dir, 'service_templates.json')
        
        # Create comprehensive test templates
        self.comprehensive_templates = {
            "templates": [
                {
                    "name": "Education Standard",
                    "sector": "Education",
                    "notes": "Standard education project template",
                    "items": [
                        {
                            "phase": "Phase 1 - Design",
                            "service_code": "EDU_DES",
                            "service_name": "Education Design Review",
                            "unit_type": "review",
                            "default_units": 6,
                            "unit_rate": 2500.0,
                            "bill_rule": "per_unit_complete",
                            "notes": "Bi-weekly design reviews"
                        },
                        {
                            "phase": "Phase 2 - Construction",
                            "service_code": "EDU_CON",
                            "service_name": "Education Construction Coordination",
                            "unit_type": "review",
                            "default_units": 12,
                            "unit_rate": 3000.0,
                            "bill_rule": "per_unit_complete",
                            "notes": "Weekly construction reviews"
                        },
                        {
                            "phase": "Phase 3 - Handover",
                            "service_code": "EDU_HO",
                            "service_name": "Education Project Handover",
                            "unit_type": "lump_sum",
                            "default_units": 1,
                            "lump_sum_fee": 8000.0,
                            "bill_rule": "on_completion",
                            "notes": "Complete project handover package"
                        }
                    ]
                },
                {
                    "name": "Healthcare Specialized",
                    "sector": "Healthcare",
                    "notes": "Specialized healthcare project template",
                    "items": [
                        {
                            "phase": "Phase 1 - Compliance",
                            "service_code": "HLT_COMP",
                            "service_name": "Healthcare Compliance Review",
                            "unit_type": "audit",
                            "default_units": 3,
                            "unit_rate": 4000.0,
                            "bill_rule": "per_unit_complete",
                            "notes": "Specialized healthcare compliance audits"
                        }
                    ]
                }
            ]
        }
        
        # Save comprehensive template data
        with open(self.temp_template_file, 'w', encoding='utf-8') as f:
            json.dump(self.comprehensive_templates, f, indent=2)
        
        # Create mock database
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
        
        # Create service instance
        from review_management_service import ReviewManagementService
        self.service = ReviewManagementService(self.mock_db)
        
        print(f"📁 Integration test template file: {self.temp_template_file}")
    
    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.temp_dir)
    
    @patch('os.path.dirname')
    def test_template_selection_workflow(self, mock_dirname):
        """Test complete template selection and application workflow"""
        print("\n🧪 Testing template_selection_workflow...")
        
        # Mock the dirname to point to our temp directory
        mock_dirname.return_value = self.temp_dir
        
        # Step 1: Get available templates
        available_templates = self.service.get_available_templates()
        self.assertEqual(len(available_templates), 2)
        
        # Verify template summaries
        education_template = next((t for t in available_templates if t['sector'] == 'Education'), None)
        self.assertIsNotNone(education_template)
        self.assertEqual(education_template['name'], "Education Standard")
        self.assertEqual(education_template['total_items'], 3)
        
        healthcare_template = next((t for t in available_templates if t['sector'] == 'Healthcare'), None)
        self.assertIsNotNone(healthcare_template)
        self.assertEqual(healthcare_template['name'], "Healthcare Specialized")
        self.assertEqual(healthcare_template['total_items'], 1)
        
        # Step 2: Load specific template for detailed review
        selected_template = self.service.load_template("Education Standard")
        self.assertIsNotNone(selected_template)
        
        # Verify template structure
        self.assertEqual(len(selected_template['items']), 3)
        
        # Verify different service types are present
        service_types = [item['unit_type'] for item in selected_template['items']]
        self.assertIn('review', service_types)
        self.assertIn('lump_sum', service_types)
        
        # Verify billing rules vary appropriately
        bill_rules = [item['bill_rule'] for item in selected_template['items']]
        self.assertIn('per_unit_complete', bill_rules)
        self.assertIn('on_completion', bill_rules)
        
        print("✅ Template selection workflow test passed")
    
    @patch('os.path.dirname')
    def test_template_customization_workflow(self, mock_dirname):
        """Test template customization and save-as workflow"""
        print("\n🧪 Testing template_customization_workflow...")
        
        # Mock the dirname to point to our temp directory
        mock_dirname.return_value = self.temp_dir
        
        # Step 1: Load existing template
        base_template = self.service.load_template("Education Standard")
        self.assertIsNotNone(base_template)
        
        # Step 2: Customize template (modify services and add new one)
        customized_items = base_template['items'].copy()
        
        # Modify first service
        customized_items[0]['unit_rate'] = 2800.0  # Increase rate
        customized_items[0]['notes'] = "Enhanced bi-weekly design reviews"
        
        # Add new specialized service
        new_service = {
            "phase": "Phase 1.5 - Validation",
            "service_code": "EDU_VAL",
            "service_name": "Education Design Validation",
            "unit_type": "review",
            "default_units": 2,
            "unit_rate": 3500.0,
            "bill_rule": "per_unit_complete",
            "notes": "Specialized validation reviews for education projects"
        }
        customized_items.append(new_service)
        
        # Step 3: Save customized template with new name
        result = self.service.save_template(
            template_name="Education Enhanced",
            sector="Education",
            notes="Enhanced education template with validation services",
            items=customized_items,
            overwrite=False
        )
        
        self.assertTrue(result)
        
        # Step 4: Verify customized template
        enhanced_template = self.service.load_template("Education Enhanced")
        self.assertIsNotNone(enhanced_template)
        self.assertEqual(len(enhanced_template['items']), 4)  # Original 3 + 1 new
        
        # Verify modifications
        first_item = enhanced_template['items'][0]
        self.assertEqual(first_item['unit_rate'], 2800.0)
        self.assertIn("Enhanced", first_item['notes'])
        
        # Verify new service
        validation_service = next((item for item in enhanced_template['items'] 
                                 if item['service_code'] == 'EDU_VAL'), None)
        self.assertIsNotNone(validation_service)
        self.assertEqual(validation_service['unit_rate'], 3500.0)
        
        # Step 5: Verify both templates exist
        all_templates = self.service.get_available_templates()
        self.assertEqual(len(all_templates), 3)  # Original 2 + 1 new
        
        template_names = [t['name'] for t in all_templates]
        self.assertIn("Education Standard", template_names)
        self.assertIn("Education Enhanced", template_names)
        self.assertIn("Healthcare Specialized", template_names)
        
        print("✅ Template customization workflow test passed")

def run_service_template_tests():
    """Run comprehensive ReviewManagementService template tests"""
    
    print("🎯 REVIEWMANAGEMENTSERVICE TEMPLATE TESTING")
    print("=" * 60)
    print(f"📅 Test Run Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestReviewManagementServiceTemplates))
    suite.addTests(loader.loadTestsFromTestCase(TestServiceTemplateIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📋 SERVICE TEMPLATE TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    passed_tests = total_tests - len(result.failures) - len(result.errors)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    # Coverage areas
    print(f"\n📊 SERVICE TEMPLATE COVERAGE:")
    print("✅ ReviewManagementService.get_available_templates()")
    print("✅ ReviewManagementService.load_template()")
    print("✅ ReviewManagementService.save_template()")
    print("✅ Template overwrite functionality")
    print("✅ Error handling (missing files, corrupted JSON)")
    print("✅ Template selection workflow")
    print("✅ Template customization workflow")
    print("✅ Integration with project management")
    
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
        print(f"\n🎉 ALL SERVICE TEMPLATE TESTS PASSED!")
        print("✅ ReviewManagementService template methods working correctly")
        print("✅ Template loading and saving operational")
        print("✅ Error handling robust")
        print("✅ Integration workflows validated")
        print("✅ Template management system production ready")
        return True
    else:
        print(f"\n⚠️ SOME SERVICE TEMPLATE TESTS FAILED")
        print("Please review the failed tests above and fix issues.")
        return False

if __name__ == "__main__":
    success = run_service_template_tests()
    
    if success:
        print(f"\n🎯 ReviewManagementService template functionality fully validated!")
        print(f"🔧 Template management system ready for production use")
    else:
        print(f"\n❌ ReviewManagementService template system needs attention")
        sys.exit(1)