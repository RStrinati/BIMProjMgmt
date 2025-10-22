"""
Revit Health Warehouse Service
Provides high-level access to cross-database health analytics and warehouse views

Author: System
Created: 2025-10-16
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from config import Config
from constants import schema as S
from typing import List, Dict, Optional, Tuple
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RevitHealthWarehouseService:
    """Service for accessing Revit health warehouse data with cross-database integration"""
    
    def __init__(self):
        self.db_name = Config.REVIT_HEALTH_DB
    
    def get_project_health_summary(self, project_id: int) -> Dict:
        """
        Get comprehensive health summary for a specific project
        
        Args:
            project_id: Internal project ID from ProjectManagement DB
            
        Returns:
            Dictionary with aggregated health metrics
        """
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        pm_project_id,
                        pm_project_name,
                        project_status,
                        client_name,
                        total_health_checks,
                        unique_files,
                        latest_health_check_date,
                        avg_health_score,
                        total_warnings_all_files,
                        total_critical_warnings,
                        total_model_size_mb,
                        good_files,
                        fair_files,
                        poor_files,
                        critical_files,
                        current_files,
                        recent_files,
                        outdated_files,
                        files_with_link_risks
                    FROM dbo.vw_RevitHealth_ProjectSummary
                    WHERE pm_project_id = ?
                """, (project_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return {
                        'project_id': row[0],
                        'project_name': row[1],
                        'project_status': row[2],
                        'client_name': row[3],
                        'total_checks': row[4] or 0,
                        'unique_files': row[5] or 0,
                        'latest_check': row[6].isoformat() if row[6] else None,
                        'avg_health_score': round(float(row[7]), 2) if row[7] else 0,
                        'total_warnings': row[8] or 0,
                        'critical_warnings': row[9] or 0,
                        'total_model_size_mb': round(float(row[10]), 2) if row[10] else 0,
                        'files_by_health': {
                            'good': row[11] or 0,
                            'fair': row[12] or 0,
                            'poor': row[13] or 0,
                            'critical': row[14] or 0
                        },
                        'data_freshness': {
                            'current': row[15] or 0,
                            'recent': row[16] or 0,
                            'outdated': row[17] or 0
                        },
                        'risk_indicators': {
                            'files_with_link_risks': row[18] or 0
                        }
                    }
                
                return {}
                
        except Exception as e:
            logger.exception(f"❌ Error getting project health summary for project {project_id}")
            return {}
    
    def get_unmapped_files(self, limit: int = 50, min_confidence: int = 60) -> List[Dict]:
        """
        Get unmapped Revit files with project suggestions
        
        Args:
            limit: Maximum number of results
            min_confidence: Minimum match confidence score (0-100)
            
        Returns:
            List of unmapped files with suggested mappings
        """
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"""
                    SELECT TOP {limit}
                        health_check_id,
                        revit_file_name,
                        revit_project_name,
                        revit_project_number,
                        revit_client_name,
                        export_date,
                        total_warnings,
                        critical_warnings,
                        calculated_health_score,
                        health_category,
                        suggested_project_id,
                        suggested_project_name,
                        match_confidence
                    FROM dbo.vw_RevitHealth_UnmappedFiles
                    WHERE match_confidence >= ?
                    ORDER BY 
                        match_confidence DESC,
                        calculated_health_score ASC, 
                        total_warnings DESC
                """, (min_confidence,))
                
                return [{
                    'health_check_id': row[0],
                    'file_name': row[1],
                    'project_name': row[2],
                    'project_number': row[3],
                    'client_name': row[4],
                    'export_date': row[5].isoformat() if row[5] else None,
                    'warnings': row[6] or 0,
                    'critical_warnings': row[7] or 0,
                    'health_score': row[8] or 0,
                    'health_category': row[9],
                    'suggested_project_id': row[10],
                    'suggested_project_name': row[11],
                    'match_confidence': row[12] or 0
                } for row in cursor.fetchall()]
                
        except Exception as e:
            logger.exception("❌ Error getting unmapped files")
            return []
    
    def create_alias_mapping(self, health_check_id: int, project_id: int, alias_name: str) -> Tuple[bool, str]:
        """
        Create alias mapping for Revit file to project
        
        Args:
            health_check_id: Health check record ID
            project_id: Target project ID
            alias_name: Alias to create for mapping
            
        Returns:
            Tuple of (success, message)
        """
        try:
            from services.project_alias_service import ProjectAliasManager
            
            manager = ProjectAliasManager()
            success = manager.add_alias(project_id, alias_name)
            manager.close_connection()
            
            if success:
                logger.info(f"✅ Created alias '{alias_name}' for project {project_id}")
                return True, f"Alias '{alias_name}' created successfully"
            else:
                return False, "Failed to create alias"
                
        except Exception as e:
            logger.exception(f"❌ Error creating alias mapping: {e}")
            return False, str(e)
    
    def get_health_trends(self, project_id: int, months: int = 6) -> pd.DataFrame:
        """
        Get health trends for project over time
        
        Args:
            project_id: Project ID
            months: Number of months to look back
            
        Returns:
            DataFrame with historical health metrics
        """
        try:
            with get_db_connection(self.db_name) as conn:
                query = f"""
                    SELECT 
                        export_date,
                        revit_file_name,
                        calculated_health_score,
                        total_warnings,
                        critical_warnings,
                        file_size_mb,
                        view_efficiency_pct,
                        total_elements
                    FROM dbo.vw_RevitHealthWarehouse_CrossDB
                    WHERE pm_project_id = ?
                      AND export_date >= DATEADD(MONTH, -{months}, GETDATE())
                    ORDER BY export_date DESC, revit_file_name
                """
                
                df = pd.read_sql(query, conn, params=(project_id,))
                return df
                
        except Exception as e:
            logger.exception(f"❌ Error getting health trends for project {project_id}")
            return pd.DataFrame()
    
    def get_file_health_detail(self, health_check_id: int) -> Dict:
        """
        Get detailed health information for specific file
        
        Args:
            health_check_id: Health check record ID
            
        Returns:
            Dictionary with detailed health metrics
        """
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        health_check_id,
                        revit_file_name,
                        pm_project_id,
                        pm_project_name,
                        mapping_status,
                        calculated_health_score,
                        health_category,
                        total_warnings,
                        critical_warnings,
                        file_size_mb,
                        export_date
                    FROM dbo.vw_RevitHealthWarehouse_CrossDB
                    WHERE health_check_id = ?
                """, (health_check_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return {
                        'health_check_id': row[0],
                        'file_name': row[1],
                        'pm_project_id': row[2],
                        'pm_project_name': row[3],
                        'mapping_status': row[4],
                        'health_score': row[5],
                        'health_category': row[6],
                        'total_warnings': row[7],
                        'critical_warnings': row[8],
                        'file_size_mb': row[9],
                        'export_date': row[10].isoformat() if row[10] else None
                    }
                
                return {}
                
        except Exception as e:
            logger.exception(f"❌ Error getting file health detail for ID {health_check_id}")
            return {}
    
    def get_critical_files(self, project_id: Optional[int] = None, limit: int = 20) -> List[Dict]:
        """
        Get files with critical health issues
        
        Args:
            project_id: Optional project filter
            limit: Maximum results
            
        Returns:
            List of critical files
        """
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                
                where_clause = "WHERE health_category IN ('Poor', 'Critical')"
                params = []
                
                if project_id:
                    where_clause += " AND pm_project_id = ?"
                    params.append(project_id)
                
                query = f"""
                    SELECT TOP {limit}
                        health_check_id,
                        revit_file_name,
                        pm_project_name,
                        health_category,
                        calculated_health_score,
                        total_warnings,
                        critical_warnings,
                        export_date,
                        link_health_flag
                    FROM dbo.vw_RevitHealthWarehouse_CrossDB
                    {where_clause}
                    ORDER BY calculated_health_score ASC, critical_warnings DESC
                """
                
                cursor.execute(query, params)
                
                return [{
                    'health_check_id': row[0],
                    'file_name': row[1],
                    'project_name': row[2],
                    'health_category': row[3],
                    'health_score': row[4],
                    'warnings': row[5],
                    'critical_warnings': row[6],
                    'export_date': row[7].isoformat() if row[7] else None,
                    'link_flag': row[8]
                } for row in cursor.fetchall()]
                
        except Exception as e:
            logger.exception("❌ Error getting critical files")
            return []
    
    def get_all_projects_summary(self) -> List[Dict]:
        """Get health summary for all projects"""
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        pm_project_id,
                        pm_project_name,
                        client_name,
                        unique_files,
                        avg_health_score,
                        total_warnings_all_files,
                        good_files,
                        poor_files,
                        critical_files
                    FROM dbo.vw_RevitHealth_ProjectSummary
                    ORDER BY pm_project_name
                """)
                
                return [{
                    'project_id': row[0],
                    'project_name': row[1],
                    'client_name': row[2],
                    'unique_files': row[3] or 0,
                    'avg_health_score': round(float(row[4]), 2) if row[4] else 0,
                    'total_warnings': row[5] or 0,
                    'good_files': row[6] or 0,
                    'poor_files': row[7] or 0,
                    'critical_files': row[8] or 0
                } for row in cursor.fetchall()]
                
        except Exception as e:
            logger.exception("❌ Error getting all projects summary")
            return []


