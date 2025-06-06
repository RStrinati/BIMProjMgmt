from database import connect_to_db  # ✅ Use shared DB connection
import ifcopenshell
import ifcopenshell.util.file
import os
import pyodbc
from datetime import datetime

def convert_ifc_coordinates(coord):
    """Convert IFC latitude/longitude tuple (D, M, S) to decimal degrees."""
    if isinstance(coord, tuple) and len(coord) == 3:
        degrees, minutes, seconds = coord
        return degrees + (minutes / 60) + (seconds / 3600)
    elif isinstance(coord, (int, float)):  # Already a valid number
        return coord
    else:
        return 0.0  # Default if None or invalid

def extract_ifc_data(ifc_file_path):
    """Extract data from a single IFC file and ensure proper data types."""
    print(f"Processing File: {ifc_file_path}")
    ifc_file = ifcopenshell.open(ifc_file_path)

    file_name = os.path.basename(ifc_file_path)
    header_info = ifcopenshell.util.file.IfcHeaderExtractor(ifc_file_path).extract()

    file_description = str(header_info.get('description', 'Not available'))  # ✅ Ensure string
    file_schema = str(header_info.get('schema_name', 'Not available'))  # ✅ Ensure string

    sites = ifc_file.by_type('IfcSite')
    site_coordinates = []
    for s in sites:
        try:
            lat = convert_ifc_coordinates(s.RefLatitude) if hasattr(s, 'RefLatitude') and s.RefLatitude is not None else 0.0
            lon = convert_ifc_coordinates(s.RefLongitude) if hasattr(s, 'RefLongitude') and s.RefLongitude is not None else 0.0
            site_coordinates.append((lat, lon))
        except ValueError:
            print(f"⚠️ Invalid latitude/longitude for {file_name}. Skipping...")

    storeys = ifc_file.by_type('IfcBuildingStorey')
    levels = []
    for s in storeys:
        try:
            level_name = str(s.Name) if hasattr(s, 'Name') else "Unknown"
            elevation = float(s.Elevation) if hasattr(s, 'Elevation') and s.Elevation is not None else None
            levels.append((level_name, elevation))
        except ValueError:
            print(f"⚠️ Invalid elevation data for {file_name}. Skipping...")
            
                    # Extract Uniclass & SINSW parameters
    sinsw_uniclass = []
    for rel in ifc_file.by_type("IfcRelDefinesByProperties"):
        element = rel.RelatedObjects[0] if rel.RelatedObjects else None
        pset = rel.RelatingPropertyDefinition
        if pset.is_a("IfcPropertySet"):
            for prop in pset.HasProperties:
                name = prop.Name
                if not name:
                    continue
                val = getattr(prop, "NominalValue", None)
                sinsw_uniclass.append({
                        "element_id": element.GlobalId if element else None,
                        "pset_name": pset.Name,
                        "prop_name": name,
                        "prop_value": str(val) if val is not None else None
                })


    return {
    "file_name": file_name,
    "file_description": file_description,
    "file_schema": file_schema,
    "site_coordinates": site_coordinates,
    "levels": levels,
    "sin_uniclass": sinsw_uniclass
    }

def insert_ifc_data_to_db(data):
    """Insert IFC data into the database."""
    conn = connect_to_db("RevitHealthCheckDB")  # ✅ Ensure correct DB connection
    cursor = conn.cursor()
    current_date = datetime.now()

    try:
        if not data["site_coordinates"] and not data["levels"]:
            print("⚠️ No valid IFC data found. Skipping database insertion.")
            return  # ✅ Prevent empty `executemany()`

        # ✅ Insert site coordinates
        for lat, lon in data["site_coordinates"]:
            cursor.execute("""
                INSERT INTO dbo.tblIFCData (file_name, description, schema_name, site_latitude, site_longitude, date_exported)
                VALUES (?, ?, ?, ?, ?, ?)
            """, 
            data["file_name"], 
            data["file_description"], 
            data["file_schema"], 
            lat if lat is not None else 0,  # ✅ Replace None with 0
            lon if lon is not None else 0,  # ✅ Replace None with 0
            current_date)

        # ✅ Insert levels
        for level_name, elevation in data["levels"]:
            cursor.execute("""
                INSERT INTO dbo.tblIFCData (file_name, description, schema_name, level_name, level_elevation, date_exported)
                VALUES (?, ?, ?, ?, ?, ?)
            """, data["file_name"], data["file_description"], data["file_schema"], level_name, elevation, current_date)
            
    # Insert SINSW / Uniclass properties
        for item in data.get("sin_uniclass", []):
            cursor.execute("""
                INSERT INTO dbo.tblIFCSharedParams 
                (file_name, element_id, pset_name, prop_name, prop_value, date_exported)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
            data["file_name"],
            item["element_id"],
            item["pset_name"],
            item["prop_name"],
            item["prop_value"],
            current_date)
            
        conn.commit()
        print("✅ Data committed to the database.")

    except pyodbc.Error as e:
        print(f"❌ Error inserting data: {e}")

    finally:
        conn.close()

def process_folder(folder_path):
    """Process all IFC files in a folder."""
    if not os.path.exists(folder_path):
        print(f"❌ Folder does not exist: {folder_path}")
        return

    files = [f for f in os.listdir(folder_path) if f.lower().endswith('.ifc')]
    if not files:
        print(f"⚠️ No IFC files found in folder: {folder_path}")
        return

    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        ifc_data = extract_ifc_data(file_path)
        insert_ifc_data_to_db(ifc_data)
