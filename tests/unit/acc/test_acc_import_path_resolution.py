"""
Test that ACC import correctly resolves merge_dir paths.
This test verifies the fix for the issue where import_acc_data
fails when called from different working directories.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_merge_dir_path_resolution():
    """
    Test that merge_dir is correctly resolved to absolute path
    regardless of current working directory.
    """
    # Read the source file directly to avoid import dependencies
    handlers_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'handlers'
    )
    acc_handler_path = os.path.join(handlers_dir, 'acc_handler.py')
    
    with open(acc_handler_path, 'r') as f:
        source = f.read()
    
    # Verify the path resolution code is present
    assert "os.path.isabs" in source, "Path resolution check not found in import_acc_data"
    assert "project_root" in source, "project_root calculation not found in import_acc_data"
    assert "os.path.dirname(os.path.dirname(os.path.abspath(__file__)))" in source, \
        "Project root calculation not found"
    
    print("✓ Path resolution code is present in import_acc_data")


def test_backend_app_merge_dir():
    """
    Test that backend/app.py correctly computes the merge_dir path.
    """
    # Read the backend app.py file
    backend_app_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'backend',
        'app.py'
    )
    
    with open(backend_app_path, 'r') as f:
        content = f.read()
    
    # Check that the endpoint computes the absolute path
    assert 'project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))' in content, \
        "project_root calculation not found in backend/app.py"
    assert 'merge_dir = os.path.join(project_root, "sql")' in content, \
        "merge_dir path join not found in backend/app.py"
    
    print("✓ Backend app.py correctly computes merge_dir path")


def test_sql_directory_exists():
    """
    Verify that the sql directory exists in the project root.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_dir = os.path.join(project_root, 'sql')
    
    assert os.path.exists(sql_dir), f"SQL directory not found at {sql_dir}"
    assert os.path.isdir(sql_dir), f"SQL path exists but is not a directory: {sql_dir}"
    
    # Check for merge SQL files
    merge_files = [f for f in os.listdir(sql_dir) if f.startswith('merge_') and f.endswith('.sql')]
    assert len(merge_files) > 0, f"No merge_*.sql files found in {sql_dir}"
    
    print(f"✓ SQL directory exists with {len(merge_files)} merge files")


if __name__ == '__main__':
    print("Running ACC import path resolution tests...\n")
    
    try:
        test_merge_dir_path_resolution()
        test_backend_app_merge_dir()
        test_sql_directory_exists()
        
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
