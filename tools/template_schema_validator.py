"""
Template Schema Validation

JSON Schema validation for service templates to ensure data integrity
"""

import json
import os
from typing import Dict, List, Optional, Any

# Define the JSON schema for service templates
TEMPLATE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "templates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 200,
                        "pattern": "^[a-zA-Z0-9\\s\\-\\(\\)\\.–&]+$"
                    },
                    "sector": {
                        "type": "string",
                        "enum": ["Education", "Data Centre", "Healthcare", "Commercial", "Residential", "Infrastructure", "Other"]
                    },
                    "notes": {
                        "type": "string",
                        "maxLength": 500
                    },
                    "items": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "properties": {
                                "phase": {
                                    "type": "string",
                                    "minLength": 1,
                                    "maxLength": 200
                                },
                                "service_code": {
                                    "type": "string",
                                    "pattern": "^[A-Z0-9_]+$",
                                    "maxLength": 20
                                },
                                "service_name": {
                                    "type": "string",
                                    "minLength": 1,
                                    "maxLength": 200
                                },
                                "unit_type": {
                                    "type": "string",
                                    "enum": ["lump_sum", "review", "audit", "hourly"]
                                },
                                "default_units": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 1000
                                },
                                "unit_rate": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100000
                                },
                                "lump_sum_fee": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 10000000
                                },
                                "bill_rule": {
                                    "type": "string",
                                    "enum": ["on_setup", "per_unit_complete", "on_completion", "monthly", "quarterly", "on_report_issue"]
                                },
                                "notes": {
                                    "type": "string",
                                    "maxLength": 500
                                }
                            },
                            "required": ["phase", "service_code", "service_name", "unit_type", "default_units", "bill_rule"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["name", "sector", "items"],
                "additionalProperties": False
            }
        }
    },
    "required": ["templates"],
    "additionalProperties": False
}

def validate_template_schema(template_data: Dict) -> List[str]:
    """
    Validate template data against JSON schema
    Returns list of validation errors, empty if valid
    """
    try:
        # Try to import jsonschema for proper validation
        try:
            import jsonschema
            JSONSCHEMA_AVAILABLE = True
        except ImportError:
            JSONSCHEMA_AVAILABLE = False
            
        if not JSONSCHEMA_AVAILABLE:
            # Fallback to basic validation if jsonschema not available
            return validate_template_basic(template_data)
            
        # Use jsonschema for comprehensive validation
        try:
            jsonschema.validate(template_data, TEMPLATE_SCHEMA)
            return []  # No errors
        except jsonschema.ValidationError as e:
            return [f"Schema validation error: {e.message} at path: {' -> '.join(str(p) for p in e.absolute_path)}"]
        except jsonschema.SchemaError as e:
            return [f"Schema definition error: {e.message}"]
            
    except Exception as e:
        return [f"Unexpected validation error: {e}"]

def validate_template_basic(template_data: Dict) -> List[str]:
    """
    Basic validation without jsonschema dependency
    """
    errors = []
    
    try:
        # Check top-level structure
        if not isinstance(template_data, dict):
            errors.append("Template data must be a dictionary")
            return errors
            
        if 'templates' not in template_data:
            errors.append("Missing 'templates' key in template data")
            return errors
            
        templates = template_data['templates']
        if not isinstance(templates, list):
            errors.append("'templates' must be a list")
            return errors
            
        if len(templates) == 0:
            errors.append("Templates list cannot be empty")
            
        # Validate each template
        for i, template in enumerate(templates):
            template_errors = validate_single_template_basic(template, f"templates[{i}]")
            errors.extend(template_errors)
            
    except Exception as e:
        errors.append(f"Basic validation error: {e}")
        
    return errors

