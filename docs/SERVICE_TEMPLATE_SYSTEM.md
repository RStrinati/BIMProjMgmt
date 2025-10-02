# Service Template System - Documentation

## Overview

The BIM Project Management system includes a flexible service template system that allows users to create standardized service packages for different types of projects. This system enables quick setup of project services based on predefined templates.

## Template Structure

Service templates are stored in `/templates/service_templates.json` and follow this structure:

```json
{
  "templates": [
    {
      "name": "Template Name",
      "sector": "Project Sector",
      "notes": "Optional description",
      "items": [
        {
          "phase": "Project Phase",
          "service_code": "SERVICE_CODE",
          "service_name": "Human Readable Service Name",
          "unit_type": "lump_sum|review|audit|hourly",
          "default_units": 1,
          "unit_rate": 1000.00,
          "lump_sum_fee": 5000.00,
          "bill_rule": "billing_rule",
          "notes": "Optional service notes"
        }
      ]
    }
  ]
}
```

## Template Fields

### Template-Level Fields
- **name**: Unique template identifier (required)
- **sector**: Project sector/type (Education, Data Centre, Healthcare, Commercial, Residential, Infrastructure, Other)
- **notes**: Optional description of the template
- **items**: Array of service items (at least 1 required)

### Service Item Fields
- **phase**: Project phase or stage name (required)
- **service_code**: Unique service identifier (uppercase alphanumeric + underscore)
- **service_name**: Human-readable service name (required)
- **unit_type**: Type of service billing (required)
  - `lump_sum`: Fixed fee service
  - `review`: Review-based service (charged per review)
  - `audit`: Audit-based service (charged per audit)
  - `hourly`: Time-based service (charged hourly)
- **default_units**: Default quantity when applying template (required)
- **unit_rate**: Rate per unit for unit-based services (required for non-lump_sum)
- **lump_sum_fee**: Fixed fee for lump_sum services (required for lump_sum)
- **bill_rule**: Billing trigger rule (required)
  - `on_setup`: Bill when service is set up
  - `per_unit_complete`: Bill as each unit is completed
  - `on_completion`: Bill when all units are complete
  - `monthly`: Bill monthly
  - `quarterly`: Bill quarterly
  - `on_report_issue`: Bill when report is issued
- **notes**: Optional service-specific notes

## Template Validation

Templates undergo validation to ensure data integrity:

### Template Validation Rules
- Name must be unique and contain only alphanumeric characters, spaces, hyphens, parentheses, periods, en-dashes, and ampersands
- Sector must be one of the allowed values
- Must contain at least one service item

### Service Item Validation Rules
- Service code must be uppercase alphanumeric with underscores
- Service name and phase are required
- Unit type must be valid
- default_units must be between 0 and 1000
- For lump_sum services: lump_sum_fee is required
- For unit-based services: unit_rate is required
- Bill rule must be valid

## Using Templates in the UI

### Loading Templates
1. Navigate to **Review Management** tab
2. Go to **Service Setup** sub-tab
3. Select a project from the dropdown
4. Choose a template from the **Available Templates** dropdown
5. Click **Load Template** to preview template details

### Applying Templates
1. After selecting a template, click **Apply to Project**
2. Confirm the action in the dialog
3. The system will create project services based on template items
4. Services will be visible in the **Current Project Services** tree

### Template Application Process
When applying a template:
1. Template items are loaded and validated
2. Each template item is converted to a project service:
   - `default_units` becomes `unit_qty`
   - Agreed fee is calculated based on unit type
   - Service is created in the database
3. Review cycles can be auto-generated from services
4. Stages can be populated from service phases

## Database Schema

Templates are stored in two ways:
1. **File-based**: Primary templates in `templates/service_templates.json`
2. **Database-based**: Custom templates in `ServiceTemplates` table (optional)

When applied, templates create records in:
- `ProjectServices` table: Core service definitions
- `ServiceReviews` table: Generated review cycles
- `ServiceScheduleSettings` table: Scheduling configuration

## API Endpoints

### GET /api/service_templates
Returns all available service templates

### POST /api/service_templates
Creates a new custom template

### PATCH /api/service_templates/{id}
Updates an existing template

### DELETE /api/service_templates/{id}
Soft deletes a template

## Troubleshooting

### Template Won't Load
1. Check template file exists in `/templates/service_templates.json`
2. Validate JSON syntax
3. Check validation errors in console/logs
4. Ensure all required fields are present

### Template Won't Apply
1. Verify project is selected
2. Check database connection
3. Review validation errors
4. Ensure service codes are unique within project

### Validation Errors
Common validation issues:
- Missing required fields (`service_code`, `service_name`, `phase`, `unit_type`, `default_units`)
- Invalid characters in service codes (must be uppercase alphanumeric + underscore)
- Invalid unit types or bill rules
- Missing billing amounts (lump_sum_fee for lump_sum services, unit_rate for others)

## Development Notes

### Schema Differences
- Templates use `default_units` field
- Services use `unit_qty` field
- Validation handles this mapping automatically

### Adding New Templates
1. Edit `/templates/service_templates.json`
2. Follow the schema structure
3. Validate using the test scripts in `/tools/`
4. Restart the application to reload templates

### Testing Templates
Use these tools for testing:
- `/tools/test_template_loading.py`: Tests template loading and validation
- `/tools/test_ui_templates.py`: Tests UI integration

## Future Enhancements

Potential improvements:
- Template versioning
- Template categories/tags
- Template import/export
- Custom template builder UI
- Template preview with cost calculations