import json
import re
from database import update_file_validation_status


def validate_files_against_naming(project_id, json_file_path, file_list, project_name):
    """
    Validates a list of filenames against a project's regex pattern from a JSON file.
    Updates validation results in the database for each file.
    
    Args:
        project_id (int): ID of the project being validated.
        json_file_path (str): Path to the JSON file containing naming rules.
        file_list (list): List of file names to validate.
        project_name (str): Project name to find corresponding regex rule.
    
    Returns:
        list: Files that failed validation with reason.
    """
    # Load JSON rules
    with open(json_file_path, "r") as f:
        patterns = json.load(f)

    # Find the regex for the selected project
    matching = next((p for p in patterns if p["project_name"] == project_name), None)
    if not matching or "regex_pattern" not in matching:
        raise ValueError(f"No naming convention found for project '{project_name}'")

    regex = matching["regex_pattern"]
    compiled = re.compile(regex)

    results = []
    for file in file_list:
        if compiled.fullmatch(file):
            # File is valid
            update_file_validation_status(
                file_name=file,
                status="Valid",
                reason="",
                regex_used=regex
            )
        else:
            # File is invalid
            reason = f"Does not match regex: {regex}"
            results.append((file, reason))
            update_file_validation_status(
                file_name=file,
                status="Invalid",
                reason=reason,
                regex_used=regex
            )

    return results
