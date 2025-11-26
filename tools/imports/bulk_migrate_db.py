"""
Bulk Migration Script for Database Functions

This script performs automated migration of simple database functions
from direct connection pattern to connection pooling pattern.

Usage:
    python tools/bulk_migrate_db.py
"""

import re
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate_simple_function(func_text):
    """
    Migrate a simple function from old pattern to new pattern.
    
    OLD PATTERN:
        with get_db_connection() as conn:        try:
            cursor = conn.cursor()
            # ... query ...
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
        finally:
    
    NEW PATTERN:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # ... query ...
        except Exception as e:
            logger.error(f"Error: {e}")
            return []
    """
    # Step 1: Remove "conn = connect_to_db()" line and if conn is None check
    func_text = re.sub(
        r'\s+conn = connect_to_db\([^)]*\)\s+if conn is None:\s+return [^\n]+\s+try:',
        '\n    try:\n        with get_db_connection() as conn:',
        func_text
    )
    
    # Step 2: If no None check, just replace connection line
    func_text = re.sub(
        r'\s+conn = connect_to_db\([^)]*\)\s+try:',
        '\n    try:\n        with get_db_connection() as conn:',
        func_text
    )
    
    # Step 3: Also handle case without try block
    func_text = re.sub(
        r'(\s+)conn = connect_to_db\(([^)]*)\)\n\s+cursor = conn\.cursor\(\)',
        r'\1try:\n\1    with get_db_connection(\2) as conn:\n\1        cursor = conn.cursor()',
        func_text
    )
    
    # Step 4: Remove finally:
    func_text = re.sub(
        r'\s+finally:\s+conn\.close\(\)',
        '',
        func_text
    )
    
    # Step 5: Replace print(f"❌... with logger.error(f"...
    func_text = re.sub(
        r'print\(f"❌ ([^"]+): {e}"\)',
        r'logger.error(f"\1: {e}")',
        func_text
    )
    func_text = re.sub(
        r'print\("❌ ([^"]+)"\)',
        r'logger.error("\1")',
        func_text
    )
    
    # Step 6: Add proper indentation for code inside with block
    lines = func_text.split('\n')
    result = []
    in_with_block = False
    with_indent = 0
    
    for i, line in enumerate(lines):
        if 'with get_db_connection() as conn:' in line:
            in_with_block = True
            with_indent = len(line) - len(line.lstrip())
            result.append(line)
        elif in_with_block and line.strip() and not line.strip().startswith('except'):
            # Add 4 spaces of indentation if inside with block
            if len(line) - len(line.lstrip()) == with_indent:
                result.append('    ' + line)
            else:
                result.append(line)
        elif 'except Exception as e:' in line:
            in_with_block = False
            result.append(line)
        else:
            result.append(line)
    
    return '\n'.join(result)

# List of simple functions to migrate
SIMPLE_FUNCTIONS = [
    'get_cycle_ids',
    'get_reference_options',
    'update_review_task_assignee',
    'get_projects_full',
    'delete_review_cycle',
    'update_bep_status',
    'delete_bookmark',
    'get_control_file',
    'set_control_file',
    'get_project_review_progress',
    'save_acc_folder_path',
]

def show_migration_template():
    """Show migration template for manual reference."""
    print("""
================================================================================
MIGRATION TEMPLATE - Copy this pattern for manual migrations
================================================================================

BEFORE (OLD PATTERN):
```python
def function_name(params):
    with get_db_connection() as conn:    try:
        cursor = conn.cursor()
        cursor.execute("SELECT ...")
        result = cursor.fetchall()
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return []
    finally:
```

AFTER (NEW PATTERN):
```python
def function_name(params):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
            result = cursor.fetchall()
            return result
    except Exception as e:
        logger.error(f"Error: {e}")
        return []
```

KEY CHANGES:
1. ✅ Replace `conn = connect_to_db()` with `with get_db_connection() as conn:`
2. ✅ Remove `if conn is None:` check (context manager handles this)
3. ✅ Remove `finally:` (context manager handles this)
4. ✅ Replace `print(f"❌...` with `logger.error(f"...`
5. ✅ Indent code inside `with` block by 4 spaces
6. ✅ Context manager automatically commits on success, rollsback on error

SPECIAL CASES:
- If function needs specific database: `with get_db_connection("DatabaseName") as conn:`
- If function has multiple operations: Keep all inside same `with` block for transaction
- If function updates data: `conn.commit()` still needed before returning

================================================================================
    """)

if __name__ == '__main__':
    if '--template' in sys.argv:
        show_migration_template()
    else:
        print("Run with --template to see migration pattern")
        print(f"\nFunctions ready for manual migration: {len(SIMPLE_FUNCTIONS)}")
        for func in SIMPLE_FUNCTIONS:
            print(f"  - {func}")
