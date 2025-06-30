import os
import json
import datetime
from typing import Any, Iterable, Dict

# Known prefix names that may appear at the start of export JSON files
# before the actual project name and timestamp. These prefixes can contain
# underscores, so they need to be matched as complete tokens.
KNOWN_PREFIXES = {
    "families",
    "family_sizes",
    "file_sizes",
    "views",
    "levels",
    "rooms",
    "rooms_levels",
    "warnings",
    "worksets",
    "lines",
    "grids",
    "project_base_point",
    "survey_point",
    "title_blocks_summary",
}


def _find_nested_values(obj: Any, keys: Iterable[str]) -> Dict[str, Any]:
    """Recursively search ``obj`` for ``keys`` and return first occurrences."""
    found = {}

    def _search(item: Any):
        if isinstance(item, dict):
            for k, v in item.items():
                if k in keys and k not in found:
                    found[k] = v
                if isinstance(v, (dict, list)):
                    _search(v)
        elif isinstance(item, list):
            for sub in item:
                _search(sub)

    _search(obj)
    return found

def _ensure_processed_dir(export_dir: str) -> str:
    """Ensure the processed directory exists and return its path."""
    processed_dir = os.path.join(export_dir, "processed")
    os.makedirs(processed_dir, exist_ok=True)
    return processed_dir

def extract_project_and_timestamp(filename: str):
    """Return project name and timestamp extracted from ``filename``.

    Filenames generally follow the pattern
    ``<prefix>_<project>_<YYYYMMDD>_<HHMMSS>.json`` where the prefix can itself
    contain underscores (e.g. ``file_sizes``).  The project name may also contain
    underscores.  This helper strips any known prefix tokens and returns the
    project name along with the date/time portion.  If the filename does not
    include at least two numeric timestamp tokens the function returns
    ``(None, None)``.
    """

    name = os.path.splitext(filename)[0]
    parts = name.split("_")
    if len(parts) < 4:
        return None, None

    date_token, time_token = parts[-2], parts[-1]
    if not (date_token.isdigit() and time_token.isdigit()):
        return None, None
    timestamp = f"{date_token}_{time_token}"

    base_parts = parts[:-2]
    # Remove known prefix tokens from the start if they match
    removed = False
    for pref in sorted(KNOWN_PREFIXES, key=lambda p: -len(p.split("_"))):
        tokens = pref.split("_")
        if base_parts[: len(tokens)] == tokens:
            base_parts = base_parts[len(tokens) :]
            removed = True
            break
    if not removed and base_parts:
        base_parts = base_parts[1:]

    if not base_parts:
        return None, None

    project = "_".join(base_parts)
    return project, timestamp

def load_json(file_path: str):
    with open(file_path, "r") as f:
        return json.load(f)

def find_latest_files_by_project(export_dir: str):
    grouped = {}
    for file in os.listdir(export_dir):
        if not file.endswith(".json"):
            continue
        if "combined" in file.lower():
            continue

        project, timestamp = extract_project_and_timestamp(file)
        if not project or not timestamp:
            continue
        key = (project, timestamp)
        grouped.setdefault(key, []).append(file)
    return grouped

