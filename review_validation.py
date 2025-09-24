"""
Review Management Validation Module

Comprehensive validation for templates, services, and review cycles
"""

import re
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, InvalidOperation


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"{field}: {message}")


class ReviewValidationService:
    """Comprehensive validation service for review management"""

    def __init__(self):
        # Define validation rules
        self.template_rules = {
            'name': {'required': True, 'max_length': 200, 'pattern': r'^[a-zA-Z0-9\s\-\(\)\.\–]+$'},
            'sector': {'required': True, 'max_length': 100, 'allowed_values': ['Education', 'Data Centre', 'Healthcare', 'Commercial', 'Residential', 'Infrastructure', 'Other']},
            'items': {'required': True, 'min_items': 1}
        }

        self.service_rules = {
            'service_code': {'required': True, 'max_length': 20, 'pattern': r'^[A-Z0-9_]+$'},
            'service_name': {'required': True, 'max_length': 200},
            'phase': {'required': True, 'max_length': 200},
            'unit_type': {'required': True, 'allowed_values': ['lump_sum', 'review', 'audit', 'hourly']},
            'unit_qty': {'required': True, 'min_value': 0, 'max_value': 1000},  # Changed from default_units
            'unit_rate': {'min_value': 0, 'max_value': 100000},
            'lump_sum_fee': {'min_value': 0, 'max_value': 10000000},
            'bill_rule': {'required': True, 'allowed_values': ['on_setup', 'per_unit_complete', 'on_completion', 'monthly', 'quarterly', 'on_report_issue']},  # Added on_report_issue
            'agreed_fee': {'min_value': 0, 'max_value': 10000000}
        }

        self.review_rules = {
            'planned_date': {'required': True},
            'due_date': {'required': False},
            'disciplines': {'max_length': 200},
            'deliverables': {'max_length': 200},
            'status': {'required': True, 'allowed_values': ['planned', 'in_progress', 'completed', 'report_issued', 'closed', 'cancelled']},
            'weight_factor': {'min_value': 0.1, 'max_value': 5.0},
            'evidence_links': {'max_length': 2000}
        }

    def validate_template(self, template: Dict) -> List[ValidationError]:
        """Validate a service template"""
        errors = []

        # Validate basic template fields
        for field, rules in self.template_rules.items():
            try:
                self._validate_field(field, template.get(field), rules)
            except ValidationError as e:
                errors.append(e)

        # Validate template items
        if 'items' in template:
            for i, item in enumerate(template['items']):
                item_errors = self.validate_template_item(item)
                for error in item_errors:
                    error.field = f"items[{i}].{error.field}"
                    errors.append(error)

        return errors

    def validate_template_item(self, item: Dict) -> List[ValidationError]:
        """Validate a single template item"""
        errors = []

        for field, rules in self.service_rules.items():
            try:
                self._validate_field(field, item.get(field), rules)
            except ValidationError as e:
                errors.append(e)

        # Additional cross-field validation
        unit_type = item.get('unit_type')
        if unit_type == 'lump_sum':
            if not item.get('lump_sum_fee'):
                errors.append(ValidationError('lump_sum_fee', 'Required for lump_sum services'))
        elif unit_type in ['review', 'audit', 'hourly']:
            if not item.get('unit_rate'):
                errors.append(ValidationError('unit_rate', 'Required for unit-based services'))

        return errors

    def validate_service_data(self, service_data: Dict) -> List[ValidationError]:
        """Validate service data before creation/update"""
        errors = []

        for field, rules in self.service_rules.items():
            try:
                self._validate_field(field, service_data.get(field), rules)
            except ValidationError as e:
                errors.append(e)

        # Business logic validation
        unit_type = service_data.get('unit_type')
        unit_qty = service_data.get('unit_qty', 0)  # Changed from default_units to unit_qty
        unit_rate = service_data.get('unit_rate', 0)
        lump_sum = service_data.get('lump_sum_fee', 0)

        # Calculate and validate agreed fee
        if unit_type == 'lump_sum':
            if lump_sum <= 0:
                errors.append(ValidationError('lump_sum_fee', 'Must be greater than 0 for lump_sum services'))
            agreed_fee = lump_sum
        else:
            if unit_rate <= 0:
                errors.append(ValidationError('unit_rate', 'Must be greater than 0 for unit-based services'))
            if unit_qty <= 0:
                errors.append(ValidationError('unit_qty', 'Must be greater than 0 for unit-based services'))
            agreed_fee = unit_qty * unit_rate

        if agreed_fee > 10000000:  # 10M limit
            errors.append(ValidationError('agreed_fee', 'Total agreed fee cannot exceed $10,000,000'))

        return errors

    def validate_review_cycle(self, review_data: Dict) -> List[ValidationError]:
        """Validate review cycle data"""
        errors = []

        for field, rules in self.review_rules.items():
            try:
                self._validate_field(field, review_data.get(field), rules)
            except ValidationError as e:
                errors.append(e)

        # Date validation
        planned_date = review_data.get('planned_date')
        due_date = review_data.get('due_date')

        if planned_date and due_date:
            if isinstance(planned_date, str):
                planned_date = datetime.strptime(planned_date, '%Y-%m-%d').date()
            if isinstance(due_date, str):
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()

            if due_date < planned_date:
                errors.append(ValidationError('due_date', 'Due date cannot be before planned date'))

        # Status transition validation
        current_status = review_data.get('current_status')
        new_status = review_data.get('status')

        if current_status and new_status:
            if not self._is_valid_status_transition(current_status, new_status):
                errors.append(ValidationError('status', f'Invalid transition from {current_status} to {new_status}'))

        return errors

    def validate_project_services(self, project_id: int, services: List[Dict]) -> List[ValidationError]:
        """Validate all services for a project"""
        errors = []

        # Check for duplicate service codes
        service_codes = {}
        for i, service in enumerate(services):
            code = service.get('service_code', '').upper()
            if code in service_codes:
                errors.append(ValidationError(f'services[{i}].service_code',
                    f'Duplicate service code: {code} (also used in service {service_codes[code]})'))
            else:
                service_codes[code] = i

        # Validate each service
        for i, service in enumerate(services):
            service_errors = self.validate_service_data(service)
            for error in service_errors:
                error.field = f'services[{i}].{error.field}'
                errors.append(error)

        # Business rule: At least one review service per project
        review_services = [s for s in services if s.get('unit_type') == 'review']
        if not review_services:
            errors.append(ValidationError('services', 'Project must have at least one review-type service'))

        return errors

    def validate_billing_claim(self, claim_data: Dict) -> List[ValidationError]:
        """Validate billing claim data"""
        errors = []

        # Required fields
        required_fields = ['project_id', 'period_start', 'period_end']
        for field in required_fields:
            if not claim_data.get(field):
                errors.append(ValidationError(field, 'Required field'))

        # Date validation
        start_date = claim_data.get('period_start')
        end_date = claim_data.get('period_end')

        if start_date and end_date:
            if end_date <= start_date:
                errors.append(ValidationError('period_end', 'End date must be after start date'))

        # PO reference format (if provided)
        po_ref = claim_data.get('po_ref', '')
        if po_ref and not re.match(r'^[A-Z0-9\-]+$', po_ref.upper()):
            errors.append(ValidationError('po_ref', 'PO reference must contain only letters, numbers, and hyphens'))

        return errors

    def _validate_field(self, field_name: str, value: Any, rules: Dict) -> None:
        """Validate a single field against rules"""
        # Required check
        if rules.get('required', False) and (value is None or value == '' or value == []):
            raise ValidationError(field_name, 'Required field')

        # Skip further validation if value is None/empty and not required
        if value is None or value == '' or value == []:
            return

        # Type-specific validation
        if 'max_length' in rules and isinstance(value, str):
            if len(value) > rules['max_length']:
                raise ValidationError(field_name, f'Maximum length is {rules["max_length"]} characters')

        if 'min_length' in rules and isinstance(value, str):
            if len(value) < rules['min_length']:
                raise ValidationError(field_name, f'Minimum length is {rules["min_length"]} characters')

        if 'pattern' in rules and isinstance(value, str):
            if not re.match(rules['pattern'], value):
                raise ValidationError(field_name, f'Invalid format')

        if 'allowed_values' in rules:
            if value not in rules['allowed_values']:
                raise ValidationError(field_name, f'Must be one of: {", ".join(rules["allowed_values"])}')

        if 'min_value' in rules:
            try:
                num_value = float(value) if isinstance(value, str) else value
                if num_value < rules['min_value']:
                    raise ValidationError(field_name, f'Must be at least {rules["min_value"]}')
            except (ValueError, TypeError):
                raise ValidationError(field_name, 'Must be a valid number')

        if 'max_value' in rules:
            try:
                num_value = float(value) if isinstance(value, str) else value
                if num_value > rules['max_value']:
                    raise ValidationError(field_name, f'Must be at most {rules["max_value"]}')
            except (ValueError, TypeError):
                raise ValidationError(field_name, 'Must be a valid number')

        if 'min_items' in rules and isinstance(value, list):
            if len(value) < rules['min_items']:
                raise ValidationError(field_name, f'Must contain at least {rules["min_items"]} items')

    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """Validate status transition logic"""
        valid_transitions = {
            'planned': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled', 'planned'],
            'completed': ['report_issued', 'in_progress'],
            'report_issued': ['closed', 'completed'],
            'closed': ['report_issued'],
            'cancelled': ['planned', 'in_progress']
        }

        return new_status in valid_transitions.get(current_status, [])

    def sanitize_input(self, data: Dict) -> Dict:
        """Sanitize input data to prevent injection attacks"""
        sanitized = {}

        for key, value in data.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized[key] = re.sub(r'[<>]', '', value.strip())
            elif isinstance(value, (int, float, bool, type(None))):
                sanitized[key] = value
            elif isinstance(value, (date, datetime)):
                sanitized[key] = value
            elif isinstance(value, Decimal):
                sanitized[key] = float(value)
            else:
                # Convert other types to string for safety
                sanitized[key] = str(value) if value is not None else None

        return sanitized


# Global validation service instance
validation_service = ReviewValidationService()


def validate_template(template: Dict) -> List[ValidationError]:
    """Convenience function to validate a template"""
    return validation_service.validate_template(template)


def validate_service_data(service_data: Dict) -> List[ValidationError]:
    """Convenience function to validate service data"""
    return validation_service.validate_service_data(service_data)


def validate_review_cycle(review_data: Dict) -> List[ValidationError]:
    """Convenience function to validate review cycle data"""
    return validation_service.validate_review_cycle(review_data)


def validate_project_services(project_id: int, services: List[Dict]) -> List[ValidationError]:
    """Convenience function to validate project services"""
    return validation_service.validate_project_services(project_id, services)


def validate_billing_claim(claim_data: Dict) -> List[ValidationError]:
    """Convenience function to validate billing claim data"""
    return validation_service.validate_billing_claim(claim_data)


def sanitize_input(data: Dict) -> Dict:
    """Convenience function to sanitize input data"""
    return validation_service.sanitize_input(data)