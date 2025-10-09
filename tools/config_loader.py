"""
Configuration loader with environment variable override support.
Follows the project's schema constants pattern.

This module provides secure configuration loading for the BIM Project Management system,
preventing credential exposure in version control.

Usage:
    from tools.config_loader import load_config, get_connection_string
    
    config = load_config()
    conn_string = get_connection_string('ProjectManagement')
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def load_config() -> Dict[str, Any]:
    """
    Load configuration from appsettings.json with environment variable overrides.
    
    Priority (highest to lowest):
    1. Environment variables
    2. appsettings.json file
    3. appsettings.template.json (fallback)
    4. Default values
    
    Returns:
        Dict containing configuration settings
        
    Raises:
        ConfigurationError: If required configuration is missing
    """
    config_path = Path(__file__).parent / 'appsettings.json'
    template_path = Path(__file__).parent / 'appsettings.template.json'
    
    # Load from file if exists
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info("Loaded configuration from appsettings.json")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in appsettings.json: {e}")
    elif template_path.exists():
        logger.warning("appsettings.json not found, using template values")
        with open(template_path, 'r') as f:
            config = json.load(f)
    else:
        logger.warning("No configuration file found, using defaults")
        config = _get_default_config()
    
    # Override with environment variables (HIGHEST PRIORITY)
    config = _apply_env_overrides(config)
    
    # Validate required settings
    _validate_config(config)
    
    return config


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to configuration."""
    
    # Revizto API Settings
    if 'ReviztoAPI' not in config:
        config['ReviztoAPI'] = {}
    
    config['ReviztoAPI']['BaseUrl'] = os.getenv(
        'REVIZTO_BASE_URL',
        config.get('ReviztoAPI', {}).get('BaseUrl', 'https://api.sydney.revizto.com')
    )
    config['ReviztoAPI']['Region'] = os.getenv(
        'REVIZTO_REGION',
        config.get('ReviztoAPI', {}).get('Region', 'sydney')
    )
    config['ReviztoAPI']['AccessToken'] = os.getenv(
        'REVIZTO_ACCESS_TOKEN',
        config.get('ReviztoAPI', {}).get('AccessToken')
    )
    config['ReviztoAPI']['RefreshToken'] = os.getenv(
        'REVIZTO_REFRESH_TOKEN',
        config.get('ReviztoAPI', {}).get('RefreshToken')
    )
    
    # Database Settings
    if 'Database' not in config:
        config['Database'] = {}
    
    config['Database']['ConnectionString'] = os.getenv(
        'DB_CONNECTION_STRING',
        config.get('Database', {}).get('ConnectionString')
    )
    
    # Export Settings
    if 'ExportSettings' not in config:
        config['ExportSettings'] = {}
    
    config['ExportSettings']['OutputDirectory'] = os.getenv(
        'EXPORT_OUTPUT_DIR',
        config.get('ExportSettings', {}).get('OutputDirectory', './Exports')
    )
    config['ExportSettings']['LogDirectory'] = os.getenv(
        'EXPORT_LOG_DIR',
        config.get('ExportSettings', {}).get('LogDirectory', './Logs')
    )
    
    # Logging Settings
    if 'Logging' not in config:
        config['Logging'] = {'LogLevel': {}}
    
    log_level = os.getenv('LOG_LEVEL', 
                         config.get('Logging', {}).get('LogLevel', {}).get('Default', 'Information'))
    config['Logging']['LogLevel']['Default'] = log_level
    
    return config