def combine_files(export_dir: str, processed_dir: str, project: str, timestamp: str, file_list):
    """Combine individual export files for a single project/timestamp into one JSON object."""
    data = {}
    search_keys = {"strRvtUserName", "strSysName"}

    for file in file_list:
        file_path = os.path.join(export_dir, file)
        json_data = load_json(file_path)

        # Extract strRvtUserName and strSysName if found
        nested = _find_nested_values(json_data, search_keys)
        for k in search_keys:
            if k in nested and k not in data:
                data[k] = nested[k]

        # Handle dict-type files with expected keys
        if isinstance(json_data, dict) and "data_type" in json_data and "data" in json_data:
            dtype = json_data["data_type"]
            content = json_data["data"]

            # Map data_type to json* keys
            type_map = {
                "metadata": None,  # Already handled separately
                "views": "jsonViews",
                "levels": "jsonLevels",
                "rooms": "jsonRooms",
                "rooms_levels": "jsonRooms",
                "schedules": "jsonSchedules",
                "title_blocks_summary": "jsonTitleBlocksSummary",
                "design_options": "jsonDesignOptions",
                "worksets": "jsonWorksets",
                "grids": "jsonGrids",
                "warnings": "jsonWarnings",
                "lines": "jsonLines",
                "project_base_point": "jsonProjectBasePoint",
                "survey_point": "jsonSurveyPoint",
                "family_sizes": "jsonFamilySizes",
                "placed_families": "jsonFamilies",
                "file_sizes": "jsonFileSizes",
            }

            json_key = type_map.get(dtype)
            if json_key:
                data[json_key] = json.dumps(content)

            # Also pull user/system info from metadata file
            if dtype == "metadata":
                nested = _find_nested_values(content, search_keys)
                for k in search_keys:
                    if k in nested and k not in data:
                        data[k] = nested[k]
                # Set default file name and export timestamp
                for field in ["strRvtFileName", "nExportedOn"]:
                    if field in content and field not in data:
                        data[field] = content[field]


        # Handle flat lists like placed families, file sizes, etc.
        elif isinstance(json_data, list) and json_data:
            sample = json_data[0]
            if isinstance(sample, dict):
                if "FamilyName" in sample and "TypeName" in sample:
                    data["jsonFamilies"] = json.dumps(json_data)
                elif "FamilyName" in sample and "SizeMB" in sample:
                    data["jsonFamilySizes"] = json.dumps(json_data)
                elif "FileName" in sample and "SizeMB" in sample:
                    data["jsonFileSizes"] = json.dumps(json_data)
                elif "TitleBlockName" in sample:
                    data["jsonTitleBlocksPlaced"] = json.dumps(json_data)


    # Add required fallback/default values
    data.setdefault("strRvtFileName", project)
    data.setdefault("nExportedOn", int(datetime.datetime.utcnow().timestamp()))
    if "strRvtUserName" not in data:
        print("⚠️ strRvtUserName not found. Using default 'Unknown'.")
        data["strRvtUserName"] = "Unknown"
    if "strSysName" not in data:
        print("⚠️ strSysName not found. Using default 'Unknown'.")
        data["strSysName"] = "Unknown"

    combined_filename = f"combined_{project}_{timestamp}.json"
    combined_path = os.path.join(export_dir, combined_filename)

    with open(combined_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Combined export created: {combined_filename}")

    # Move source files to processed folder
    for file in file_list:
        src = os.path.join(export_dir, file)
        dst = os.path.join(processed_dir, file)
        try:
            os.rename(src, dst)
            print(f"📁 Moved {file} to processed folder.")
        except FileExistsError:
            print(f"⚠️ Skipping move of {file} — already exists in processed.")


def combine_exports_to_single_file(export_dir: str) -> str:
        """Combine all relevant export files into one unified JSON per project name."""
        processed_dir = _ensure_processed_dir(export_dir)
        project_files = {}

        # Group files by base project name (ignore timestamp)
        for file in os.listdir(export_dir):
            if not file.endswith(".json") or "combined" in file.lower():
                continue
            project, _ = extract_project_and_timestamp(file)
            if not project:
                continue
            project_files.setdefault(project, []).append(file)

        for project, file_list in project_files.items():
            output_path = os.path.join(export_dir, f"{project}_combined.json")
            combine_files_into_single(output_path, export_dir, processed_dir, file_list)

        return export_dir

def combine_files_into_single(output_path, export_dir, processed_dir, file_list):
        data = {}
        search_keys = {"strRvtUserName", "strSysName"}

        for file in file_list:
            file_path = os.path.join(export_dir, file)
            json_data = load_json(file_path)

            # Handle metadata
            if isinstance(json_data, dict) and json_data.get("data_type") == "metadata":
                content = json_data["data"]
                for key in ["strRvtFileName", "nExportedOn"]:
                    if key in content:
                        data[key] = content[key]
                for k in search_keys:
                    if k in content:
                        data[k] = content[k]

            # Handle other data types
            elif isinstance(json_data, dict) and "data_type" in json_data:
                dtype = json_data["data_type"]
                content = json_data["data"]
                key_map = {
                    "views": "jsonViews",
                    "levels": "jsonLevels",
                    "rooms": "jsonRooms",
                    "rooms_levels": "jsonRooms",
                    "placed_families": "jsonFamilies",
                    "file_sizes": "jsonFileSizes"
                }
                out_key = key_map.get(dtype)
                if out_key:
                    data[out_key] = json.dumps(content)

            # Handle legacy flat JSON lists (like old-style placed families or file sizes)
            elif isinstance(json_data, list):
                if "FamilyName" in json_data[0]:
                    if "SizeMB" in json_data[0]:
                        data["jsonFamilySizes"] = json.dumps(json_data)
                    else:
                        data["jsonFamilies"] = json.dumps(json_data)
                elif "FileName" in json_data[0] and "SizeMB" in json_data[0]:
                    data["jsonFileSizes"] = json.dumps(json_data)

            # Fallbacks
            data.setdefault("strRvtUserName", "Unknown")
            data.setdefault("strSysName", "Unknown")
            data.setdefault("nExportedOn", int(datetime.datetime.utcnow().timestamp()))

        # Write final combined file
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Combined project export created: {os.path.basename(output_path)}")

        # Move input files to processed
        for file in file_list:
            src = os.path.join(export_dir, file)
            dst = os.path.join(processed_dir, file)
            try:
                os.rename(src, dst)
                print(f"📁 Moved {file} to processed folder.")
            except FileExistsError:
                print(f"⚠️ Skipping move of {file} — already exists in processed.")

def main():
    export_dir = os.getcwd()
    combine_exports_to_single_file(export_dir)


if __name__ == "__main__":
    main()
