"""
Revit Naming Convention Validator
Automatically validates file naming conventions when new health checks are imported

Author: System
Created: 2025-10-16
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from config import Config
from services.naming_convention_service import naming_convention_service
from constants import schema as S
from typing import Dict, List, Tuple, Optional
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RevitNamingValidator:
    """Validates Revit file naming conventions and updates database"""
    
    # Naming convention patterns
    NAMING_PATTERNS = {
        'standard': re.compile(r'^([A-Z]{2,4})[-_](\d{4,6})[-_]([A-Z]{2,3})[-_](.+)\.rvt$', re.IGNORECASE),
        'client_project': re.compile(r'^([A-Z\s]+)[-_]([A-Z0-9]+)[-_](.+)\.rvt$', re.IGNORECASE),
        'discipline_based': re.compile(r'^([A-Z]{3})[-_](.+)\.rvt$', re.IGNORECASE),
        'simple': re.compile(r'^(.+)\.rvt$', re.IGNORECASE)
    }
    
    DISCIPLINE_CODES = {
        'ARC': 'Architecture',
        'STR': 'Structural', 
        'MEP': 'MEP',
        'MEC': 'Mechanical',
        'ELE': 'Electrical',
        'PLU': 'Plumbing',
        'FPS': 'Fire Protection',
        'CIV': 'Civil',
        'LAN': 'Landscape',
        'INT': 'Interior',
        'URB': 'Urban Design'
    }
    
    def __init__(self):
        self.db_name = Config.REVIT_HEALTH_DB
        self._project_convention_cache: Dict[int, Optional[str]] = {}
    
    def _get_project_convention_code(self, project_id: Optional[int]) -> Optional[str]:
        if project_id is None:
            return None
        if project_id in self._project_convention_cache:
            return self._project_convention_cache[project_id]
        try:
            with get_db_connection(Config.PROJECT_MGMT_DB) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        """
                        SELECT naming_convention
                        FROM ProjectManagement.dbo.vw_projects_full
                        WHERE project_id = ?
                        """,
                        (project_id,),
                    )
                except Exception:
                    cursor.execute(
                        """
                        SELECT naming_convention
                        FROM ProjectManagement.dbo.projects
                        WHERE project_id = ?
                        """,
                        (project_id,),
                    )
                row = cursor.fetchone()
                code = row[0] if row and row[0] else None
                self._project_convention_cache[project_id] = code
                return code
        except Exception as exc:
            logger.warning("Failed to resolve naming convention for project %s: %s", project_id, exc)
            self._project_convention_cache[project_id] = None
            return None

    def _validate_against_schema(self, file_name: str, schema: Dict) -> Tuple[str, str, Optional[str], Optional[str]]:
        base_name = os.path.basename(file_name or "")
        base_no_ext, _ = os.path.splitext(base_name)
        regex_pattern = schema.get("regex_pattern")
        delimiter = schema.get("delimiter", "-")

        if regex_pattern:
            if not re.match(regex_pattern, base_no_ext):
                return "Invalid", f"Does not match naming convention {schema.get('institution', 'schema')}", None, None

        discipline_code = None
        discipline_name = None
        fields = schema.get("fields", [])
        discipline_field = next(
            (f for f in fields if "discipline" in str(f.get("name", "")).lower()),
            None,
        )
        if discipline_field:
            position = discipline_field.get("position")
            if isinstance(position, int):
                parts = base_no_ext.split(delimiter)
                if position < len(parts):
                    discipline_code = parts[position].strip()
                    mapped_values = discipline_field.get("mapped_values") or {}
                    discipline_name = mapped_values.get(discipline_code)
                    allowed_values = discipline_field.get("allowed_values")
                    if allowed_values and discipline_code not in allowed_values:
                        return (
                            "Warning",
                            f"Discipline code {discipline_code} not in allowed values",
                            discipline_code,
                            discipline_name,
                        )
                    if discipline_code and not discipline_name and mapped_values:
                        return (
                            "Warning",
                            f"Unknown discipline code: {discipline_code}",
                            discipline_code,
                            None,
                        )

        return "Valid", f"Naming convention {schema.get('institution', 'schema')}", discipline_code, discipline_name

    def validate_file_naming(
        self,
        file_name: str,
        naming_convention_code: Optional[str] = None,
    ) -> Tuple[str, str, Optional[str], Optional[str]]:
        """
        Validate file naming convention
        
        Args:
            file_name: Revit file name to validate
            
        Returns:
            Tuple of (validation_status, validation_reason, discipline_code, discipline_name)
        """
        if not file_name:
            return 'Invalid', 'Empty file name', None, None

        if naming_convention_code:
            schema = naming_convention_service.get_convention_schema(naming_convention_code)
            if schema:
                return self._validate_against_schema(file_name, schema)
        
        # Remove path if present
        base_name = os.path.basename(file_name)
        
        # Try standard pattern first: CLIENT-PROJECT-DISCIPLINE-DESCRIPTION.rvt
        match = self.NAMING_PATTERNS['standard'].match(base_name)
        if match:
            client_code = match.group(1).upper()
            project_code = match.group(2)
            discipline_code = match.group(3).upper()
            description = match.group(4)
            
            # Validate discipline code
            discipline_name = self.DISCIPLINE_CODES.get(discipline_code)
            
            if discipline_name:
                return 'Valid', 'Standard naming convention', discipline_code, discipline_name
            else:
                return 'Warning', f'Unknown discipline code: {discipline_code}', discipline_code, None
        
        # Try client-project pattern
        match = self.NAMING_PATTERNS['client_project'].match(base_name)
        if match:
            return 'Valid', 'Client-project naming convention', None, None
        
        # Try discipline-based pattern
        match = self.NAMING_PATTERNS['discipline_based'].match(base_name)
        if match:
            discipline_code = match.group(1).upper()
            discipline_name = self.DISCIPLINE_CODES.get(discipline_code)
            
            if discipline_name:
                return 'Valid', 'Discipline-based naming', discipline_code, discipline_name
            else:
                return 'Warning', f'Unknown discipline code: {discipline_code}', discipline_code, None
        
        # Fallback to simple validation
        if base_name.lower().endswith('.rvt'):
            return 'Warning', 'Non-standard naming convention', None, None
        
        return 'Invalid', 'Does not follow any recognized naming pattern', None, None
    
    def validate_new_health_check(self, health_check_id: int) -> bool:
        """
        Validate naming for a newly imported health check record
        
        Args:
            health_check_id: Health check record ID
            
        Returns:
            Success status
        """
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Get file name
                cursor.execute("""
                    SELECT strRvtFileName, pm_project_id
                    FROM dbo.tblRvtProjHealth
                    WHERE nId = ?
                """, (health_check_id,))
                
                row = cursor.fetchone()
                if not row:
                    logger.error(f"❌ Health check {health_check_id} not found")
                    return False
                
                file_name = row[0]
                project_id = row[1]
                convention_code = self._get_project_convention_code(project_id)

                # Validate naming
                status, reason, disc_code, disc_name = self.validate_file_naming(
                    file_name,
                    naming_convention_code=convention_code,
                )
                
                # Update record
                cursor.execute("""
                    UPDATE dbo.tblRvtProjHealth
                    SET 
                        validation_status = ?,
                        validation_reason = ?,
                        discipline_code = ?,
                        discipline_full_name = ?
                    WHERE nId = ?
                """, (status, reason, disc_code, disc_name, health_check_id))
                
                conn.commit()
                
                logger.info(f"✅ Validated {file_name}: {status} - {reason}")
                return True
                
        except Exception as e:
            logger.exception(f"❌ Error validating health check {health_check_id}")
            return False
    
    def validate_all_unvalidated(self) -> int:
        """
        Validate all health check records without validation status
        
        Returns:
            Number of records validated
        """
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Get unvalidated records
                cursor.execute("""
                    SELECT nId, strRvtFileName, pm_project_id
                    FROM dbo.tblRvtProjHealth
                    WHERE validation_status IS NULL
                      AND nDeletedOn IS NULL
                """)

                records = cursor.fetchall()
                validated_count = 0

                for record_id, file_name, project_id in records:
                    convention_code = self._get_project_convention_code(project_id)
                    status, reason, disc_code, disc_name = self.validate_file_naming(
                        file_name,
                        naming_convention_code=convention_code,
                    )
                    
                    cursor.execute("""
                        UPDATE dbo.tblRvtProjHealth
                        SET 
                            validation_status = ?,
                            validation_reason = ?,
                            discipline_code = ?,
                            discipline_full_name = ?
                        WHERE nId = ?
                    """, (status, reason, disc_code, disc_name, record_id))
                    
                    validated_count += 1
                
                conn.commit()
                logger.info(f"✅ Validated {validated_count} records")
                return validated_count
                
        except Exception as e:
            logger.exception("❌ Error in batch validation")
            return 0
    
    def get_validation_summary(self) -> Dict:
        """Get summary of naming validation results"""
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        validation_status,
                        COUNT(*) as count,
                        COUNT(DISTINCT discipline_code) as unique_disciplines
                    FROM dbo.tblRvtProjHealth
                    WHERE nDeletedOn IS NULL
                    GROUP BY validation_status
                """)
                
                summary = {}
                for row in cursor.fetchall():
                    summary[row[0] or 'Unvalidated'] = {
                        'count': row[1],
                        'unique_disciplines': row[2]
                    }
                
                return summary
                
        except Exception as e:
            logger.exception("❌ Error getting validation summary")
            return {}
    
    def get_invalid_files(self, limit: int = 50) -> List[Dict]:
        """Get files with invalid naming conventions"""
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"""
                    SELECT TOP {limit}
                        nId,
                        strRvtFileName,
                        validation_status,
                        validation_reason,
                        strProjectName,
                        ConvertedExportedDate
                    FROM dbo.tblRvtProjHealth
                    WHERE validation_status IN ('Invalid', 'Warning')
                      AND nDeletedOn IS NULL
                    ORDER BY 
                        CASE 
                            WHEN validation_status = 'Invalid' THEN 1
                            ELSE 2
                        END,
                        ConvertedExportedDate DESC
                """)
                
                return [{
                    'health_check_id': row[0],
                    'file_name': row[1],
                    'status': row[2],
                    'reason': row[3],
                    'project_name': row[4],
                    'export_date': row[5].isoformat() if row[5] else None
                } for row in cursor.fetchall()]
                
        except Exception as e:
            logger.exception("❌ Error getting invalid files")
            return []


