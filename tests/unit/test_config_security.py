"""
Test configuration validation and security requirements.

This test ensures that:
1. Config validation works properly when credentials are missing
2. Config loads successfully when credentials are present
3. No hardcoded credentials remain in the codebase
"""

import os
import sys
import pytest
import importlib

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConfigSecurity:
    """Test configuration security requirements."""
    
    def test_config_requires_credentials_without_env_vars(self):
        """Test that config validation fails when DB_USER and DB_PASSWORD are not set."""
        # Save original env vars
        original_user = os.environ.get("DB_USER")
        original_password = os.environ.get("DB_PASSWORD")
        
        try:
            # Remove credentials from environment
            if "DB_USER" in os.environ:
                del os.environ["DB_USER"]
            if "DB_PASSWORD" in os.environ:
                del os.environ["DB_PASSWORD"]
            
            # Force reload config module
            if "config" in sys.modules:
                del sys.modules["config"]
            
            # Importing config should raise ValueError due to missing credentials
            with pytest.raises(ValueError) as exc_info:
                import config
            
            # Check that error message mentions the missing variables
            error_msg = str(exc_info.value)
            assert "Missing required environment variables" in error_msg
            assert "DB_USER" in error_msg or "DB_PASSWORD" in error_msg
            assert ".env.example" in error_msg  # Should reference the example file
            
        finally:
            # Restore original env vars
            if original_user is not None:
                os.environ["DB_USER"] = original_user
            if original_password is not None:
                os.environ["DB_PASSWORD"] = original_password
            
            # Clean up module
            if "config" in sys.modules:
                del sys.modules["config"]
    
    def test_config_loads_with_credentials(self):
        """Test that config loads successfully when credentials are provided."""
        # Set test credentials
        os.environ["DB_USER"] = "test_user"
        os.environ["DB_PASSWORD"] = "test_password"
        
        try:
            # Force reload config module
            if "config" in sys.modules:
                del sys.modules["config"]
            
            # Import should succeed
            import config
            
            # Verify Config class has the credentials
            assert config.Config.DB_USER == "test_user"
            assert config.Config.DB_PASSWORD == "test_password"
            
            # Verify no default hardcoded values
            assert config.Config.DB_USER != "admin02"
            assert config.Config.DB_PASSWORD != "1234"
            
        finally:
            # Clean up
            if "config" in sys.modules:
                del sys.modules["config"]
    
    def test_no_hardcoded_credentials_in_config(self):
        """Test that config.py doesn't contain hardcoded credentials."""
        # Navigate up from tests/unit to project root
        tests_dir = os.path.dirname(__file__)
        if os.path.basename(tests_dir) == "unit":
            project_root = os.path.dirname(os.path.dirname(tests_dir))
        else:
            project_root = os.path.dirname(tests_dir)
        
        config_path = os.path.join(project_root, "config.py")
        
        with open(config_path, "r") as f:
            config_content = f.read()
        
        # Check for hardcoded credentials
        forbidden_patterns = [
            '"admin02"',
            "'admin02'",
            '"1234"',
            "'1234'",
            'os.getenv("DB_USER", "admin02")',
            'os.getenv("DB_PASSWORD", "1234")',
        ]
        
        for pattern in forbidden_patterns:
            assert pattern not in config_content, (
                f"Found hardcoded credential pattern '{pattern}' in config.py"
            )
    
    def test_env_example_files_exist(self):
        """Test that .env.example template files exist."""
        # Navigate up from tests/unit to project root
        tests_dir = os.path.dirname(__file__)
        if os.path.basename(tests_dir) == "unit":
            project_root = os.path.dirname(os.path.dirname(tests_dir))
        else:
            project_root = os.path.dirname(tests_dir)
        
        # Check root .env.example
        root_example = os.path.join(project_root, ".env.example")
        assert os.path.exists(root_example), ".env.example not found in project root"
        
        # Check tools/.env.example
        tools_example = os.path.join(project_root, "tools", ".env.example")
        assert os.path.exists(tools_example), "tools/.env.example not found"
        
        # Verify they contain placeholder values, not real credentials
        with open(root_example, "r") as f:
            content = f.read()
            assert "your_username_here" in content or "your_server_here" in content
            assert "your_secure_password_here" in content or "your_password_here" in content
            # Should NOT contain actual credentials
            assert "admin02" not in content
            assert content.count("1234") == 0 or "your_secure_password_here" in content  # 1234 might be in a port
    
    def test_sensitive_env_file_not_in_git(self):
        """Test that tools/.env has been removed from git."""
        # Navigate up from tests/unit to project root
        tests_dir = os.path.dirname(__file__)
        if os.path.basename(tests_dir) == "unit":
            project_root = os.path.dirname(os.path.dirname(tests_dir))
        else:
            project_root = os.path.dirname(tests_dir)
        
        tools_env = os.path.join(project_root, "tools", ".env")
        
        # Check if file is tracked by git
        try:
            import subprocess
            result = subprocess.run(
                ["git", "ls-files", "--error-unmatch", tools_env],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            # If exit code is 0, file is tracked (which is bad)
            if result.returncode == 0:
                pytest.fail("tools/.env is still tracked by git - it should be removed")
        except FileNotFoundError:
            # git not available, skip this check
            pytest.skip("git not available for testing")
    
    def test_config_validation_function_exists(self):
        """Test that validation function exists and is called."""
        # Navigate up from tests/unit to project root
        tests_dir = os.path.dirname(__file__)
        if os.path.basename(tests_dir) == "unit":
            project_root = os.path.dirname(os.path.dirname(tests_dir))
        else:
            project_root = os.path.dirname(tests_dir)
        
        config_path = os.path.join(project_root, "config.py")
        
        with open(config_path, "r") as f:
            config_content = f.read()
        
        # Check that validation function exists
        assert "def _validate_required_config():" in config_content, (
            "_validate_required_config() function not found in config.py"
        )
        
        # Check that validation is called
        assert "_validate_required_config()" in config_content, (
            "_validate_required_config() is not being called in config.py"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
