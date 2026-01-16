"""
Expected Model Alias Management Service (Phase 1)

Manages the mapping between observed Revit files and expected models.
Works in tandem with ExpectedModels to provide never-empty quality register.

Key Concepts:
- Expected Models: Authoritative registry of intended deliverables
- Expected Model Aliases: Patterns to match observed files to expected models
- Alias Resolution: Deterministic matching with priority-based conflict resolution
"""

from database import (
    get_expected_models,
    create_expected_model,
    get_expected_model_aliases,
    create_expected_model_alias,
    match_observed_to_expected,
)
from constants import schema as S
from database_pool import get_db_connection
import logging
from typing import List, Dict, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class ExpectedModelAliasManager:
    """Manage expected model aliases and resolution logic"""
    
    def __init__(self):
        """Initialize manager"""
        pass
    
    def get_all_expected_models(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all expected models for a project"""
        return get_expected_models(project_id)
    
    def add_expected_model(
        self,
        project_id: int,
        expected_model_key: str,
        display_name: Optional[str] = None,
        discipline: Optional[str] = None,
        company_id: Optional[int] = None,
        is_required: bool = True
    ) -> Optional[int]:
        """Create a new expected model"""
        return create_expected_model(
            project_id=project_id,
            expected_model_key=expected_model_key,
            display_name=display_name,
            discipline=discipline,
            company_id=company_id,
            is_required=is_required
        )
    
    def get_all_aliases(
        self,
        project_id: int,
        expected_model_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get aliases for a project or expected model"""
        return get_expected_model_aliases(project_id, expected_model_id)
    
    def add_alias(
        self,
        expected_model_id: int,
        project_id: int,
        alias_pattern: str,
        match_type: str = 'exact',
        target_field: str = 'filename',
        is_active: bool = True
    ) -> Optional[int]:
        """Create a new alias"""
        return create_expected_model_alias(
            expected_model_id=expected_model_id,
            project_id=project_id,
            alias_pattern=alias_pattern,
            match_type=match_type,
            target_field=target_field,
            is_active=is_active
        )
    
    def resolve_observed_to_expected(
        self,
        observed_filename: str,
        observed_rvt_model_key: Optional[str],
        aliases: List[Dict[str, Any]]
    ) -> Optional[int]:
        """
        Match an observed file to an expected model using aliases.
        
        Returns expected_model_id if match found, None otherwise.
        """
        return match_observed_to_expected(
            observed_filename=observed_filename,
            observed_rvt_model_key=observed_rvt_model_key,
            aliases=aliases
        )
    
    def bulk_seed_expected_models_from_observed(
        self,
        project_id: int,
        observed_files: List[Dict[str, Any]]
    ) -> List[int]:
        """
        Auto-generate expected models from observed files.
        
        Used for initial seeding when no expected models exist yet.
        Creates one expected model per unique observed filename.
        
        Args:
            project_id: Project to seed
            observed_files: List of observed file dicts with 'filename', 'discipline'
        
        Returns:
            List of created expected_model_ids
        """
        created_ids = []
        seen_keys = set()
        
        try:
            for observed in observed_files:
                filename = observed.get('filename', '')
                discipline = observed.get('discipline')
                
                if not filename:
                    continue
                
                # Use filename as initial key (can be refined by user later)
                key = filename.split('.')[0] if '.' in filename else filename
                
                # Avoid duplicates within this batch
                if key in seen_keys:
                    continue
                
                seen_keys.add(key)
                
                # Create expected model
                expected_id = self.add_expected_model(
                    project_id=project_id,
                    expected_model_key=key,
                    display_name=key,
                    discipline=discipline,
                    is_required=True
                )
                
                if expected_id:
                    created_ids.append(expected_id)
                    
                    # Create initial alias (exact filename match)
                    self.add_alias(
                        expected_model_id=expected_id,
                        project_id=project_id,
                        alias_pattern=filename,
                        match_type='exact',
                        target_field='filename'
                    )
            
            logger.info(f"Seeded {len(created_ids)} expected models from {len(observed_files)} observed files")
            return created_ids
        
        except Exception as e:
            logger.error(f"Error seeding expected models: {e}", exc_info=True)
            return created_ids
    
    def get_unmapped_observed_count(
        self,
        project_id: int,
        observed_files: List[Dict[str, Any]],
        aliases: List[Dict[str, Any]]
    ) -> int:
        """
        Count observed files with no matching expected model.
        
        Args:
            project_id: Project context
            observed_files: All observed files from health data
            aliases: All aliases for the project
        
        Returns:
            Count of unmatched observed files
        """
        unmapped_count = 0
        
        for observed in observed_files:
            filename = observed.get('filename', '')
            rvt_key = observed.get('rvt_model_key')
            
            expected_id = self.resolve_observed_to_expected(
                observed_filename=filename,
                observed_rvt_model_key=rvt_key,
                aliases=aliases
            )
            
            if not expected_id:
                unmapped_count += 1
        
        return unmapped_count
    
    def validate_alias_pattern(self, pattern: str, match_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that an alias pattern is syntactically correct.
        
        Args:
            pattern: The pattern string
            match_type: The match type (exact, contains, regex)
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        import re
        
        if not pattern:
            return False, "Pattern cannot be empty"
        
        if match_type == 'regex':
            try:
                re.compile(pattern)
                return True, None
            except re.error as e:
                return False, f"Invalid regex: {str(e)}"
        
        # exact and contains patterns are always valid
        return True, None


def get_expected_model_alias_manager() -> ExpectedModelAliasManager:
    """Factory function to get manager instance"""
    return ExpectedModelAliasManager()
