import os
import json
import pandas as pd

# Define the folder where JSON files are stored
json_folder = r"C:\Users\RicoStrinati\Documents\research\ReviztoAPI\ReviztoDataExporter"

# Lists to hold cleaned data
projects_data = []
members_data = []

# Process JSON files
for file_name in os.listdir(json_folder):
    file_path = os.path.join(json_folder, file_name)

    # Skip non-JSON files
    if not file_name.endswith(".json"):
        continue

    print(f"Processing file: {file_name}")
    
    # Read JSON file
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format in file: {file_name}. Error: {e}")
        continue

    # Debug: Print the top-level keys in the JSON
    print(f"Top-level keys in {file_name}: {list(data.keys())}")

    # Process license projects
    if "licenseprojects" in file_name.lower():
        projects = data.get("data", {}).get("data", [])  # Navigate to the nested "data" key
        print(f"Found {len(projects)} projects in {file_name}")
        for project in projects:
            # Append project data
            projects_data.append({
                "project_id": project.get("id"),
                "project_uuid": project.get("uuid"),
                "title": project.get("title"),  # Extract project title as project_name
                "created": project.get("created"),
                "updated": project.get("updated"),
                "license_id": project.get("license_id"),
                "region": project.get("region"),
                "owner_name": project.get("owner", {}).get("fullname"),
                "owner_email": project.get("owner", {}).get("email"),
                "last_active": project.get("lastActive"),
                "members_count": project.get("members"),
            })

    # Process project members
    elif "projectmembers" in file_name.lower():
        members = data.get("data", {}).get("entities", [])  # Navigate to nested entities
        print(f"Found {len(members)} members in {file_name}")
        for member in members:
            # Append member data
            members_data.append({
                "member_id": member.get("id"),
                "member_uuid": member.get("uuid"),
                "member_name": member.get("fullname"),
                "member_email": member.get("email"),
                "project_uuid": member.get("member", {}).get("uuid"),  # Extract project UUID
                "role": member.get("member", {}).get("role"),  # Include role
                "company": member.get("company"),
                "department": member.get("department"),
                "location": member.get("location"),
                "access_level": member.get("accesslevel"),
            })

# Convert data to pandas DataFrames
projects_df = pd.DataFrame(projects_data)
members_df = pd.DataFrame(members_data)

# Debug: Check DataFrame structure
print("Projects DataFrame:")
print(projects_df.head())
print("Members DataFrame:")
print(members_df.head())

# Verify project_uuid presence in both DataFrames
if "project_uuid" not in projects_df.columns or "project_uuid" not in members_df.columns:
    print("Error: 'project_uuid' is missing in one or both DataFrames. Skipping merge.")
else:
    # Debug: Print unique project_uuid values
    print("Unique project_uuid in members_df:")
    print(members_df['project_uuid'].unique())
    print("Unique project_uuid in projects_df:")
    print(projects_df['project_uuid'].unique())

    # Ensure data types match
    members_df['project_uuid'] = members_df['project_uuid'].astype(str)
    projects_df['project_uuid'] = projects_df['project_uuid'].astype(str)

    # Identify unmatched project_uuid values
    unmatched_projects = members_df[~members_df['project_uuid'].isin(projects_df['project_uuid'])]
    print("Unmatched project_uuid in members_df:")
    print(unmatched_projects)

    # Merge projects and members data on 'project_uuid'
    merged_df = pd.merge(members_df, projects_df, on="project_uuid", how="left")

    # Debug: Check merged DataFrame
    print("Merged DataFrame:")
    print(merged_df.head())

    # Export consolidated data to CSV
    output_path = os.path.join(json_folder, "consolidated_data.csv")
    merged_df.to_csv(output_path, index=False)
    print(f"Consolidated data saved to {output_path}")
