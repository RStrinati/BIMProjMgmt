"""
Automated migration script for all remaining tools/* files.
Migrates from connect_to_db() to get_db_connection() context manager.
"""
import os
import re

def migrate_file(filepath):
    """Migrate a single file to use get_db_connection()."""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # 1. Update imports
    if 'from database import connect_to_db' in content:
        content = content.replace(
            'from database import connect_to_db',
            'from database_pool import get_db_connection'
        )
        changes_made.append("Updated import statement")
    
    # 2. Replace connection patterns
    # Pattern 1: conn = connect_to_db() or conn = connect_to_db('db_name')
    # Replace with: with get_db_connection() as conn: or with get_db_connection('db_name') as conn:
    
    # Find all connection assignments
    conn_pattern = r'(\s+)(conn|db_conn|db_connection|connection) = connect_to_db\((.*?)\)'
    matches = list(re.finditer(conn_pattern, content))
    
    if matches:
        print(f"  Found {len(matches)} connection(s) to migrate")
        
        # Process each match
        for match in matches:
            indent = match.group(1)
            var_name = match.group(2)
            db_arg = match.group(3)
            
            old_str = match.group(0)
            
            # Create new context manager
            if db_arg:
                new_str = f"{indent}with get_db_connection({db_arg}) as {var_name}:"
            else:
                new_str = f"{indent}with get_db_connection() as {var_name}:"
            
            content = content.replace(old_str, new_str, 1)
            changes_made.append(f"Migrated {var_name} = connect_to_db({db_arg})")
    
    # 3. Remove connection checks (if conn is None)
    check_patterns = [
        r'\s+if\s+(conn|db_conn|db_connection|connection)\s+is\s+None:\s*\n\s+.*return.*\n',
        r'\s+if\s+not\s+(conn|db_conn|db_connection|connection):\s*\n\s+.*return.*\n',
        r'\s+if\s+(conn|db_conn|db_connection|connection)\s*==\s*None:\s*\n\s+.*return.*\n',
    ]
    
    for pattern in check_patterns:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, '', content)
            changes_made.append(f"Removed {len(matches)} connection check(s)")
    
    # 4. Remove conn.close() calls
    close_pattern = r'\s+(conn|db_conn|db_connection|connection)\.close\(\)'
    matches = re.findall(close_pattern, content)
    if matches:
        content = re.sub(close_pattern, '', content)
        changes_made.append(f"Removed {len(matches)} .close() call(s)")
    
    # 5. Remove finally blocks that only close connections
    finally_pattern = r'\s+finally:\s*\n\s+(conn|db_conn|db_connection|connection)\.close\(\)'
    matches = re.findall(finally_pattern, content)
    if matches:
        content = re.sub(finally_pattern, '', content)
        changes_made.append(f"Removed {len(matches)} finally block(s)")
    
    # Only write if changes were made
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {os.path.basename(filepath)}")
        for change in changes_made:
            print(f"    - {change}")
        return True
    else:
        print(f"⏭️  {os.path.basename(filepath)} - No changes needed")
        return False

def main():
    """Migrate all tools/*.py files."""
    
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get all .py files in tools/
    py_files = [f for f in os.listdir(tools_dir) if f.endswith('.py') and f != 'migrate_all_tools.py']
    
    print("=" * 80)
    print("AUTOMATED TOOLS MIGRATION")
    print("=" * 80)
    print(f"\nFound {len(py_files)} Python files in tools/")
    print("\nStarting migration...\n")
    
    migrated = 0
    skipped = 0
    errors = 0
    
    for filename in sorted(py_files):
        filepath = os.path.join(tools_dir, filename)
        try:
            if migrate_file(filepath):
                migrated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"❌ {filename} - ERROR: {e}")
            errors += 1
    
    print("\n" + "=" * 80)
    print("MIGRATION SUMMARY")
    print("=" * 80)
    print(f"✅ Migrated: {migrated} files")
    print(f"⏭️  Skipped: {skipped} files")
    if errors > 0:
        print(f"❌ Errors: {errors} files")
    print("\nDone!")

if __name__ == '__main__':
    main()
