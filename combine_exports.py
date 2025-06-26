# combine_exports.py
# Combines all JSON exports from Revit into a single merged JSON per project and timestamp

import os
import json
import re
import shutil
from collections import defaultdict
from datetime import datetime

EXPORT_DIR = r"C:/Users/RicoStrinati/Documents/research/HealthCheck/dynamo/exports"
PROCESSED_DIR = os.path.join(EXPORT_DIR, "processed")
COMBINED_DIR = os.path.join(EXPORT_DIR, "combined")
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(COMBINED_DIR, exist_ok=True)

# Regex pattern to extract type, filename and timestamp
token_pattern = re.compile(r"^(.*?)_([^_]+)_((?:\d{8}_\d{6})).json$")

# Collect files by project and timestamp
groups = defaultdict(dict)
for file in os.listdir(EXPORT_DIR):
    if not file.endswith(".json"):
        continue
    match = token_pattern.match(file)
    if not match:
        continue
    type_key, proj_name, timestamp = match.groups()
    groups[(proj_name, timestamp)][type_key] = os.path.join(EXPORT_DIR, file)

# Combine grouped files
for (proj_name, timestamp), parts in groups.items():
    merged = {"project": proj_name, "timestamp": timestamp}
    for part_name, filepath in parts.items():
        with open(filepath, "r") as f:
            try:
                merged[f"json_{part_name}"] = json.load(f)
            except Exception as e:
                print(f"❌ Failed to load {filepath}: {e}")
                continue
        shutil.move(filepath, os.path.join(PROCESSED_DIR, os.path.basename(filepath)))

    output_filename = f"merged_{proj_name}_{timestamp}.json"
    output_path = os.path.join(COMBINED_DIR, output_filename)
    with open(output_path, "w") as out_file:
        json.dump(merged, out_file, indent=2)
    print(f"✅ Combined JSON created: {output_path}")
