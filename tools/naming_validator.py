import json
import re
from database import update_file_validation_status



def validate_files(project_id, file_list, schema_path, project_name):
    with open(schema_path) as f:
        config = json.load(f)

    if isinstance(config, list):
        schema = next((s for s in config if s["project_name"].lower() == project_name.lower()), None)
    else:
        schema = config

    if not schema:
        raise ValueError(f"No schema for project '{project_name}'")

    delimiter = schema.get("delimiter", "-")
    fields = schema.get("fields", [])
    compiled_regex = re.compile(schema.get("regex_pattern", ".*"), re.IGNORECASE)

    results = []

    for file in file_list:
        if not isinstance(file, str):
            results.append((str(file), "Invalid filename format"))
            continue

        parts = file.split(delimiter)
        reason = None
        failed_field = None
        failed_value = None

        for field in fields:
            pos = field["position"]
            if pos >= len(parts):
                reason = f"Missing field at position {pos}: {field['name']}"
                failed_field = field['name']
                break

            value = parts[pos]
            # Case-insensitive checks
            if "allowed_values" in field:
                allowed = field["allowed_values"]
                if field.get("case_sensitive", False):
                    if value not in allowed:
                        reason = f"{field['name']} '{value}' not allowed (case-sensitive)"
                        failed_field = field['name']
                        failed_value = value
                        break
                else:
                    allowed_lower = [v.lower() for v in allowed]
                    if value.lower() not in allowed_lower:
                        reason = f"{field['name']} '{value}' not allowed"
                        failed_field = field['name']
                        failed_value = value
                        break

            if "regex" in field:
                if not re.fullmatch(field["regex"], value, re.IGNORECASE):
                    reason = f"{field['name']} '{value}' does not match pattern {field['regex']}"
                    failed_field = field['name']
                    failed_value = value
                    break

        if not reason and not compiled_regex.fullmatch(file):
            reason = f"Filename does not match required pattern {compiled_regex.pattern}"

        if reason:
            update_file_validation_status(
                file_name=file,
                status="Invalid",
                reason=reason,
                regex_used=compiled_regex.pattern,
                failed_field=failed_field,
                failed_value=failed_value,
                failed_reason=reason
            )
            results.append((file, reason))
        else:
            update_file_validation_status(
                file_name=file,
                status="Valid",
                reason="",
                regex_used=compiled_regex.pattern,
                failed_field=None,
                failed_value=None,
                failed_reason=None
            )

    return results