def validate_single_template_basic(template: Dict, path: str) -> List[str]:
    """
    Validate a single template without jsonschema
    """
    errors = []
    
    # Required fields
    required_fields = ['name', 'sector', 'items']
    for field in required_fields:
        if field not in template:
            errors.append(f"{path}.{field} is required")
            
    # Validate name
    if 'name' in template:
        name = template['name']
        if not isinstance(name, str) or len(name.strip()) == 0:
            errors.append(f"{path}.name must be a non-empty string")
        elif len(name) > 200:
            errors.append(f"{path}.name must be 200 characters or less")
            
    # Validate sector
    if 'sector' in template:
        sector = template['sector']
        valid_sectors = ["Education", "Data Centre", "Healthcare", "Commercial", "Residential", "Infrastructure", "Other"]
        if sector not in valid_sectors:
            errors.append(f"{path}.sector must be one of: {', '.join(valid_sectors)}")
            
    # Validate items
    if 'items' in template:
        items = template['items']
        if not isinstance(items, list):
            errors.append(f"{path}.items must be a list")
        elif len(items) == 0:
            errors.append(f"{path}.items cannot be empty")
        else:
            for j, item in enumerate(items):
                item_errors = validate_template_item_basic(item, f"{path}.items[{j}]")
                errors.extend(item_errors)
                
    return errors

def validate_template_item_basic(item: Dict, path: str) -> List[str]:
    """
    Validate a single template item without jsonschema
    """
    errors = []
    
    # Required fields
    required_fields = ['phase', 'service_code', 'service_name', 'unit_type', 'default_units', 'bill_rule']
    for field in required_fields:
        if field not in item:
            errors.append(f"{path}.{field} is required")
            
    # Validate service_code
    if 'service_code' in item:
        code = item['service_code']
        if not isinstance(code, str) or not code.replace('_', '').replace('-', '').isalnum():
            errors.append(f"{path}.service_code must contain only letters, numbers, and underscores")
        elif len(code) > 20:
            errors.append(f"{path}.service_code must be 20 characters or less")
            
    # Validate unit_type
    if 'unit_type' in item:
        unit_type = item['unit_type']
        valid_types = ["lump_sum", "review", "audit", "hourly"]
        if unit_type not in valid_types:
            errors.append(f"{path}.unit_type must be one of: {', '.join(valid_types)}")
            
    # Validate default_units
    if 'default_units' in item:
        units = item['default_units']
        if not isinstance(units, int) or units < 1 or units > 1000:
            errors.append(f"{path}.default_units must be an integer between 1 and 1000")
            
    # Validate bill_rule
    if 'bill_rule' in item:
        rule = item['bill_rule']
        valid_rules = ["on_setup", "per_unit_complete", "on_completion", "monthly", "quarterly", "on_report_issue"]
        if rule not in valid_rules:
            errors.append(f"{path}.bill_rule must be one of: {', '.join(valid_rules)}")
            
    # Validate numeric fields
    if 'unit_rate' in item:
        rate = item['unit_rate']
        if not isinstance(rate, (int, float)) or rate < 0 or rate > 100000:
            errors.append(f"{path}.unit_rate must be a number between 0 and 100000")
            
    if 'lump_sum_fee' in item:
        fee = item['lump_sum_fee']
        if not isinstance(fee, (int, float)) or fee < 0 or fee > 10000000:
            errors.append(f"{path}.lump_sum_fee must be a number between 0 and 10000000")
            
    return errors

def validate_template_file(file_path: str) -> List[str]:
    """
    Validate a template file
    """
    errors = []
    
    try:
        if not os.path.exists(file_path):
            return [f"Template file not found: {file_path}"]
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        schema_errors = validate_template_schema(data)
        errors.extend(schema_errors)
        
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
    except UnicodeDecodeError as e:
        errors.append(f"Encoding error: {e}")
    except Exception as e:
        errors.append(f"Validation error: {e}")
        
    return errors

if __name__ == "__main__":
    # Test the validation on the current template file
    template_file = os.path.join(os.path.dirname(__file__), '..', 'templates', 'service_templates.json')
    errors = validate_template_file(template_file)
    
    if errors:
        print("❌ Template validation failed:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Template validation passed!")