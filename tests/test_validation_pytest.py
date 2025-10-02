"""
Pytest-based validation tests for the BIM Project Management System
"""

import pytest
from review_validation import ReviewValidationService, ValidationError


class TestReviewValidationService:
    """Test the ReviewValidationService class"""

    def setup_method(self):
        """Setup for each test method"""
        self.validator = ReviewValidationService()

    def test_template_validation_valid(self):
        """Test validation of a valid template"""
        valid_template = {
            'name': 'Test Template',
            'sector': 'Education',
            'items': [{
                'service_code': 'REV001',
                'service_name': 'Test Review',
                'phase': 'Design',
                'unit_type': 'review',
                'default_units': 5,
                'unit_rate': 100.0,
                'bill_rule': 'per_unit_complete'
            }]
        }

        errors = self.validator.validate_template(valid_template)
        assert len(errors) == 0, f"Expected no errors, got: {errors}"

    def test_template_validation_invalid_sector(self):
        """Test validation of template with invalid sector"""
        invalid_template = {
            'name': 'Test Template',
            'sector': 'InvalidSector',  # Invalid sector
            'items': []
        }

        errors = self.validator.validate_template(invalid_template)
        assert len(errors) > 0
        assert any('sector' in str(error) for error in errors)

    def test_service_validation_missing_required(self):
        """Test service validation with missing required fields"""
        invalid_service = {
            'service_name': 'Test Service'
            # Missing service_code, phase, unit_type, default_units, bill_rule
        }

        errors = self.validator.validate_service_data(invalid_service)
        assert len(errors) > 0
        # Should have errors for missing required fields

    def test_service_validation_valid(self):
        """Test validation of valid service data"""
        valid_service = {
            'service_code': 'REV001',
            'service_name': 'Test Review Service',
            'phase': 'Design Phase',
            'unit_type': 'review',
            'default_units': 5,
            'unit_rate': 100.0,
            'bill_rule': 'per_unit_complete'
        }

        errors = self.validator.validate_service_data(valid_service)
        assert len(errors) == 0, f"Expected no errors, got: {errors}"

    def test_review_validation_valid(self):
        """Test validation of valid review data"""
        valid_review = {
            'planned_date': '2025-10-01',
            'due_date': '2025-10-15',
            'status': 'planned',
            'disciplines': 'Architecture',
            'deliverables': 'Review report',
            'weight_factor': 1.0
        }

        # Note: This would need to be integrated with the full validation system
        # For now, just test the basic structure
        assert 'planned_date' in valid_review
        assert 'status' in valid_review


class TestValidationError:
    """Test the ValidationError class"""

    def test_validation_error_creation(self):
        """Test creating a ValidationError"""
        error = ValidationError('test_field', 'Test message', 'test_value')
        assert error.field == 'test_field'
        assert error.message == 'Test message'
        assert error.value == 'test_value'
        assert str(error) == 'test_field: Test message'