with open('phase1_enhanced_ui.py', 'r') as f:
    content = f.read()

print(f'File length: {len(content)}')

# Find the positions of the two ProjectSetupTab classes
first_pos = content.find('class ProjectSetupTab:')
second_pos = content.find('class ProjectSetupTab:', first_pos + 1)

print(f'First class at: {first_pos}')
print(f'Second class at: {second_pos}')

if first_pos != -1 and second_pos != -1:
    # Find the end of the second class (next class definition after second_pos)
    next_class_pos = content.find('\nclass ', second_pos + 1)
    if next_class_pos == -1:
        next_class_pos = len(content)

    print(f'Next class at: {next_class_pos}')
    print(f'Removing from {second_pos} to {next_class_pos}')

    # Show what we're removing
    removed_content = content[second_pos:next_class_pos]
    print(f'Removing {len(removed_content)} characters')
    print('First 200 chars of removed content:')
    print(repr(removed_content[:200]))

    # Remove the duplicate class (from second_pos to next_class_pos)
    new_content = content[:second_pos] + content[next_class_pos:]

    print(f'New content length: {len(new_content)}')

    with open('phase1_enhanced_ui.py', 'w') as f:
        f.write(new_content)

    print('Duplicate class removed!')
else:
    print('Could not find duplicate classes')