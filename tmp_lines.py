from pathlib import Path
path = Path('constants/schema.py')
for idx, line in enumerate(path.read_text().splitlines(), start=1):
    if 'TblRvtFamilySummary' in line:
        print(idx, line)
