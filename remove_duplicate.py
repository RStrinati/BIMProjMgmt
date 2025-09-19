print("Starting script...")
with open('phase1_enhanced_ui.py', 'r') as f:
    lines = f.readlines()

print(f'Total lines before: {len(lines)}')

# Find the duplicate ProjectSetupTab class (second occurrence)
duplicate_start = None
duplicate_end = None

class_count = 0
for i, line in enumerate(lines):
    if line.strip() == 'class ProjectSetupTab:':
        class_count += 1
        print(f'Found ProjectSetupTab class {class_count} at line {i + 1}')
        if class_count == 2:  # Second occurrence
            duplicate_start = i
            break

print(f'Duplicate start: {duplicate_start + 1 if duplicate_start else None}')

# Find the end of the duplicate class (next class definition)
if duplicate_start is not None:
    for i in range(duplicate_start + 1, len(lines)):
        if lines[i].strip().startswith('class ') and i > duplicate_start:
            duplicate_end = i - 1
            break

    if duplicate_end is None:
        duplicate_end = len(lines) - 1

    print(f'Duplicate end: {duplicate_end + 1}')

    print(f'Removing lines {duplicate_start + 1} to {duplicate_end + 1}')

    # Remove the duplicate class
    new_lines = lines[:duplicate_start] + lines[duplicate_end + 1:]

    print(f'Total lines after: {len(new_lines)}')

    # Write back to file
    with open('phase1_enhanced_ui.py', 'w') as f:
        f.writelines(new_lines)

    print('Duplicate class removed successfully!')
else:
    print('Could not find duplicate class')