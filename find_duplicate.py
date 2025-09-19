with open('phase1_enhanced_ui.py', 'r') as f:
    lines = f.readlines()

print(f'Total lines: {len(lines)}')

# Find all ProjectSetupTab classes
class_lines = []
for i, line in enumerate(lines):
    if 'class ProjectSetupTab:' in line:
        class_lines.append(i + 1)  # 1-indexed

print(f'ProjectSetupTab classes found at lines: {class_lines}')

if len(class_lines) >= 2:
    duplicate_start = class_lines[1] - 1  # 0-indexed
    print(f'Duplicate starts at line {duplicate_start + 1}')

    # Find the end of the duplicate class (next class definition or end of file)
    duplicate_end = len(lines) - 1
    for i in range(duplicate_start + 1, len(lines)):
        if lines[i].strip().startswith('class ') and i > duplicate_start:
            duplicate_end = i - 1
            break

    print(f'Duplicate ends at line {duplicate_end + 1}')

    # Show context
    print('Before duplicate:')
    for i in range(max(0, duplicate_start-2), duplicate_start):
        print(f'{i+1}: {lines[i].rstrip()}')

    print('After duplicate:')
    for i in range(duplicate_end, min(len(lines), duplicate_end+3)):
        print(f'{i+1}: {lines[i].rstrip()}')