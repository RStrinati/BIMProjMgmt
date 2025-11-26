with open('database.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for idx, line in enumerate(lines, start=1):
    if '_ensure_control_model_metadata_column' in line:
        for j in range(idx-5, idx+120):
            print(f"{j}: {lines[j-1].rstrip()}")
        break
