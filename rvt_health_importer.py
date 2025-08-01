import os
import json
import shutil
from datetime import datetime

from config import Config
REVIT_HEALTH_DB = Config.REVIT_HEALTH_DB

from combine_exports import combine_exports_to_single_file
from database import connect_to_db

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

def import_health_data(json_folder, db_name=None):
    # reset log
    open(LOG_FILE, "w").close()

    # combine exports into one JSON file
    try:
        json_folder = combine_exports_to_single_file(json_folder)
    except Exception as e:
        log(f"[ERROR] combine_exports failed: {e}")
        return

    processed = os.path.join(json_folder, "processed")
    os.makedirs(processed, exist_ok=True)

    # connect
    if db_name is None:
        db_name = REVIT_HEALTH_DB
    conn = connect_to_db(db_name)
    cursor = conn.cursor()
    log(f"Connected to DB: {cursor.execute('SELECT DB_NAME()').fetchone()[0]}")

    # define the JSON→DB columns we want
    #
    # Note: nRvtUserId, nSysNameId get set separately
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

    for fn in os.listdir(json_folder):
        if not fn.lower().startswith("combined_") or not fn.endswith(".json"):
            log(f"[SKIP] {fn}")
            continue

        full = os.path.join(json_folder, fn)
        log(f"[FILE] {fn}")

        try:
            data = json.load(open(full, "r", encoding="utf-8"))
            log(f"  JSON keys: {list(data.keys())}")

            # upsert user
            cursor.execute(
                "SELECT nId FROM tblRvtUser WHERE rvtUserName=?", data["strRvtUserName"]
            )
            r = cursor.fetchone()
            user_id = r[0] if r else cursor.execute(
                "INSERT INTO tblRvtUser (rvtUserName) OUTPUT INSERTED.nId VALUES (?)",
                data["strRvtUserName"]
            ).fetchone()[0]

            # upsert sysname
            cursor.execute(
                "SELECT nId FROM tblSysName WHERE sysUserName=?", data["strSysName"]
            )
            r = cursor.fetchone()
            sys_id = r[0] if r else cursor.execute(
                "INSERT INTO tblSysName (sysUserName) OUTPUT INSERTED.nId VALUES (?)",
                data["strSysName"]
            ).fetchone()[0]

            # build columns + values
            cols = ["nRvtUserId", "nSysNameId"] + [db_col for _,db_col in MAPPING]
            vals = [user_id, sys_id]
            for json_key, _ in MAPPING:
                v = data.get(json_key)
                # if it’s one of the two JSON objects, dump to text
                if json_key in ("jsonProjectBasePoint","jsonSurveyPoint") and v is not None:
                    vals.append(json.dumps(v))
                else:
                    vals.append(v)

            # placeholders
            ph = ",".join("?" for _ in vals)

            sql = f"""
                INSERT INTO tblRvtProjHealth (
                  {','.join(cols)}
                ) VALUES ({ph})
            """
            cursor.execute(sql, vals)
            conn.commit()

            log(f"[OK] inserted {fn}")
            shutil.move(full, os.path.join(processed, fn))
            log(f"[MOVED] {fn}")

        except Exception as e:
            log(f"[ERROR] {fn}: {e}")

    cursor.close()
    conn.close()
    log("All done.")
