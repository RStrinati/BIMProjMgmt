"""Debug naming pattern matching"""
import re

# The pattern used in get_model_register
NAMING_PATTERN = r"^([A-Z0-9]{6})-([A-Z]{1,2})-([A-Z]{2})-([A-Z])-(\d{4})"

files = [
    "NFPS-SMS-ZZ-ZZ-M3-M-0001",
    "NFPS-SMS-ZZ-ZZ-M3-M-0001_detached.rvt",
    "NFPS-PDG-00-00-M3-L-0001.rvt",
    "NFPS-ACO-00-00-M3-C-0001",
]

for filename in files:
    # Uppercase for matching
    upper_fn = filename.upper()
    match = re.match(NAMING_PATTERN, upper_fn)
    if match:
        key = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        print(f'✓ {filename} → CORRECT (key: {key})')
    else:
        print(f'✗ {filename} → MISNAMED')
