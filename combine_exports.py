"""Utility for merging multiple Revit health export JSON files.

This module was originally a standalone script. The ``combine_exports`` function
exposes the same behaviour for use by other modules (e.g. the health importer).
When executed directly it behaves like the original script using the hard coded
``EXPORT_DIR`` path.
"""

import os
import json
import re
import shutil
from collections import defaultdict
from datetime import datetime


EXPORT_DIR = r"C:/Users/RicoStrinati/Documents/research/HealthCheck/dynamo/exports"


def combine_exports(export_dir: str) -> str:
    """Combine JSON parts located in ``export_dir``.

    Parameters
    ----------
    export_dir : str
        Folder containing JSON parts exported from Revit.

    Returns
    -------
    str
        Path to the directory containing the combined JSON files.
    """

    processed_dir = os.path.join(export_dir, "processed")
    combined_dir = os.path.join(export_dir, "combined")
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(combined_dir, exist_ok=True)

    # Regex pattern to extract type, project filename and timestamp
    token_pattern = re.compile(r"^(.*?)_([^_]+)_((?:\d{8}_\d{6})).json$")

    groups = defaultdict(dict)
    for file in os.listdir(export_dir):
        if not file.endswith(".json"):
            continue
        match = token_pattern.match(file)
        if not match:
            continue
        type_key, proj_name, timestamp = match.groups()
        groups[(proj_name, timestamp)][type_key] = os.path.join(export_dir, file)

    for (proj_name, timestamp), parts in groups.items():
        merged = {"project": proj_name, "timestamp": timestamp}
        for part_name, filepath in parts.items():
            with open(filepath, "r") as f:
                try:
                    merged[f"json_{part_name}"] = json.load(f)
                except Exception as e:
                    print(f"❌ Failed to load {filepath}: {e}")
                    continue
            shutil.move(filepath, os.path.join(processed_dir, os.path.basename(filepath)))

        output_filename = f"merged_{proj_name}_{timestamp}.json"
        output_path = os.path.join(combined_dir, output_filename)
        with open(output_path, "w") as out_file:
            json.dump(merged, out_file, indent=2)
        print(f"✅ Combined JSON created: {output_path}")

    return combined_dir


if __name__ == "__main__":
    combine_exports(EXPORT_DIR)
