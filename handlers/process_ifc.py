from database import connect_to_db  # ✅ Use shared DB connection
import ifcopenshell
import ifcopenshell.util.file
import os
import pyodbc
from datetime import datetime
from collections import Counter

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
    author = header_info.get('author', 'Unknown')
    organization = header_info.get('organization', 'Unknown')
    timestamp = header_info.get('timestamp', 'Unknown')

    sites = ifc_file.by_type('IfcSite')
    site_coordinates = []
    for s in sites:
        try:
            lat = convert_ifc_coordinates(s.RefLatitude) if hasattr(s, 'RefLatitude') and s.RefLatitude is not None else 0.0
            lon = convert_ifc_coordinates(s.RefLongitude) if hasattr(s, 'RefLongitude') and s.RefLongitude is not None else 0.0
            site_coordinates.append((lat, lon))
        except ValueError:
            print(f"⚠️ Invalid latitude/longitude for {file_name}. Skipping...")

    # Project base point & model origin
    contexts = ifc_file.by_type("IfcGeometricRepresentationContext")
    origin_coords = None
    rotation_info = None
    if contexts:
        origin = contexts[0].WorldCoordinateSystem
        if origin:
            loc = origin.Location
            axis = origin.Axis
            origin_coords = loc.Coordinates if loc else None
            rotation_info = axis.DirectionRatios if axis else None

    # Collect building storeys, accounting for nesting
    storeys = list(ifc_file.by_type('IfcBuildingStorey'))
    for rel in ifc_file.by_type('IfcRelAggregates'):
        for obj in getattr(rel, 'RelatedObjects', []):
            if obj and obj.is_a('IfcBuildingStorey') and obj not in storeys:
                storeys.append(obj)
    for rel in ifc_file.by_type('IfcRelContainedInSpatialStructure'):
        storey = getattr(rel, 'RelatingStructure', None)
        if storey and storey.is_a('IfcBuildingStorey') and storey not in storeys:
            storeys.append(storey)

    levels = []
    for s in storeys:
        try:
            level_name = str(s.Name) if hasattr(s, 'Name') else "Unknown"
            elevation = float(s.Elevation) if hasattr(s, 'Elevation') and s.Elevation is not None else None
            levels.append((level_name, elevation))
        except ValueError:
            print(f"⚠️ Invalid elevation data for {file_name}. Skipping...")

    # Count elements per storey
    elements_per_storey = {}
    for rel in ifc_file.by_type('IfcRelContainedInSpatialStructure'):
        storey = rel.RelatingStructure
        if storey and storey.is_a('IfcBuildingStorey'):
            name = storey.Name or "Unnamed Storey"
            count = len(rel.RelatedElements)
            elements_per_storey[name] = elements_per_storey.get(name, 0) + count
    # Element count and type summary
    product_elements = ifc_file.by_type("IfcProduct")
    element_counts = Counter(e.is_a() for e in product_elements)
    total_elements = sum(element_counts.values())

    checked_elements = 0
    shared_param_hits = 0

    # Extract Uniclass & SINSW parameters
    sinsw_uniclass = []
    for rel in ifc_file.by_type("IfcRelDefinesByProperties"):
        element = rel.RelatedObjects[0] if rel.RelatedObjects else None
        pset = rel.RelatingPropertyDefinition
        if pset.is_a("IfcPropertySet"):
            checked_elements += 1
            has_sinsw_param = False
            for prop in pset.HasProperties:
                name = prop.Name
                if not name:
                    continue
                val = getattr(prop, "NominalValue", None)
                has_sinsw_param = True
                sinsw_uniclass.append({
                    "element_id": element.GlobalId if element else None,
                    "pset_name": pset.Name,
                    "prop_name": name,
                    "prop_value": str(val) if val is not None else None
                })
            if has_sinsw_param:
                shared_param_hits += 1


    return {
        "file_name": file_name,
        "file_description": file_description,
        "file_schema": file_schema,
        "author": author,
        "organization": organization,
        "timestamp": timestamp,
        "site_coordinates": site_coordinates,
        "origin_coords": origin_coords,
        "rotation_info": rotation_info,
        "levels": levels,
        "elements_per_storey": elements_per_storey,
        "element_counts": dict(element_counts),
        "total_elements": total_elements,
        "checked_elements": checked_elements,
        "shared_param_hits": shared_param_hits,
        "sin_uniclass": sinsw_uniclass,
    }

def insert_ifc_data_to_db(data):
    """Insert IFC data into the database."""
    from database_pool import get_db_connection
    current_date = datetime.now()

    try:
        with get_db_connection("RevitHealthCheckDB") as conn:
            cursor = conn.cursor()
            
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

    except Exception as e:
        print(f"❌ Error inserting data: {e}")

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
