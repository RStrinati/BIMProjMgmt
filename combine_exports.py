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
    """Combine individual export files for a single project/timestamp."""
    data = {}

    search_keys = {"strRvtUserName", "strSysName"}

    for file in file_list:
        file_path = os.path.join(export_dir, file)
        json_data = load_json(file_path)

        nested = _find_nested_values(json_data, search_keys)
        for k in search_keys:
            if k in nested and k not in data:
                data[k] = nested[k]

        if isinstance(json_data, dict):
            # copy all top level keys by default
            for k, v in json_data.items():
                if k == "views":
                    data["jsonViews"] = json.dumps(v)
                elif k == "levels":
                    data["jsonLevels"] = json.dumps(v)
                elif k == "rooms":
                    data["jsonRooms"] = json.dumps(v)
                elif k == "title_blocks":
                    data["jsonTitleBlocksSummary"] = json.dumps(v)
                else:
                    data[k] = v
        elif isinstance(json_data, list) and json_data:
            # recognise exports that return a list
            sample = json_data[0]
            if isinstance(sample, dict) and "FamilyName" in sample:
                data["jsonFamilySizes"] = json.dumps(json_data)
            elif isinstance(sample, dict) and "TypeName" in sample:
                data["jsonFamilies"] = json.dumps(json_data)

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

    # Move source files
    for file in file_list:
        src = os.path.join(export_dir, file)
        dst = os.path.join(processed_dir, file)
        os.rename(src, dst)
        print(f"📁 Moved {file} to processed folder.")

def combine_exports(export_dir: str) -> str:
    """Combine related export files in ``export_dir``.

    The function searches for JSON exports sharing the same project name and
    timestamp, merges their contents, and writes a ``combined_<project>_<timestamp>.json``
    file. Source files are moved into a ``processed`` subfolder. The original
    ``export_dir`` path is returned so callers can continue processing within the
    same directory.
    """

    processed_dir = _ensure_processed_dir(export_dir)
    groups = find_latest_files_by_project(export_dir)

    for (project, timestamp), files in groups.items():
        combine_files(export_dir, processed_dir, project, timestamp, files)

    return export_dir


def main():
    export_dir = os.getcwd()
    combine_exports(export_dir)

if __name__ == "__main__":
    main()
