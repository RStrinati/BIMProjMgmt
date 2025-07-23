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


ORDERED_KEYS = [
    # model metadata
    "nModelFileSizeMB",
    # family file-sizes
    "jsonFamily_sizes",
    "jsonFamilyFileSizesMetadata",
    "nFamilyFileSizesCount",
    # annotation & geometry dumps
    "jsonGrids",
    "jsonLevels",
    "jsonPhases",
    "jsonFamilies",
    # base points & rooms
    "jsonProjectBasePoint",
    "jsonRooms",
    "jsonSchedules",
    "jsonSurveyPoint",
    # view titles & worksets
    "jsonTitleBlocksSummary",
    "jsonViews",
    "jsonWorksets",
    # warnings
    "jsonWarnings",
    # warning counts
    "nCriticalWarningsCount",
    # export timestamp
    "nExportedOn",
    # project counts
    "nFamilyCount",
    "nGroupCount",
    "nRvtLinkCount",
    "nSheetsCount",
    "nTotalElementsCount",
    "nWarningsCount",
    # project identifiers
    "strClientName",
    "strProjectName",
    "strProjectNumber",
    "strRvtBuildVersion",
    "strRvtFileName",
    "strRvtUserName",
    "strRvtVersion",
    "strSysName",
]


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


def combine_files_into_dict(export_dir: str, file_list) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    for file in file_list:
        path = os.path.join(export_dir, file)
        try:
            blob = load_json(path)
        except Exception as e:
            print(f"[ERROR] Skipping {file}: {e}")
            continue

        dtype = blob.get("data_type")
        exported_on = blob.get("exported_on")
        # Record per-file export timestamps/types if needed
        if dtype and exported_on is not None:
            data[f"{dtype}_exported_on"] = exported_on
            data[f"{dtype}_data_type"] = dtype

        # 1) Metadata: top-level project info
        if dtype == "metadata":
            content = blob.get("data", {})
            # bring in all metadata fields
            for k, v in content.items():
                data[k] = v
            # rename ModelFileSizeMB to nModelFileSizeMB
            if "ModelFileSizeMB" in content:
                data["nModelFileSizeMB"] = content["ModelFileSizeMB"]
            # rename base/survey points
            if "projectBasePoint" in content:
                data["jsonProjectBasePoint"] = content["projectBasePoint"]
            if "surveyPoint" in content:
                data["jsonSurveyPoint"] = content["surveyPoint"]

        # 2) Family file sizes: distinct from placed_families
        elif dtype == "family_sizes":
            # the raw array
            data["jsonFamily_sizes"] = json.dumps(blob.get("data", []))
            # include its own metadata section
            data["jsonFamilyFileSizesMetadata"] = json.dumps(blob.get("metadata", {}))
            # include its count
            data["nFamilyFileSizesCount"] = blob.get("family_count")

        # 3) Placed families (actual loaded families)
        elif dtype == "placed_families":
            data["jsonFamilies"] = json.dumps(blob.get("data", []))

        # 4) Views / rooms / levels / grids / phases / warnings / design_options / schedules / title_blocks / worksets
        elif dtype == "views_rooms_levels":
            content = blob.get("data", {}) or {}
            data["jsonViews"]                = json.dumps(content.get("views", []))
            data["jsonLevels"]               = json.dumps(content.get("levels", []))
            data["jsonRooms"]                = json.dumps(content.get("rooms", []))
            data["jsonGrids"]                = json.dumps(content.get("grids", []))
            data["jsonPhases"]               = json.dumps(content.get("phases", []))
            data["jsonDesignOptions"]        = json.dumps(content.get("design_options", []))
            data["jsonSchedules"]            = json.dumps(content.get("schedules", []))
            data["jsonTitleBlocksSummary"]   = json.dumps(content.get("title_blocks", []))
            data["jsonWorksets"]             = json.dumps(content.get("worksets", []))
            data["jsonWarnings"]             = json.dumps(content.get("warnings", []))

        # 5) Any other single-array exports
        elif isinstance(blob, dict) and isinstance(blob.get("data"), list):
            # already handled family_sizes/placed_families above
            # warnings, lines, grids, etc can be expanded here if standalone
            pass

    # Ensure every expected key is present (None if missing)
    for key in ORDERED_KEYS:
        data.setdefault(key, None)

    # Print summary
    print("\n📦 Combined Data Summary for project:")
    for key in ORDERED_KEYS:
        status = "✅ Included" if data[key] is not None else "⚠️  Missing"
        print(f"   {status}: {key}")

    # Return only in the specified order
    return {key: data[key] for key in ORDERED_KEYS}


def combine_exports_to_single_file(export_dir: str) -> str:
    processed_dir = _ensure_processed_dir(export_dir)
    projects = {}
    for f in os.listdir(export_dir):
        if not f.endswith(".json") or f.lower().startswith("combined_"):
            continue
        proj, _ = extract_project_and_timestamp(f)
        if not proj:
            continue
        projects.setdefault(proj, []).append(f)

    for proj, files in projects.items():
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out = os.path.join(export_dir, f"combined_{proj}_{timestamp}.json")
        combined = combine_files_into_dict(export_dir, files)
        # ensure credentials placeholders
        combined.setdefault("strRvtUserName", combined.get("strRvtUserName", "Unknown"))
        combined.setdefault("strSysName",     combined.get("strSysName",     "Unknown"))
        # master export time
        combined["nExportedOn"] = int(datetime.datetime.utcnow().timestamp())

        with open(out, "w", encoding="utf-8") as fp:
            json.dump(combined, fp, indent=2)
        print(f"✅ Combined project export created: {os.path.basename(out)}")

        # move processed files
        for f in files:
            src = os.path.join(export_dir, f)
            dst = os.path.join(processed_dir, f)
            try:
                os.rename(src, dst)
                print(f"📁 Moved {f} to processed folder.")
            except FileExistsError:
                print(f"⚠️  {f} already processed.")

    return export_dir
