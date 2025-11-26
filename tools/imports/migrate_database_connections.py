"""
Automated Database Connection Pool Migration Script

This script helps migrate database.py functions from direct connection pattern
to connection pooling pattern.

Usage:
    python tools/migrate_database_connections.py --dry-run
    python tools/migrate_database_connections.py --apply
"""

import re
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_database_file():
    """Analyze database.py to find all functions needing migration."""
    with open('database.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find function definitions with direct connection pattern
    pattern = r'def (\w+)\([^)]*\):.*?(?=\ndef |\nclass |\Z)'
    matches = re.finditer(pattern, content, re.DOTALL)
    
    functions_to_migrate = []
    functions_already_migrated = []
    
    for match in matches:
        func_name = match.group(1)
        func_body = match.group(0)
        
        # Check if uses old pattern
        if 'conn = connect_to_db()' in func_body:
            functions_to_migrate.append({
                'name': func_name,
                'has_if_conn_none': 'if conn is None:' in func_body,
                'has_finally_close': 'conn.close()' in func_body,
                'has_print_error': 'print(f"❌' in func_body or 'print("❌' in func_body,
                'line_count': len(func_body.split('\n'))
            })
        elif 'with get_db_connection()' in func_body:
            functions_already_migrated.append(func_name)
    
    return functions_to_migrate, functions_already_migrated

def generate_migration_report():
    """Generate a report of migration status."""
    to_migrate, migrated = analyze_database_file()
    
    print("=" * 80)
    print("DATABASE.PY CONNECTION POOL MIGRATION STATUS")
    print("=" * 80)
    print(f"\n✅ Functions Already Migrated: {len(migrated)}")
    for func in migrated:
        print(f"   - {func}")
    
    print(f"\n❌ Functions Still Need Migration: {len(to_migrate)}")
    
    # Group by complexity
    simple = [f for f in to_migrate if f['line_count'] < 30]
    medium = [f for f in to_migrate if 30 <= f['line_count'] < 60]
    complex_funcs = [f for f in to_migrate if f['line_count'] >= 60]
    
    print(f"\n   Simple Functions ({len(simple)}):")
    for func in simple[:10]:  # Show first 10
        print(f"   - {func['name']} ({func['line_count']} lines)")
    if len(simple) > 10:
        print(f"   ... and {len(simple) - 10} more")
    
    print(f"\n   Medium Functions ({len(medium)}):")
    for func in medium[:10]:
        print(f"   - {func['name']} ({func['line_count']} lines)")
    if len(medium) > 10:
        print(f"   ... and {len(medium) - 10} more")
    
    print(f"\n   Complex Functions ({len(complex_funcs)}):")
    for func in complex_funcs:
        print(f"   - {func['name']} ({func['line_count']} lines)")
    
    print(f"\n" + "=" * 80)
    print(f"SUMMARY:")
    print(f"  Total Functions: {len(to_migrate) + len(migrated)}")
    print(f"  Migrated: {len(migrated)} ({len(migrated)/(len(to_migrate)+len(migrated))*100:.1f}%)")
    print(f"  Remaining: {len(to_migrate)} ({len(to_migrate)/(len(to_migrate)+len(migrated))*100:.1f}%)")
    print("=" * 80)
    
    return to_migrate, migrated

def generate_migration_batch():
    """Generate list of next 10 functions to migrate."""
    to_migrate, _ = analyze_database_file()
    
    # Sort by complexity (simple first)
    to_migrate.sort(key=lambda x: x['line_count'])
    
    print("\n" + "=" * 80)
    print("NEXT BATCH TO MIGRATE (10 simplest functions):")
    print("=" * 80)
    
    for i, func in enumerate(to_migrate[:10], 1):
        print(f"\n{i}. {func['name']}")
        print(f"   Lines: {func['line_count']}")
        print(f"   Has null check: {func['has_if_conn_none']}")
        print(f"   Has finally: {func['has_finally_close']}")
        print(f"   Has print errors: {func['has_print_error']}")
    
    print("\n" + "=" * 80)
    print("Migration Pattern:")
    print("=" * 80)
    print("""
OLD PATTERN:
    with get_db_connection() as conn:    try:
        cursor = conn.cursor()
        # ... query ...
        conn.commit()
    except Exception as e:
        print(f"❌ Error: {e}")
        return []
    finally:

NEW PATTERN:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # ... query ...
            conn.commit()
            return result
    except Exception as e:
        logger.error(f"Error: {e}")
        return []
    """)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--batch':
        generate_migration_batch()
    else:
        generate_migration_report()
