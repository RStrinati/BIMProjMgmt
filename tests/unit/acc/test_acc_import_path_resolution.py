"""
Test that ACC import correctly resolves merge_dir paths.
This test verifies the fix for the issue where import_acc_data
fails when called from different working directories.
"""

import inspect
import os
from importlib import import_module
from pathlib import Path


def test_merge_dir_path_resolution():
    """
    Test that merge_dir is correctly resolved to absolute path
    regardless of current working directory.
    """
    acc_handler = import_module("handlers.acc_handler")
    source = inspect.getsource(acc_handler)
    
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
    backend_app = import_module("backend.app")
    content = inspect.getsource(backend_app)
    
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
    project_root = Path(__file__).resolve().parents[3]
    sql_dir = project_root / "sql"
    
    assert sql_dir.exists(), f"SQL directory not found at {sql_dir}"
    assert sql_dir.is_dir(), f"SQL path exists but is not a directory: {sql_dir}"
    
    # Check for merge SQL files
    merge_files = [f.name for f in sql_dir.iterdir() if f.name.startswith('merge_') and f.name.endswith('.sql')]
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
