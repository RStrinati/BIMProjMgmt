with open('phase1_enhanced_ui.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all ProjectSetupTab classes
class_starts = []
for i, line in enumerate(lines):
    if line.strip() == 'class ProjectSetupTab:':
        class_starts.append(i)

print(f'Found ProjectSetupTab classes at lines: {[x+1 for x in class_starts]}')

if len(class_starts) >= 2:
    # Comment out the second class
    duplicate_start = class_starts[1]
    
    # Find the end of the duplicate class
    duplicate_end = len(lines) - 1
    for i in range(duplicate_start + 1, len(lines)):
        if lines[i].strip().startswith('class ') and i > duplicate_start:
            duplicate_end = i - 1
            break
    
    print(f'Commenting out duplicate class from line {duplicate_start + 1} to {duplicate_end + 1}')
    
    # Comment out the duplicate class
    for i in range(duplicate_start, duplicate_end + 1):
        if lines[i].strip():  # Only comment non-empty lines
            lines[i] = '# ' + lines[i]
    
    # Write back
    with open('phase1_enhanced_ui.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print('Duplicate class commented out!')
else:
    print('Could not find duplicate class')