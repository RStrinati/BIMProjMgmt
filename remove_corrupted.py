with open('phase1_enhanced_ui.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Original line count: {len(lines)}')

# Find the start of corrupted content (setup_eir_tab method)
corrupt_start = None
for i, line in enumerate(lines):
    if line.strip() == 'def setup_eir_tab(self):':
        corrupt_start = i
        break

# Find the _DocumentTypeTab class
doc_class_start = None
for i, line in enumerate(lines):
    if line.strip() == 'class _DocumentTypeTab:':
        doc_class_start = i
        break

print(f'Corrupt content starts at line {corrupt_start + 1}')
print(f'Document class starts at line {doc_class_start + 1}')

if corrupt_start is not None and doc_class_start is not None:
    # Remove corrupted content
    new_lines = lines[:corrupt_start] + lines[doc_class_start:]
    
    print(f'New line count: {len(new_lines)}')
    
    with open('phase1_enhanced_ui.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print('Corrupted content removed!')
else:
    print('Could not find boundaries')