def validate_naming_on_import(health_check_id: int) -> bool:
    """
    Convenience function to validate naming when health check is imported
    Called by health check import process
    """
    validator = RevitNamingValidator()
    return validator.validate_new_health_check(health_check_id)


if __name__ == "__main__":
    # Test the validator
    validator = RevitNamingValidator()
    
    print("\n" + "="*80)
    print("🔍 REVIT NAMING VALIDATOR TEST")
    print("="*80)
    
    # Test file name patterns
    test_files = [
        "CWPS-123456-ARC-Model.rvt",
        "NFPS-SMS-ZZ-ZZ-M3-M-0001.rvt",
        "ClientName-PRJ001-Building.rvt",
        "ARC-Building Model.rvt",
        "RandomFileName.rvt",
        "NoExtension"
    ]
    
    print("\n🔍 Testing Naming Patterns:")
    for file in test_files:
        status, reason, disc, disc_name = validator.validate_file_naming(file)
        print(f"  • {file}")
        print(f"    Status: {status} - {reason}")
        if disc:
            print(f"    Discipline: {disc} ({disc_name})")
    
    # Validate all unvalidated
    print("\n🔄 Validating all unvalidated records...")
    count = validator.validate_all_unvalidated()
    print(f"✅ Validated {count} records")
    
    # Get summary
    print("\n📊 Validation Summary:")
    summary = validator.get_validation_summary()
    for status, data in summary.items():
        print(f"  • {status}: {data['count']} files, {data['unique_disciplines']} unique disciplines")
    
    # Get invalid files
    print("\n⚠️ Files with Naming Issues (Top 10):")
    invalid = validator.get_invalid_files(limit=10)
    if invalid:
        for file in invalid:
            print(f"  • {file['file_name']}")
            print(f"    Status: {file['status']} - {file['reason']}")
    else:
        print("  ✅ No files with naming issues!")
    
    print("\n" + "="*80)
    print("✅ Naming validator test complete!")
    print("="*80 + "\n")
