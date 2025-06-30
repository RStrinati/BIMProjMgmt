import os
import json
import datetime
from typing import Any, Dict

# Define known export prefixes
KNOWN_PREFIXES = {
    "families", "family_sizes", "file_sizes", "views", "levels", "rooms", "rooms_levels",
    "warnings", "worksets", "lines", "grids", "project_base_point", "survey_point",
    "title_blocks_summary", "metadata", "placed_families", "family_file_sizes", "views_rooms_levels"
}

def _ensure_processed_dir(export_dir: str) -> str:
    processed_dir = os.path.join(export_dir, "processed")
    os.makedirs(processed_dir, exist_ok=True)
    return processed_dir

def extract_project_and_timestamp(filename: str):
    name = os.path.splitext(filename)[0]
    parts = name.split("_")
    if len(parts) < 4:
        return None, None
    date_token, time_token = parts[-2], parts[-1]
    if not (date_token.isdigit() and time_token.isdigit()):
        return None, None
    timestamp = f"{date_token}_{time_token}"
    base_parts = parts[:-2]
    for pref in sorted(KNOWN_PREFIXES, key=lambda p: -len(p.split("_"))):
        pref_parts = pref.split("_")
        if base_parts[:len(pref_parts)] == pref_parts:
            base_parts = base_parts[len(pref_parts):]
            break
    if not base_parts:
        return None, None
    project = "_".join(base_parts)
    return project, timestamp

def load_json(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def combine_files_into_dict(export_dir, file_list) -> Dict[str, Any]:
    data = {}
    search_keys = {"strRvtUserName", "strSysName"}

    ordered_keys = [
        "nModelFileSizeMB",
        "jsonDesignOptions",
        "jsonFamily_sizes",  # keep this for now if you plan to extend DB later
        "jsonGrids",
        "jsonLevels",
        "jsonPhases",        # same here
        "jsonFamilies",
        "jsonProjectBasePoint",
        "jsonRooms",
        "jsonSchedules",     # not yet in DB, safe to include in JSON
        "jsonSurveyPoint",
        "jsonTitleBlocksSummary",
        "jsonViews",
        "jsonWorksets",
        "nCriticalWarningsCount",
        "nExportedOn",
        "nFamilyCount",
        "nGroupCount",
        "nRvtLinkCount",
        "nSheetsCount",
        "nTotalElementsCount",
        "nWarningsCount",
        "strClientName",
        "strProjectName",
        "strProjectNumber",
        "strRvtBuildVersion",
        "strRvtFileName",
        "strRvtUserName",  # will be replaced with ID during DB insertion
        "strRvtVersion",
        "strSysName"       # will be replaced with ID during DB insertion
    ]


    for file in file_list:
        file_path = os.path.join(export_dir, file)
        try:
            json_data = load_json(file_path)
        except Exception as e:
            print(f"[ERROR] Skipping {file}: {e}")
            continue

        if isinstance(json_data, dict) and json_data.get("data_type") == "metadata":
            content = json_data["data"]
            for key in content:
                data[key] = content[key]

            # Map old metadata key to the ordered key expected downstream
            if "ModelFileSizeMB" in content:
                data["nModelFileSizeMB"] = content["ModelFileSizeMB"]

            # ✅ Check and include base/survey point if available
            if "projectBasePoint" in content:
                data["jsonProjectBasePoint"] = json.dumps(content["projectBasePoint"])
            if "surveyPoint" in content:
                data["jsonSurveyPoint"] = json.dumps(content["surveyPoint"])

        elif isinstance(json_data, dict) and "data_type" in json_data:
            dtype = json_data["data_type"]
            content = json_data["data"]
            key_map = {
                "views": "jsonViews",
                "levels": "jsonLevels",
                "rooms": "jsonRooms",
                "rooms_levels": "jsonRooms",
                "views_rooms_levels": ["jsonViews", "jsonLevels", "jsonRooms", "jsonGrids", "jsonPhases"],
                "schedules": "jsonSchedules",
                "design_options": "jsonDesignOptions",
                "title_blocks_summary": "jsonTitleBlocksSummary",
                "worksets": "jsonWorksets",
                "grids": "jsonGrids",
                "phases": "jsonPhases",
                "warnings": "jsonWarnings",
                "lines": "jsonLines",
                "project_base_point": "jsonProjectBasePoint",
                "survey_point": "jsonSurveyPoint",
                "family_sizes": "jsonFamily_sizes",
                "placed_families": "jsonFamilies",  # renamed from jsonPlaced_families
                "file_sizes": "nModelFileSizeMB"    # renamed from ModelFileSizeMB
            }


            out_key = key_map.get(dtype)
            if isinstance(out_key, list):
                for key in out_key:
                    sub_key = key.replace("json", "").lower()
                    if sub_key in content:
                        data[key] = json.dumps(content[sub_key])
            elif out_key:
                data[out_key] = json.dumps(content)

        elif isinstance(json_data, list) and json_data:
            first = json_data[0]
            if isinstance(first, dict):
                if "FamilyName" in first and "TypeName" in first:
                    data["jsonPlaced_families"] = json.dumps(json_data)
                elif "FamilyName" in first and "SizeMB" in first:
                    data["jsonFamily_sizes"] = json.dumps(json_data)

    # Add missing keys as null for consistency
    for key in ordered_keys:
        data.setdefault(key, None)

    print(f"\n📦 Combined Data Summary for project:")
    for key in ordered_keys:
        status = "✅ Included" if data[key] is not None else "⚠️  Missing"
        print(f"   {status}: {key}")

    return {key: data[key] for key in ordered_keys}

def combine_exports_to_single_file(export_dir: str) -> str:
    processed_dir = _ensure_processed_dir(export_dir)
    project_name_map = {}

    for file in os.listdir(export_dir):
        if not file.endswith(".json"):
            continue
        if file.lower().startswith("combined_"):
            continue

        project, _ = extract_project_and_timestamp(file)
        if not project:
            continue
        project_name_map.setdefault(project, []).append(file)

    for project, file_list in project_name_map.items():
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(export_dir, f"combined_{project}_{timestamp}.json")

        data = combine_files_into_dict(export_dir, file_list)
        data.setdefault("strRvtUserName", "Unknown")
        data.setdefault("strSysName", "Unknown")
        data.setdefault("nExportedOn", int(datetime.datetime.utcnow().timestamp()))

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Combined project export created: {os.path.basename(output_path)}")

        for file in file_list:
            src = os.path.join(export_dir, file)
            dst = os.path.join(processed_dir, file)
            try:
                os.rename(src, dst)
                print(f"📁 Moved {file} to processed folder.")
            except FileExistsError:
                print(f"⚠️ Skipping move of {file} — already exists in processed.")

    return export_dir
