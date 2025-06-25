import os
import json
import pyodbc
import shutil

from config import REVIT_HEALTH_DB

from database import connect_to_db


def safe_float(value):
    try:
        return float(value)
    except:
        return None
    
def import_health_data(json_folder, db_name=None):
    processed_folder = os.path.join(json_folder, "processed")
    os.makedirs(processed_folder, exist_ok=True)

    if db_name is None:
        db_name = REVIT_HEALTH_DB
    conn = connect_to_db(db_name)
    cursor = conn.cursor()

    print("🧠 Connected to DB:", cursor.execute("SELECT DB_NAME()").fetchone()[0])

    for file in os.listdir(json_folder):
        if not file.endswith(".json"):
            continue
        full_path = os.path.join(json_folder, file)
        print(f"📂 Processing: {file}")
        try:
            with open(full_path, "r") as f:
                data = json.load(f)

            cursor.execute("SELECT nId FROM tblRvtUser WHERE rvtUserName = ?", data["strRvtUserName"])
            row = cursor.fetchone()
            user_id = row[0] if row else cursor.execute(
                "INSERT INTO tblRvtUser (rvtUserName) OUTPUT INSERTED.nId VALUES (?)", data["strRvtUserName"]
            ).fetchone()[0]

            cursor.execute("SELECT nId FROM tblSysName WHERE sysUserName = ?", data["strSysName"])
            row = cursor.fetchone()
            sys_id = row[0] if row else cursor.execute(
                "INSERT INTO tblSysName (sysUserName) OUTPUT INSERTED.nId VALUES (?)", data["strSysName"]
            ).fetchone()[0]

            cursor.execute("""
                INSERT INTO tblRvtProjHealth (
                    nRvtUserId, nSysNameId, strRvtVersion, strRvtBuildVersion, strRvtFileName,
                    strProjectName, strProjectNumber, strClientName,
                    nRvtLinkCount, nDwgLinkCount, nDwgImportCount,
                    nTotalViewCount, nCopiedViewCount, nDependentViewCount,
                    nViewsNotOnSheetsCount, nViewTemplateCount,
                    nWarningsCount, nCriticalWarningsCount,
                    nFamilyCount, nGroupCount, nDetailGroupTypeCount, nModelGroupTypeCount,
                    nTotalElementsCount, jsonTypeOfElements,
                    nInPlaceFamiliesCount, nSketchupImportsCount, nSheetsCount,
                    nDesignOptionSetCount, nDesignOptionCount,
                    jsonDesignOptions, jsonDwgImports, jsonFamilies,
                    jsonLevels, jsonLines, jsonRooms, jsonViews, jsonWarnings, jsonWorksets,
                    nExportedOn, nDeletedOn,
                    validation_status, validation_reason,
                    strExtractedProjectName, compiled_regex,
                    jsonGrids, jsonProjectBasePoint, jsonSurveyPoint,
                    nModelFileSizeMB, jsonTitleBlocksSummary
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, sys_id,
                data.get("strRvtVersion"), data.get("strRvtBuildVersion"), data.get("strRvtFileName"),
                data.get("strProjectName"), data.get("strProjectNumber"), data.get("strClientName"),
                data.get("nRvtLinkCount", 0), 0, data.get("nDwgImportCount", 0),
                data.get("nTotalViewCount", 0), data.get("nCopiedViewCount", 0), data.get("nDependentViewCount", 0),
                data.get("nViewsNotOnSheetsCount", 0), data.get("nViewTemplateCount", 0),
                data.get("nWarningsCount", 0), data.get("nCriticalWarningsCount", 0),
                data.get("nFamilyCount", 0), data.get("nGroupCount", 0), data.get("nDetailGroupTypeCount", 0), data.get("nModelGroupTypeCount", 0),
                data.get("nTotalElementsCount", 0), data.get("jsonTypeOfElements"),
                data.get("nInPlaceFamiliesCount", 0), data.get("nSketchupImportsCount", 0), data.get("nSheetsCount", 0),
                data.get("nDesignOptionSetCount", 0), data.get("nDesignOptionCount", 0),
                data.get("jsonDesignOptions"), data.get("jsonDwgImports"), data.get("jsonFamilies"),
                data.get("jsonLevels"), data.get("jsonLines"), data.get("jsonRooms"), data.get("jsonViews"),
                data.get("jsonWarnings"), data.get("jsonWorksets"),
                data.get("nExportedOn"), None,
                None, None,
                data.get("strExtractedProjectName"), None,
                data.get("jsonGrids"),
                json.dumps(data.get("projectBasePoint")),
                json.dumps(data.get("surveyPoint")),
                safe_float(data.get("ModelFileSizeMB")),
                data.get("jsonTitleBlocksSummary")
            ))

            conn.commit()
            print(f"✅ Inserted: {file}")
            shutil.move(full_path, os.path.join(processed_folder, file))
            print(f"📁 Moved to: {processed_folder}\\{file}")
        except Exception as e:
            print(f"❌ Failed: {file}\n   Reason: {e}")

    cursor.close()
    conn.close()
    print("🎉 All files processed.")
