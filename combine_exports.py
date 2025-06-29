import os
import json
import datetime

EXPORT_DIR = r"C:\Users\RicoStrinati\Documents\research\HealthCheck\dynamo\exports"
PROCESSED_DIR = os.path.join(EXPORT_DIR, "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

def extract_project_and_timestamp(filename):
    parts = filename.replace(".json", "").split("_")
    if len(parts) < 3:
        return None, None
    project = parts[1]
    timestamp = "_".join(parts[2:])
    return project, timestamp

def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def find_latest_files_by_project():
    grouped = {}
    for file in os.listdir(EXPORT_DIR):
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

def combine_files(project, timestamp, file_list):
    data = {
        "strRvtFileName": project,
        "nExportedOn": int(datetime.datetime.utcnow().timestamp())
    }

    for file in file_list:
        file_path = os.path.join(EXPORT_DIR, file)
        json_data = load_json(file_path)

        if "views" in json_data:
            data["jsonViews"] = json.dumps(json_data["views"])
        if "levels" in json_data:
            data["jsonLevels"] = json.dumps(json_data["levels"])
        if "rooms" in json_data:
            data["jsonRooms"] = json.dumps(json_data["rooms"])
        if "title_blocks" in json_data:
            data["jsonTitleBlocksSummary"] = json.dumps(json_data["title_blocks"])
        if isinstance(json_data, list) and "FamilyName" in json_data[0]:
            # From family size script
            data["jsonFamilySizes"] = json.dumps(json_data)
        if isinstance(json_data, list) and "TypeName" in json_data[0]:
            # From placed family script
            data["jsonFamilies"] = json.dumps(json_data)

    combined_filename = f"combined_{project}_{timestamp}.json"
    combined_path = os.path.join(EXPORT_DIR, combined_filename)
    with open(combined_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Combined export created: {combined_filename}")

    # Move source files
    for file in file_list:
        src = os.path.join(EXPORT_DIR, file)
        dst = os.path.join(PROCESSED_DIR, file)
        os.rename(src, dst)
        print(f"📁 Moved {file} to processed folder.")

def main():
    groups = find_latest_files_by_project()
    for (project, timestamp), files in groups.items():
        combine_files(project, timestamp, files)

if __name__ == "__main__":
    main()
