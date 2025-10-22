import os
import json
import shutil
from datetime import datetime
from collections import defaultdict

from config import Config
from constants.schema import TblRvtProjHealth, TblRvtUser, TblSysName

REVIT_HEALTH_DB = Config.REVIT_HEALTH_DB
LOG_FILE = "rvt_import_summary.txt"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

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

    # Group JSON files by project_name
    combined_by_project = defaultdict(dict)
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
            
            combined_data = combined_by_project[project_name]
            
            if data_type == "metadata":
                # Extract metadata fields to top level
                combined_data.update(data["data"])
            elif data_type == "family_sizes":
                # Store family sizes as JSON string
                combined_data["jsonFamily_sizes"] = json.dumps(data["data"])
            elif data_type == "placed_families":
                # Store placed families as JSON string
                combined_data["jsonFamilies"] = json.dumps(data["data"])
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
    for project_file_name, combined_data in combined_by_project.items():
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
                    ) VALUES ({ph})
                """
                cursor.execute(sql, vals)
                conn.commit()
                log(f"[OK] inserted {combined_fn} for project {project_file_name}")
                shutil.move(combined_path, os.path.join(processed, combined_fn))
                log(f"[MOVED] {combined_fn}")
        except Exception as e:
            log(f"ERROR: Database operation failed for project {project_file_name}: {e}")
            raise
    
    log("All projects processed.")
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
                ("nCopiedViewCount",    "nCopiedViewCount"),
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
                ("jsonWarnings",           "jsonWarnings"),
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
                ) VALUES ({ph})
            """
            cursor.execute(sql, vals)
            conn.commit()
            log(f"[OK] inserted {combined_fn}")
            shutil.move(combined_path, os.path.join(processed, combined_fn))
            log(f"[MOVED] {combined_fn}")
            log("All done.")
    except Exception as e:
        log(f"ERROR: Database operation failed: {e}")
        raise
