#!/usr/bin/env python3
"""Test script for validation functionality"""

from review_validation import (
    validate_template, validate_service_data, validate_review_cycle,
    validate_billing_claim, ValidationError
)
import json
import os

def test_template_validation():
    """Test template validation"""
    print("Testing template validation...")

    # Load a real template
    template_file = os.path.join(os.path.dirname(__file__), 'templates', 'service_templates.json')
    with open(template_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    template = data['templates'][0]  # Test first template

    errors = validate_template(template)
    if errors:
        print(f"❌ Template validation failed: {errors}")
        return False
    else:
        print("✅ Template validation passed")
        return True

def test_service_validation():
    """Test service data validation"""
    print("Testing service validation...")

    # Valid service data
    valid_service = {
        'service_code': 'TEST001',
        'service_name': 'Test Service',
        'phase': 'Test Phase',
        'unit_type': 'review',
        'default_units': 4,
        'unit_rate': 5000.0,
        'bill_rule': 'per_unit_complete',
        'agreed_fee': 20000.0
    }

    errors = validate_service_data(valid_service)
    if errors:
        print(f"❌ Valid service validation failed: {errors}")
        return False

    # Invalid service data
    invalid_service = {
        'service_code': '',  # Missing required field
        'service_name': 'A' * 300,  # Too long
        'unit_type': 'invalid_type',  # Invalid type
        'unit_qty': -1,  # Negative quantity
    }

    errors = validate_service_data(invalid_service)
    if not errors:
        print("❌ Invalid service should have failed validation")
        return False

    print(f"✅ Service validation correctly identified {len(errors)} errors")
    return True

def test_review_validation():
    """Test review cycle validation"""
    print("Testing review validation...")

    # Valid review data
    valid_review = {
        'planned_date': '2024-01-01',
        'due_date': '2024-01-15',
        'status': 'planned',
        'weight_factor': 1.0
    }

    errors = validate_review_cycle(valid_review)
    if errors:
        print(f"❌ Valid review validation failed: {errors}")
        return False

    # Invalid review data (due date before planned date)
    invalid_review = {
        'planned_date': '2024-01-15',
        'due_date': '2024-01-01',  # Before planned date
        'status': 'invalid_status'
    }

    errors = validate_review_cycle(invalid_review)
    if len(errors) < 2:  # Should have at least 2 errors
        print(f"❌ Invalid review should have failed validation, only got {len(errors)} errors")
        return False

    print(f"✅ Review validation correctly identified {len(errors)} errors")
    return True

def test_billing_validation():
    """Test billing claim validation"""
    print("Testing billing validation...")

    # Valid claim data
    valid_claim = {
        'project_id': 1,
        'period_start': '2024-01-01',
        'period_end': '2024-01-31',
        'po_ref': 'PO-2024-001'
    }

    errors = validate_billing_claim(valid_claim)
    if errors:
        print(f"❌ Valid claim validation failed: {errors}")
        return False

    # Invalid claim data
    invalid_claim = {
        'period_start': '2024-01-31',
        'period_end': '2024-01-01',  # End before start
        'po_ref': 'INVALID<>REF'  # Invalid characters
    }

    errors = validate_billing_claim(invalid_claim)
    if not errors:
        print("❌ Invalid claim should have failed validation")
        return False

    print(f"✅ Billing validation correctly identified {len(errors)} errors")
    return True

def main():
    """Run all validation tests"""
    print("Running validation tests...\n")

    tests = [
        test_template_validation,
        test_service_validation,
        test_review_validation,
        test_billing_validation
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}\n")

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All validation tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    main()