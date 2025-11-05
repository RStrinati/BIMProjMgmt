import os
import json
import shutil
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional

from config import Config
from constants.schema import TblRvtProjHealth, TblRvtUser, TblSysName, TblRvtFamilySummary
from services.revit_naming_validator_service import RevitNamingValidator

REVIT_HEALTH_DB = Config.REVIT_HEALTH_DB
LOG_FILE = "rvt_import_summary.txt"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")


def _coerce_size_mb(raw_value: Optional[str]) -> Optional[float]:
    """Convert a size string to float MB when possible."""
    if raw_value is None:
        return None
    if isinstance(raw_value, (int, float)):
        try:
            return float(raw_value)
        except (TypeError, ValueError):
            return None
    if isinstance(raw_value, str):
        value = raw_value.strip().lower()
        if not value or "unavailable" in value or value in {"na", "n/a"}:
            return None
        # Remove non-numeric characters except dot
        filtered = "".join(ch for ch in value if ch.isdigit() or ch == ".")
        if not filtered:
            return None
        try:
            return float(filtered)
        except ValueError:
            return None
    return None


def _persist_family_details(cursor, health_check_id: int,
                            family_sizes: List[Dict], placed_families: List[Dict]) -> None:
    """Persist summarised family metadata to dedicated table."""
    if not family_sizes and not placed_families:
        return

    try:
        cursor.execute(
            f"DELETE FROM {TblRvtFamilySummary.TABLE} WHERE {TblRvtFamilySummary.HEALTH_CHECK_ID} = ?",
            health_check_id
        )
    except Exception as exc:
        log(f"[WARNING] Skipping family summary storage for health check {health_check_id}: {exc}")
        return

    merged: Dict[str, Dict[str, Optional[object]]] = {}

    for entry in family_sizes or []:
        name = entry.get("FamilyName") or entry.get("family_name")
        if not name:
            continue
        name = str(name).strip()
        if not name:
            continue

        record = merged.setdefault(name, {
            "category": None,
            "instance_count": None,
            "size_mb": None,
            "file_path": None,
            "shared_parameters_json": None,
        })
        size_mb = _coerce_size_mb(entry.get("SizeMB"))
        if size_mb is not None:
            record["size_mb"] = size_mb
        file_path = entry.get("FilePath")
        if file_path:
            record["file_path"] = str(file_path)
        shared_params = entry.get("SharedParameters")
        if shared_params:
            try:
                record["shared_parameters_json"] = json.dumps(shared_params)
            except (TypeError, ValueError):
                record["shared_parameters_json"] = None

    for entry in placed_families or []:
        name = entry.get("FamilyName") or entry.get("family_name")
        if not name:
            continue
        name = str(name).strip()
        if not name:
            continue
        record = merged.setdefault(name, {
            "category": None,
            "instance_count": None,
            "size_mb": None,
            "file_path": None,
            "shared_parameters_json": None,
        })
        category = entry.get("Category") or entry.get("category")
        if category:
            record["category"] = str(category)
        count = entry.get("Count") or entry.get("count") or entry.get("Instances") or entry.get("instances")
        if count is not None:
            try:
                record["instance_count"] = int(count)
            except (TypeError, ValueError):
                pass

    if not merged:
        return

    payload = [
        (
            health_check_id,
            family_name,
            details.get("category"),
            details.get("instance_count"),
            details.get("size_mb"),
            details.get("file_path"),
            details.get("shared_parameters_json"),
        )
        for family_name, details in merged.items()
    ]

    try:
        cursor.executemany(f"""
            INSERT INTO {TblRvtFamilySummary.TABLE} (
                {TblRvtFamilySummary.HEALTH_CHECK_ID},
                {TblRvtFamilySummary.FAMILY_NAME},
                {TblRvtFamilySummary.CATEGORY},
                {TblRvtFamilySummary.INSTANCE_COUNT},
                {TblRvtFamilySummary.SIZE_MB},
                {TblRvtFamilySummary.FILE_PATH},
                {TblRvtFamilySummary.SHARED_PARAMETERS_JSON}
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, payload)
        log(f"[FAMILY] Stored {len(payload)} family summary rows for health check {health_check_id}")
    except Exception as exc:
        log(f"[WARNING] Failed to insert family summary rows for health check {health_check_id}: {exc}")

def safe_float(v):
    """Return ``float(v)`` or ``None`` if conversion fails."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def import_health_data(json_folder, project_id=None, db_name=None):
    """
    Import Revit health data from a folder of JSON files.
    
    Args:
        json_folder: Path to folder containing JSON health check files
        project_id: Optional project ID for associating data with specific project
        db_name: Optional database name, defaults to REVIT_HEALTH_DB
    """
    # reset log
    open(LOG_FILE, "w").close()

    processed = os.path.join(json_folder, "processed")
    os.makedirs(processed, exist_ok=True)
    naming_validator = RevitNamingValidator()

    # Group JSON files by project_name
    project_data: Dict[str, Dict] = defaultdict(lambda: {
        "data": {},
        "files": [],
        "family_sizes": [],
        "placed_families": [],
    })
    json_files = [fn for fn in os.listdir(json_folder)
                 if fn.lower().endswith('.json') and fn != os.path.basename(LOG_FILE)]
    if not json_files:
        log("No JSON files found for combining.")
        return

    for fn in json_files:
        full = os.path.join(json_folder, fn)
        try:
            with open(full, "r", encoding="utf-8") as f:
                data = json.load(f)
            data_type = data.get("data_type")
            project_name = data.get("project_name")
            if not project_name:
                log(f"[WARNING] No project_name in {fn}, skipping")
                continue
            
            combined_data = project_data[project_name]["data"]
            project_data[project_name]["files"].append(fn)
            
            if data_type == "metadata":
                # Extract metadata fields to top level
                combined_data.update(data["data"])
            elif data_type == "family_sizes":
                family_entries = data.get("data") or []
                project_data[project_name]["family_sizes"] = family_entries
                combined_data["nFamilyCount"] = data.get("family_count", len(family_entries))
            elif data_type == "placed_families":
                placed_entries = data.get("data") or []
                project_data[project_name]["placed_families"] = placed_entries
            elif data_type == "views_rooms_levels":
                # Extract individual arrays from the data dict
                d = data["data"]
                combined_data["jsonViews"] = json.dumps(d.get("views", []))
                combined_data["jsonLevels"] = json.dumps(d.get("levels", []))
                combined_data["jsonRooms"] = json.dumps(d.get("rooms", []))
                combined_data["jsonSchedules"] = json.dumps(d.get("schedules", []))
                combined_data["jsonTitleBlocksSummary"] = json.dumps(d.get("title_blocks", []))
                combined_data["jsonDesignOptions"] = json.dumps(d.get("design_options", []))
                combined_data["jsonGrids"] = json.dumps(d.get("grids", []))
                combined_data["jsonPhases"] = json.dumps(d.get("phases", []))
                combined_data["jsonWorksets"] = json.dumps(d.get("worksets", []))
                combined_data["jsonWarnings"] = json.dumps(d.get("warnings", []))
                # Set counts
                combined_data["nTotalViewCount"] = len(d.get("views", []))
                combined_data["nSheetsCount"] = len(d.get("title_blocks", []))
                combined_data["nDesignOptionSetCount"] = len(d.get("design_options", []))
                combined_data["nDesignOptionCount"] = len(d.get("design_options", []))  # Assuming same
            else:
                log(f"Unknown data_type '{data_type}' in {fn}, skipping")
            log(f"[COMBINED] {fn} (project: {project_name}, type: {data_type})")
        except Exception as e:
            log(f"[ERROR] {fn}: {e}")

    # Process each project
    for project_file_name, project_info in project_data.items():
        combined_data = project_info["data"]
        family_sizes = project_info.get("family_sizes", [])
        placed_families = project_info.get("placed_families", [])
        project_files = project_info["files"]
        # Save combined file
        file_identifier = project_file_name.replace(" ", "_").replace("/", "-")
        combined_fn = f"combined_{file_identifier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        combined_path = os.path.join(json_folder, combined_fn)
        with open(combined_path, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, indent=2)
        log(f"[SAVED] {combined_fn}")

        # Database insertion logic here (same as before, but inside the loop)
        if db_name is None:
            db_name = REVIT_HEALTH_DB
        
        try:
            from database_pool import get_db_connection
            with get_db_connection(db_name) as conn:
                cursor = conn.cursor()
                log(f"Connected to DB: {cursor.execute('SELECT DB_NAME()').fetchone()[0]}")

                # define the JSON→DB columns we want
                MAPPING = [
                    ("strRvtVersion",       "strRvtVersion"),
                    ("strRvtBuildVersion",  "strRvtBuildVersion"),
                    ("strRvtFileName",      "strRvtFileName"),
                    ("strProjectName",      "strProjectName"),
                    ("strProjectNumber",    "strProjectNumber"),
                    ("strClientName",       "strClientName"),
                    ("nRvtLinkCount",       "nRvtLinkCount"),
                    ("nDwgLinkCount",       "nDwgLinkCount"),
                    ("nDwgImportCount",     "nDwgImportCount"),
                    ("nTotalViewCount",     "nTotalViewCount"),
                    ("nCopiedViewCount",     "nCopiedViewCount"),
                    ("nDependentViewCount", "nDependentViewCount"),
                    ("nViewsNotOnSheetsCount", "nViewsNotOnSheetsCount"),
                    ("nViewTemplateCount",  "nViewTemplateCount"),
                    ("nWarningsCount",      "nWarningsCount"),
                    ("nCriticalWarningsCount","nCriticalWarningsCount"),
                    ("nFamilyCount",        "nFamilyCount"),
                    ("nGroupCount",         "nGroupCount"),
                    ("nDetailGroupTypeCount","nDetailGroupTypeCount"),
                    ("nModelGroupTypeCount","nModelGroupTypeCount"),
                    ("nTotalElementsCount", "nTotalElementsCount"),
                    ("nModelFileSizeMB",    "nModelFileSizeMB"),
                    # the big JSON blobs
                    ("jsonDesignOptions",      "jsonDesignOptions"),
                    ("jsonFamily_sizes",       "jsonFamily_sizes"),
                    ("jsonGrids",              "jsonGrids"),
                    ("jsonLevels",             "jsonLevels"),
                    ("jsonPhases",             "jsonPhases"),
                    ("jsonFamilies",           "jsonFamilies"),
                    ("jsonRooms",              "jsonRooms"),
                    ("jsonSchedules",          "jsonSchedules"),
                    ("jsonProjectBasePoint",   "jsonProjectBasePoint"),
                    ("jsonSurveyPoint",        "jsonSurveyPoint"),
                    ("jsonTitleBlocksSummary", "jsonTitleBlocksSummary"),
                    ("jsonViews",              "jsonViews"),
                    ("jsonWarnings",          "jsonWarnings"),
                    ("jsonWorksets",           "jsonWorksets"),
                    # extra counts / timestamps
                    ("nInPlaceFamiliesCount",  "nInPlaceFamiliesCount"),
                    ("nSketchupImportsCount",  "nSketchupImportsCount"),
                    ("nSheetsCount",           "nSheetsCount"),
                    ("nDesignOptionSetCount",  "nDesignOptionSetCount"),
                    ("nDesignOptionCount",     "nDesignOptionCount"),
                    ("nExportedOn",            "nExportedOn"),
                ]

                # upsert user
                user_name = (
                    combined_data.get("strRvtUserName")
                    or combined_data.get("rvtUserName")
                    or combined_data.get("user")
                    or "UnknownUser"
                )
                cursor.execute(
                    f"SELECT {TblRvtUser.NID} FROM {TblRvtUser.TABLE} WHERE {TblRvtUser.RVT_USERNAME}=?", 
                    user_name
                )
                r = cursor.fetchone()
                user_id = r[0] if r else cursor.execute(
                    f"INSERT INTO {TblRvtUser.TABLE} ({TblRvtUser.RVT_USERNAME}) OUTPUT INSERTED.{TblRvtUser.NID} VALUES (?)",
                    user_name
                ).fetchone()[0]

                # upsert sysname
                sys_name = (
                    combined_data.get("strSysName")
                    or combined_data.get("sysUserName")
                    or os.path.splitext(combined_fn)[0]
                )
                cursor.execute(
                    f"SELECT {TblSysName.NID} FROM {TblSysName.TABLE} WHERE {TblSysName.SYS_USERNAME}=?", 
                    sys_name
                )
                r = cursor.fetchone()
                sys_id = r[0] if r else cursor.execute(
                    f"INSERT INTO {TblSysName.TABLE} ({TblSysName.SYS_USERNAME}) OUTPUT INSERTED.{TblSysName.NID} VALUES (?)",
                    sys_name
                ).fetchone()[0]

                # Add project association if project_id provided
                if project_id is not None:
                    log(f"Associating data with project ID: {project_id}")

                # Normalise coordinate payload keys coming from newer exporters
                if "surveyPoint" in combined_data and "jsonSurveyPoint" not in combined_data:
                    combined_data["jsonSurveyPoint"] = combined_data["surveyPoint"]
                if "projectBasePoint" in combined_data and "jsonProjectBasePoint" not in combined_data:
                    combined_data["jsonProjectBasePoint"] = combined_data["projectBasePoint"]
                if "internalOrigin" in combined_data and "jsonInternalOrigin" not in combined_data:
                    combined_data["jsonInternalOrigin"] = combined_data["internalOrigin"]

                # build columns + values
                cols = ["nRvtUserId", "nSysNameId"] + [db_col for _,db_col in MAPPING]
                vals = [user_id, sys_id]
                for json_key, _ in MAPPING:
                    v = combined_data.get(json_key)
                    if json_key in ("jsonProjectBasePoint","jsonSurveyPoint") and v is not None:
                        vals.append(json.dumps(v))
                    else:
                        vals.append(v)

                # placeholders
                ph = ",".join("?" for _ in vals)

                sql = f"""
                    INSERT INTO {TblRvtProjHealth.TABLE} (
                      {','.join(cols)}
                    )
                    VALUES ({ph})
                """
                cursor.execute(sql, vals)
                # SCOPE_IDENTITY() avoids trigger conflicts with OUTPUT clauses.
                cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                inserted_row = cursor.fetchone()
                health_check_id = inserted_row[0] if inserted_row and inserted_row[0] else None

                if not health_check_id:
                    # Fallback lookup when SCOPE_IDENTITY returns no value (e.g. triggers/identity gaps)
                    fallback_params = []
                    where_clauses = []

                    file_name = combined_data.get("strRvtFileName")
                    if file_name:
                        where_clauses.append(f"{TblRvtProjHealth.STR_RVT_FILENAME} = ?")
                        fallback_params.append(file_name)

                    exported_on = combined_data.get("nExportedOn")
                    if exported_on is not None:
                        where_clauses.append(f"{TblRvtProjHealth.NEXPORTEDON} = ?")
                        fallback_params.append(exported_on)

                    if fallback_params:
                        fallback_sql = f"""
                            SELECT TOP 1 {TblRvtProjHealth.NID}
                            FROM {TblRvtProjHealth.TABLE}
                            WHERE {' AND '.join(where_clauses)}
                            ORDER BY {TblRvtProjHealth.NID} DESC
                        """
                        cursor.execute(fallback_sql, fallback_params)
                        fallback_row = cursor.fetchone()
                        if fallback_row:
                            health_check_id = fallback_row[0]
                            log(f"[INFO] Resolved health check ID via fallback: {health_check_id} ({project_file_name})")
                        else:
                            log(f"[WARNING] Unable to resolve health check ID for {project_file_name} after insert")
                    else:
                        log(f"[WARNING] Missing keys to resolve health check ID for {project_file_name}")

                if health_check_id:
                    _persist_family_details(cursor, health_check_id, family_sizes, placed_families)

                conn.commit()
                log(f"[OK] inserted {combined_fn} for project {project_file_name}")
                if health_check_id:
                    try:
                        naming_validator.validate_new_health_check(health_check_id)
                        log(f"[NAMING] Validated naming for health check ID {health_check_id}")
                    except Exception as validation_error:
                        log(f"[WARNING] Naming validation failed for health check {health_check_id}: {validation_error}")
                shutil.move(combined_path, os.path.join(processed, combined_fn))
                log(f"[MOVED] {combined_fn}")
                
                # Move individual files for this project to processed folder
                for individual_file in project_files:
                    src_path = os.path.join(json_folder, individual_file)
                    dst_path = os.path.join(processed, individual_file)
                    if os.path.exists(src_path):
                        shutil.move(src_path, dst_path)
                        log(f"[MOVED] {individual_file} (individual file)")
        except Exception as e:
            log(f"ERROR: Database operation failed for project {project_file_name}: {e}")
            raise
    
    log("All projects processed.")
