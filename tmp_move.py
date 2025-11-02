import shutil
from pathlib import Path
base = Path('tmp_shutil_py')
processed = base / 'processed'
processed.mkdir(parents=True, exist_ok=True)
file_path = base / 'file.json'
file_path.write_text('{}')
processed_file = processed / 'file.json'
processed_file.write_text('old')
try:
    shutil.move(str(file_path), str(processed_file))
except Exception as e:
    print(type(e).__name__, e)
else:
    print('moved ok')
