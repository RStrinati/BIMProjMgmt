"""
Naming Convention Service

Manages file naming conventions for different clients and validates
project files against client-specific naming standards.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

# Base path for naming convention JSON files
NAMING_CONVENTIONS_DIR = Path(__file__).parent.parent / "constants" / "naming_conventions"


class NamingConventionService:
    """Service for managing and applying client-specific naming conventions"""
    
    def __init__(self):
        self._conventions_cache = {}
    
    def get_convention_schema(self, convention_code: str) -> Optional[Dict]:
        """
        Load naming convention schema for a given convention code.
        
        Args:
            convention_code: Code for the naming convention (e.g., 'AWS', 'SINSW')
            
        Returns:
            Dictionary containing the naming convention schema, or None if not found
        """
        if not convention_code:
            logger.warning("No convention code provided")
            return None
            
        # Check cache first
        if convention_code in self._conventions_cache:
            return self._conventions_cache[convention_code]
        
        # Load from file
        convention_file = NAMING_CONVENTIONS_DIR / f"{convention_code}.json"
        
        if not convention_file.exists():
            logger.error(f"Naming convention file not found: {convention_file}")
            return None
        
        try:
            with open(convention_file, 'r') as f:
                schema = json.load(f)
                self._conventions_cache[convention_code] = schema
                logger.info(f"Loaded naming convention schema for {convention_code}")
                return schema
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in naming convention file {convention_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading naming convention {convention_code}: {e}")
            return None
    
    def get_available_conventions(self) -> List[Tuple[str, str]]:
        """
        Get list of available naming conventions.
        
        Returns:
            List of tuples (code, institution_name)
        """
        conventions = []
        
        if not NAMING_CONVENTIONS_DIR.exists():
            logger.warning(f"Naming conventions directory not found: {NAMING_CONVENTIONS_DIR}")
            return conventions
        
        for file in NAMING_CONVENTIONS_DIR.glob("*.json"):
            try:
                with open(file, 'r') as f:
                    schema = json.load(f)
                    code = file.stem  # Filename without extension
                    institution = schema.get('institution', code)
                    conventions.append((code, institution))
            except Exception as e:
                logger.error(f"Error reading convention file {file}: {e}")
                continue
        
        return sorted(conventions)
    
    def get_convention_path(self, convention_code: str) -> Optional[str]:
        """
        Get the full file path for a naming convention schema.
        
        Args:
            convention_code: Code for the naming convention
            
        Returns:
            Full path to the JSON schema file, or None if not found
        """
        if not convention_code:
            return None
            
        convention_file = NAMING_CONVENTIONS_DIR / f"{convention_code}.json"
        
        if convention_file.exists():
            return str(convention_file)
        
        return None
    
    def validate_convention_exists(self, convention_code: str) -> bool:
        """
        Check if a naming convention exists.
        
        Args:
            convention_code: Code for the naming convention
            
        Returns:
            True if the convention exists, False otherwise
        """
        if not convention_code:
            return False
            
        convention_file = NAMING_CONVENTIONS_DIR / f"{convention_code}.json"
        return convention_file.exists()
    
    def get_convention_summary(self, convention_code: str) -> Optional[Dict]:
        """
        Get a summary of a naming convention (metadata only).
        
        Args:
            convention_code: Code for the naming convention
            
        Returns:
            Dictionary with convention metadata
        """
        schema = self.get_convention_schema(convention_code)
        
        if not schema:
            return None
        
        return {
            'code': convention_code,
            'institution': schema.get('institution', 'Unknown'),
            'standard': schema.get('standard', 'Unknown'),
            'delimiter': schema.get('delimiter', '-'),
            'field_count': len(schema.get('fields', [])),
            'regex_pattern': schema.get('regex_pattern', '')
        }


# Global service instance
naming_convention_service = NamingConventionService()


# Convenience functions
def get_convention_schema(convention_code: str) -> Optional[Dict]:
    """Get naming convention schema by code"""
    return naming_convention_service.get_convention_schema(convention_code)


def get_available_conventions() -> List[Tuple[str, str]]:
    """Get list of available naming conventions"""
    return naming_convention_service.get_available_conventions()


def get_convention_path(convention_code: str) -> Optional[str]:
    """Get file path for naming convention schema"""
    return naming_convention_service.get_convention_path(convention_code)


def validate_convention_exists(convention_code: str) -> bool:
    """Check if naming convention exists"""
    return naming_convention_service.validate_convention_exists(convention_code)


def get_convention_summary(convention_code: str) -> Optional[Dict]:
    """Get summary of naming convention"""
    return naming_convention_service.get_convention_summary(convention_code)
