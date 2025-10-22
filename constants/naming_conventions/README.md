# Naming Conventions

This directory contains JSON schemas for file naming conventions used by different clients.

## Available Conventions

- **AWS.json** - Amazon Web Services naming convention (ISO 19650)
- **SINSW.json** - School Infrastructure NSW naming convention (ISO 19650-2 + SINSW National Annex 2021)

## Schema Structure

Each JSON file defines:
- `institution`: Client/organization name
- `standard`: The naming standard being followed
- `delimiter`: Character used to separate fields (typically "-")
- `regex_pattern`: Overall regex pattern for validation
- `fields`: Array of field definitions with:
  - `name`: Field name
  - `position`: Position in the delimited string
  - `allowed_values`: Valid values for this field
  - `mapped_values`: Human-readable descriptions (optional)
  - `case_sensitive`: Whether validation is case-sensitive
  - `regex`: Pattern for this specific field (optional)

## Usage

These schemas are automatically loaded by the naming validation service when validating project files based on the client's `naming_convention` property.

## Adding New Conventions

1. Create a new JSON file with the client code (e.g., `NEWCLIENT.json`)
2. Follow the schema structure shown in existing files
3. Update the database constraint in `sql/migrations/add_naming_convention_to_clients.sql` to include the new convention
4. Test thoroughly with sample files
