import argparse
import json
import os
import re
import sys

# Ensure project root is on the module search path when run as a script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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

        discipline = None
        discipline_full = None
        for field in fields:
            if field['name'].lower() == "discipline":
                pos = field["position"]
                if pos < len(parts):
                    discipline = parts[pos]
                    discipline_full = field.get("mapped_values", {}).get(discipline.upper(), discipline)
                break
            
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
                failed_reason=reason,
                discipline=discipline,
                discipline_full=discipline_full
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
                failed_reason=None,
                discipline=discipline,
                discipline_full=discipline_full
            )

    return results


def _load_files_from_folder(folder_path):
    files = []
    for entry in sorted(os.listdir(folder_path)):
        full_path = os.path.join(folder_path, entry)
        if os.path.isfile(full_path):
            files.append(entry)
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Validate file names against a naming convention schema."
    )
    parser.add_argument(
        "--project-id",
        type=int,
        default=0,
        help="Project identifier written to the database (optional)",
    )
    parser.add_argument(
        "--project-name",
        required=True,
        help="Project name used to pick the schema entry",
    )
    parser.add_argument(
        "--schema",
        required=True,
        help="Path to the naming convention JSON schema",
    )
    parser.add_argument(
        "--folder",
        help="Folder containing files to validate (only immediate files are read)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip database updates and only print results",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Individual file names to validate (in addition to --folder contents)",
    )

    args = parser.parse_args()

    file_list = []
    if args.folder:
        if not os.path.isdir(args.folder):
            parser.error(f"--folder path is not a directory: {args.folder}")
        file_list.extend(_load_files_from_folder(args.folder))

    file_list.extend(args.files)

    if not file_list:
        parser.error("No files supplied. Use --folder or pass file names as arguments.")

    if args.dry_run:
        # Replace DB update with no-op for this run
        globals()["update_file_validation_status"] = lambda **kwargs: None

    try:
        results = validate_files(
            project_id=args.project_id,
            file_list=file_list,
            schema_path=args.schema,
            project_name=args.project_name,
        )
    except Exception as exc:
        parser.exit(1, f"Validation failed: {exc}\n")

    total = len(file_list)
    invalid = len(results)

    print(f"Validated {total} file(s).")
    if invalid:
        print(f"{invalid} file(s) failed validation:")
        for file_name, reason in results:
            print(f" - {file_name}: {reason}")
    else:
        print("All files passed validation.")


if __name__ == "__main__":
    main()