def get_warehouse_service() -> RevitHealthWarehouseService:
    """Get warehouse service instance"""
    return RevitHealthWarehouseService()


if __name__ == "__main__":
    # Test the service
    service = get_warehouse_service()
    
    print("\n" + "="*80)
    print("📊 REVIT HEALTH WAREHOUSE SERVICE TEST")
    print("="*80)
    
    # Test all projects summary
    print("\n📋 All Projects Health Summary:")
    all_projects = service.get_all_projects_summary()
    for proj in all_projects:
        print(f"  • {proj['project_name']}: {proj['unique_files']} files, "
              f"avg score: {proj['avg_health_score']}, warnings: {proj['total_warnings']}")
    
    # Test specific project summary
    if all_projects:
        test_project_id = all_projects[0]['project_id']
        print(f"\n📊 Detailed Summary for Project {test_project_id}:")
        summary = service.get_project_health_summary(test_project_id)
        if summary:
            print(f"  Project: {summary['project_name']}")
            print(f"  Client: {summary['client_name']}")
            print(f"  Files: {summary['unique_files']}")
            print(f"  Avg Health Score: {summary['avg_health_score']}")
            print(f"  Total Warnings: {summary['total_warnings']}")
            print(f"  Health Distribution: {summary['files_by_health']}")
    
    # Test unmapped files
    print("\n🔍 Unmapped Files (if any):")
    unmapped = service.get_unmapped_files(limit=10)
    if unmapped:
        for file in unmapped:
            print(f"  • {file['file_name']}: confidence {file['match_confidence']}% "
                  f"→ {file['suggested_project_name']}")
    else:
        print("  ✅ No unmapped files found!")
    
    # Test critical files
    print("\n⚠️ Critical Health Files (Top 5):")
    critical = service.get_critical_files(limit=5)
    for file in critical:
        print(f"  • {file['file_name']}: Score {file['health_score']} "
              f"({file['warnings']} warnings, {file['critical_warnings']} critical)")
    
    print("\n" + "="*80)
    print("✅ Warehouse service test complete!")
    print("="*80 + "\n")