def _get_default_config() -> Dict[str, Any]:
    """Return default configuration values."""
    return {
        'ReviztoAPI': {
            'BaseUrl': 'https://api.sydney.revizto.com',
            'Region': 'sydney',
            'AccessToken': None,
            'RefreshToken': None,
            'TokenUpdatedAt': datetime.utcnow().isoformat()
        },
        'Database': {
            'ConnectionString': None
        },
        'ExportSettings': {
            'OutputDirectory': './Exports',
            'LogDirectory': './Logs'
        },
        'Logging': {
            'LogLevel': {
                'Default': 'Information',
                'Microsoft': 'Warning'
            }
        }
    }


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate that required configuration is present.
    
    Raises:
        ConfigurationError: If required configuration is missing or contains placeholder values
    """
    # Check for placeholder values that indicate template usage
    placeholders = [
        'YOUR_REVIZTO_ACCESS_TOKEN_HERE',
        'YOUR_REVIZTO_REFRESH_TOKEN_HERE',
        'YOUR_SERVER',
        'YOUR_DATABASE',
        'YOUR_',
        'Path\\To\\Your'
    ]
    
    config_str = json.dumps(config)
    for placeholder in placeholders:
        if placeholder in config_str:
            raise ConfigurationError(
                f"Configuration contains placeholder value '{placeholder}'. "
                f"Please copy appsettings.template.json to appsettings.json and configure with actual values."
            )
    
    # Validate critical fields
    if not config.get('ReviztoAPI', {}).get('AccessToken'):
        logger.warning("Revizto AccessToken is not configured")
    
    if not config.get('Database', {}).get('ConnectionString'):
        logger.warning("Database ConnectionString is not configured")
    
    logger.info("Configuration validation passed")


def get_connection_string() -> str:
    """
    Get database connection string.
    
    Returns:
        Connection string
        
    Raises:
        ConfigurationError: If connection string is not configured
    """
    config = load_config()
    
    conn_string = config.get('Database', {}).get('ConnectionString')
    if not conn_string:
        raise ConfigurationError("Database connection string is not configured")
    
    return conn_string


def get_revizto_config() -> Dict[str, Any]:
    """
    Get Revizto API configuration.
    
    Returns:
        Dictionary with Revizto API settings
        
    Raises:
        ConfigurationError: If Revizto configuration is incomplete
    """
    config = load_config()
    
    revizto_config = config.get('ReviztoAPI', {})
    if not revizto_config.get('AccessToken'):
        raise ConfigurationError("Revizto AccessToken is not configured")
    
    return revizto_config


def get_export_settings() -> Dict[str, str]:
    """
    Get export directory settings.
    
    Returns:
        Dictionary with output and log directories
    """
    config = load_config()
    return config.get('ExportSettings', {
        'OutputDirectory': './Exports',
        'LogDirectory': './Logs'
    })


def update_revizto_tokens(access_token: str, refresh_token: str) -> None:
    """
    Update Revizto tokens in the configuration file.
    
    Args:
        access_token: New access token
        refresh_token: New refresh token
        
    Note:
        This updates the appsettings.json file directly. Use with caution.
    """
    config_path = Path(__file__).parent / 'appsettings.json'
    
    if not config_path.exists():
        raise ConfigurationError("appsettings.json not found. Cannot update tokens.")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    if 'ReviztoAPI' not in config:
        config['ReviztoAPI'] = {}
    
    config['ReviztoAPI']['AccessToken'] = access_token
    config['ReviztoAPI']['RefreshToken'] = refresh_token
    config['ReviztoAPI']['TokenUpdatedAt'] = datetime.utcnow().isoformat() + '+00:00'
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info("Successfully updated Revizto tokens in appsettings.json")


if __name__ == "__main__":
    # Test configuration loading
    print("\n=== Configuration Loader Test ===\n")
    
    try:
        config = load_config()
        print("✅ Configuration loaded successfully")
        print(f"\nRevizto API:")
        print(f"  Base URL: {config['ReviztoAPI']['BaseUrl']}")
        print(f"  Region: {config['ReviztoAPI']['Region']}")
        print(f"  Access Token: {'***configured***' if config['ReviztoAPI'].get('AccessToken') else 'NOT SET'}")
        print(f"  Refresh Token: {'***configured***' if config['ReviztoAPI'].get('RefreshToken') else 'NOT SET'}")
        
        print(f"\nDatabase:")
        print(f"  Connection String: {'***configured***' if config['Database'].get('ConnectionString') else 'NOT SET'}")
        
        print(f"\nExport Settings:")
        print(f"  Output Directory: {config['ExportSettings']['OutputDirectory']}")
        print(f"  Log Directory: {config['ExportSettings']['LogDirectory']}")
        
        print(f"\nLogging:")
        print(f"  Log Level: {config['Logging']['LogLevel']['Default']}")
        
    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        print("\nTo fix this:")
        print("1. Copy tools/appsettings.template.json to tools/appsettings.json")
        print("2. Edit appsettings.json with your actual credentials")
        print("3. Run this test again")
