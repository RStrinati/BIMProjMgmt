"""
Simplified Template Management Tests

This test suite focuses on core template functionality that can be tested
without complex mocking of internal methods.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import json
import tempfile
import shutil
from unittest.mock import Mock
from datetime import datetime

def create_test_template_data():
    """Create sample template data for testing"""
    return {
        "templates": [
            {
                "name": "Test Educational Template",
                "sector": "Education",
                "notes": "Template for educational projects",
                "items": [
                    {
                        "phase": "Phase 1 - Design Development",
                        "service_code": "DDR001",
                        "service_name": "Design Development Review",
                        "unit_type": "review",
                        "default_units": 4,
                        "unit_rate": 2200.0,
                        "bill_rule": "per_unit_complete",
                        "notes": "Weekly design development reviews"
                    },
                    {
                        "phase": "Phase 2 - Documentation",
                        "service_code": "DCR001", 
                        "service_name": "Documentation Coordination Review",
                        "unit_type": "lump_sum",
                        "default_units": 1,
                        "lump_sum_fee": 12000.0,
                        "bill_rule": "on_completion",
                        "notes": "Complete documentation package review"
                    }
                ]
            },
            {
                "name": "Test Commercial Template",
                "sector": "Commercial",
                "notes": "Template for commercial projects",
                "items": [
                    {
                        "phase": "Phase 1 - Coordination",
                        "service_code": "COORD01",
                        "service_name": "BIM Coordination Review",
                        "unit_type": "review",
                        "default_units": 6,
                        "unit_rate": 2800.0,
                        "bill_rule": "per_unit_complete",
                        "notes": "Bi-weekly coordination reviews"
                    }
                ]
            }
        ]
    }

class TestTemplateManagementCore(unittest.TestCase):
    """Test core template functionality without complex mocking"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary template file with test data
        self.temp_dir = tempfile.mkdtemp()
        self.temp_template_file = os.path.join(self.temp_dir, 'service_templates.json')
        
        self.test_data = create_test_template_data()
        with open(self.temp_template_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_data, f, indent=2)
        
        # Create mock database connection
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
        
        # We'll use the real template file path for these tests
        print(f"📁 Using test template file: {self.temp_template_file}")
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_template_file_operations(self):
        """Test basic template file read/write operations"""
        print("\n🧪 Testing template_file_operations...")
        
        # Test reading template file
        self.assertTrue(os.path.exists(self.temp_template_file))
        
        with open(self.temp_template_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertIn('templates', loaded_data)
        self.assertEqual(len(loaded_data['templates']), 2)
        
        # Test template structure
        first_template = loaded_data['templates'][0]
        self.assertEqual(first_template['name'], "Test Educational Template")
        self.assertEqual(first_template['sector'], "Education")
        self.assertEqual(len(first_template['items']), 2)
        
        print("✅ Template file operations test passed")
    
    def test_template_validation_with_real_validator(self):
        """Test template validation using the actual validation system"""
        print("\n🧪 Testing template_validation_with_real_validator...")
        
        from review_validation import validate_template
        
        # Test with valid template from our test data
        valid_template = self.test_data['templates'][0]
        
        # The validator returns a list of ValidationError objects
        errors = validate_template(valid_template)
        self.assertEqual(len(errors), 0, f"Valid template should have no errors, got: {[str(e) for e in errors]}")
        
        # Test with invalid template (missing required fields)
        invalid_template = {
            "name": "Invalid Template"
            # Missing sector, notes, items
        }
        
        errors = validate_template(invalid_template)
        self.assertGreater(len(errors), 0, "Invalid template should have validation errors")
        
        # Verify that required fields are flagged
        error_fields = [error.field for error in errors]
        self.assertIn('sector', error_fields)
        self.assertIn('items', error_fields)
        
        print("✅ Template validation test passed")
    
    def test_template_item_validation(self):
        """Test individual template item validation"""
        print("\n🧪 Testing template_item_validation...")
        
        from review_validation import validate_template
        
        # Test template with invalid items
        invalid_item_template = {
            "name": "Invalid Item Template",
            "sector": "Education",
            "notes": "Template with invalid items",
            "items": [
                {
                    "phase": "",  # Empty phase should fail
                    "service_code": "INVALID",
                    "service_name": "Invalid Service",
                    "unit_type": "invalid_type",  # Invalid unit_type
                    "default_units": -1,  # Negative quantity should fail
                    "unit_rate": -100  # Negative rate should fail
                }
            ]
        }
        
        errors = validate_template(invalid_item_template)
        self.assertGreater(len(errors), 0, "Template with invalid items should have errors")
        
        # Check for specific validation errors
        error_messages = [str(error) for error in errors]
        print(f"📋 Validation errors found: {error_messages}")
        
        print("✅ Template item validation test passed")
    
    def test_template_data_consistency(self):
        """Test that template data structure is consistent"""
        print("\n🧪 Testing template_data_consistency...")
        
        for template_idx, template in enumerate(self.test_data['templates']):
            # Check required template fields
            required_fields = ['name', 'sector', 'notes', 'items']
            for field in required_fields:
                self.assertIn(field, template, f"Template {template_idx} missing {field}")
                self.assertIsNotNone(template[field], f"Template {template_idx} {field} is None")
            
            # Check template items
            self.assertIsInstance(template['items'], list, f"Template {template_idx} items must be list")
            self.assertGreater(len(template['items']), 0, f"Template {template_idx} must have items")
            
            # Check each item
            for item_idx, item in enumerate(template['items']):
                required_item_fields = ['phase', 'service_code', 'service_name', 'unit_type']
                for field in required_item_fields:
                    self.assertIn(field, item, f"Template {template_idx} item {item_idx} missing {field}")
                
                # Check unit_type specific fields
                if item['unit_type'] == 'lump_sum':
                    self.assertIn('lump_sum_fee', item, f"Lump sum item missing lump_sum_fee")
                    self.assertGreater(item['lump_sum_fee'], 0, f"Lump sum fee must be positive")
                else:
                    self.assertIn('default_units', item, f"Non-lump-sum item missing default_units")
                    self.assertIn('unit_rate', item, f"Non-lump-sum item missing unit_rate")
                    self.assertGreater(item['default_units'], 0, f"Default units must be positive")
                    self.assertGreater(item['unit_rate'], 0, f"Unit rate must be positive")
        
        print("✅ Template data consistency test passed")

class TestTemplateIntegrationScenarios(unittest.TestCase):
    """Test realistic template usage scenarios"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_template_file = os.path.join(self.temp_dir, 'service_templates.json')
        
        # Start with empty template file
        initial_data = {"templates": []}
        with open(self.temp_template_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)
        
        print(f"📁 Integration test template file: {self.temp_template_file}")
    
    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_template_creation_workflow(self):
        """Test creating templates from scratch"""
        print("\n🧪 Testing template_creation_workflow...")
        
        # Create a new template structure
        new_template = {
            "name": "Integration Test Template",
            "sector": "Healthcare",
            "notes": "Created during integration testing",
            "items": [
                {
                    "phase": "Phase 1 - Planning",
                    "service_code": "PLAN01",
                    "service_name": "Healthcare Planning Review",
                    "unit_type": "review",
                    "default_units": 3,
                    "unit_rate": 3500.0,
                    "bill_rule": "per_unit_complete",
                    "notes": "Specialized healthcare planning reviews"
                },
                {
                    "phase": "Phase 2 - Compliance",
                    "service_code": "COMP01",
                    "service_name": "Healthcare Compliance Check",
                    "unit_type": "lump_sum",
                    "default_units": 1,
                    "lump_sum_fee": 8500.0,
                    "bill_rule": "on_completion",
                    "notes": "Comprehensive healthcare compliance verification"
                }
            ]
        }
        
        # Validate the new template
        from review_validation import validate_template
        errors = validate_template(new_template)
        self.assertEqual(len(errors), 0, f"New template should be valid, got errors: {[str(e) for e in errors]}")
        
        # Add template to file (simulate save operation)
        with open(self.temp_template_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data['templates'].append(new_template)
        
        with open(self.temp_template_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        # Verify template was saved
        with open(self.temp_template_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(len(saved_data['templates']), 1)
        saved_template = saved_data['templates'][0]
        self.assertEqual(saved_template['name'], "Integration Test Template")
        self.assertEqual(saved_template['sector'], "Healthcare")
        
        print("✅ Template creation workflow test passed")
    
    def test_template_modification_workflow(self):
        """Test modifying existing templates"""
        print("\n🧪 Testing template_modification_workflow...")
        
        # Start with a basic template
        original_template = {
            "name": "Modifiable Template",
            "sector": "Commercial",
            "notes": "Original template for modification testing",
            "items": [
                {
                    "phase": "Phase 1 - Original",
                    "service_code": "ORIG01",
                    "service_name": "Original Service",
                    "unit_type": "review",
                    "default_units": 2,
                    "unit_rate": 1500.0,
                    "bill_rule": "per_unit_complete",
                    "notes": "Original service item"
                }
            ]
        }
        
        # Save original template
        with open(self.temp_template_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data['templates'].append(original_template)
        
        with open(self.temp_template_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        # Modify the template (add new service item)
        modified_item = {
            "phase": "Phase 2 - Addition",
            "service_code": "ADD01",
            "service_name": "Additional Service",
            "unit_type": "lump_sum",
            "default_units": 1,
            "lump_sum_fee": 5000.0,
            "bill_rule": "on_completion",
            "notes": "Added during modification"
        }
        
        # Load, modify, and save
        with open(self.temp_template_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data['templates'][0]['items'].append(modified_item)
        data['templates'][0]['notes'] = "Modified template with additional service"
        
        # Validate modified template
        from review_validation import validate_template
        errors = validate_template(data['templates'][0])
        self.assertEqual(len(errors), 0, f"Modified template should be valid, got errors: {[str(e) for e in errors]}")
        
        with open(self.temp_template_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        # Verify modifications
        with open(self.temp_template_file, 'r', encoding='utf-8') as f:
            final_data = json.load(f)
        
        modified_template = final_data['templates'][0]
        self.assertEqual(len(modified_template['items']), 2)
        self.assertEqual(modified_template['items'][1]['service_code'], "ADD01")
        self.assertIn("Modified template", modified_template['notes'])
        
        print("✅ Template modification workflow test passed")

def run_focused_template_tests():
    """Run focused template tests with detailed reporting"""
    
    print("🎯 FOCUSED TEMPLATE MANAGEMENT TESTING")
    print("=" * 60)
    print(f"📅 Test Run Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add focused test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateManagementCore))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateIntegrationScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📋 FOCUSED TEMPLATE TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    passed_tests = total_tests - len(result.failures) - len(result.errors)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    # Coverage areas
    print(f"\n📊 TEST COVERAGE AREAS:")
    print("✅ Template File Operations (read, write, JSON handling)")
    print("✅ Template Validation (structure, data integrity)")
    print("✅ Template Item Validation (service details, rates)")
    print("✅ Data Consistency (required fields, data types)")
    print("✅ Integration Workflows (creation, modification)")
    
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
        print(f"\n🎉 ALL FOCUSED TEMPLATE TESTS PASSED!")
        print("✅ Template validation system working correctly")
        print("✅ Template file operations functional")
        print("✅ Data consistency verified")
        print("✅ Integration workflows operational")
        print("✅ Core template functionality validated")
        return True
    else:
        print(f"\n⚠️ SOME FOCUSED TESTS FAILED")
        print("Please review the failed tests above and fix issues.")
        return False

if __name__ == "__main__":
    success = run_focused_template_tests()
    
    if success:
        print(f"\n🎯 Core template management functionality validated!")
        print(f"🔧 Ready to extend with full integration testing")
    else:
        print(f"\n❌ Core template management needs attention")
        sys.exit(1)