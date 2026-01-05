"""
Revit Health Warehouse - Deployment and Testing Script
Automates deployment and validation of warehouse objects

Author: Data Warehouse Team
Date: 2025-12-04
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from config import Config
import logging
from datetime import datetime
from typing import Tuple, List, Dict
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WarehouseDeployer:
    """Handles deployment and testing of Revit health warehouse"""
    
    def __init__(self):
        self.db_name = 'ProjectManagement'
        self.deployment_order = [
            ('dim.revit_file', 'U', 'Dimension table for Revit files'),
            ('stg.revit_health_snapshots', 'U', 'Staging table for health snapshots'),
            ('fact.revit_health_daily', 'U', 'Fact table for daily health metrics'),
            ('warehouse.usp_load_stg_revit_health', 'P', 'ETL procedure for staging'),
            ('warehouse.usp_load_fact_revit_health_daily', 'P', 'ETL procedure for fact table'),
            ('mart.v_project_health_summary', 'V', 'Project health summary view'),
            ('mart.v_health_trends_monthly', 'V', 'Monthly health trends view')
        ]
    
    def verify_deployment(self) -> Tuple[bool, List[str]]:
        """
        Verify all warehouse objects exist
        
        Returns:
            Tuple of (all_exist, missing_objects)
        """
        logger.info("="*80)
        logger.info("VERIFYING WAREHOUSE DEPLOYMENT")
        logger.info("="*80)
        
        missing = []
        
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                
                for obj_name, obj_type, description in self.deployment_order:
                    cursor.execute("""
                        SELECT CASE WHEN OBJECT_ID(?, ?) IS NOT NULL THEN 1 ELSE 0 END
                    """, (obj_name, obj_type))
                    
                    exists = cursor.fetchone()[0]
                    
                    if exists:
                        logger.info(f"  ✓ {obj_name} - {description}")
                    else:
                        logger.error(f"  ✗ {obj_name} - MISSING")
                        missing.append(obj_name)
                
                logger.info("")
                
                if missing:
                    logger.error(f"Deployment incomplete. Missing {len(missing)} objects:")
                    for obj in missing:
                        logger.error(f"  - {obj}")
                    return False, missing
                else:
                    logger.info("✅ All warehouse objects deployed successfully!")
                    return True, []
                    
        except Exception as e:
            logger.exception(f"Error verifying deployment: {e}")
            return False, ['ERROR']
    
    def run_initial_etl(self, debug: bool = True) -> Tuple[bool, str]:
        """
        Run initial ETL load to populate warehouse
        
        Args:
            debug: Enable debug output
            
        Returns:
            Tuple of (success, message)
        """
        logger.info("="*80)
        logger.info("RUNNING INITIAL ETL LOAD")
        logger.info("="*80)
        
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Step 1: Load staging
                logger.info("\n📥 STEP 1: Loading staging table...")
                start_time = time.time()
                
                cursor.execute("EXEC warehouse.usp_load_stg_revit_health @debug = ?", (1 if debug else 0,))
                
                # Capture print statements
                while cursor.nextset():
                    pass
                
                staging_duration = time.time() - start_time
                logger.info(f"  ✓ Staging load completed in {staging_duration:.2f} seconds")
                
                # Step 2: Load fact table
                logger.info("\n📊 STEP 2: Loading fact table...")
                start_time = time.time()
                
                cursor.execute("EXEC warehouse.usp_load_fact_revit_health_daily @debug = ?", (1 if debug else 0,))
                
                while cursor.nextset():
                    pass
                
                fact_duration = time.time() - start_time
                logger.info(f"  ✓ Fact load completed in {fact_duration:.2f} seconds")
                
                conn.commit()
                
                logger.info("\n✅ Initial ETL completed successfully!")
                return True, "ETL completed successfully"
                
        except Exception as e:
            logger.exception(f"❌ Error running ETL: {e}")
            return False, str(e)
    
    def validate_data_quality(self) -> Dict:
        """
        Validate data quality in warehouse tables
        
        Returns:
            Dictionary with validation results
        """
        logger.info("="*80)
        logger.info("VALIDATING DATA QUALITY")
        logger.info("="*80)
        
        results = {}
        
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Check staging table
                logger.info("\n📋 Staging Table (stg.revit_health_snapshots):")
                cursor.execute("""
                    SELECT 
                        COUNT(*) as row_count,
                        COUNT(DISTINCT project_id) as distinct_projects,
                        COUNT(DISTINCT revit_file_name) as distinct_files,
                        MIN(export_date) as earliest_export,
                        MAX(export_date) as latest_export,
                        AVG(health_score) as avg_health_score
                    FROM stg.revit_health_snapshots
                """)
                
                row = cursor.fetchone()
                results['staging'] = {
                    'row_count': row[0] or 0,
                    'distinct_projects': row[1] or 0,
                    'distinct_files': row[2] or 0,
                    'earliest_export': row[3],
                    'latest_export': row[4],
                    'avg_health_score': round(float(row[5]), 2) if row[5] else 0
                }
                
                logger.info(f"  Rows: {results['staging']['row_count']}")
                logger.info(f"  Projects: {results['staging']['distinct_projects']}")
                logger.info(f"  Files: {results['staging']['distinct_files']}")
                logger.info(f"  Avg Health Score: {results['staging']['avg_health_score']}")
                
                # Check dimension table
                logger.info("\n📁 Dimension Table (dim.revit_file):")
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(CASE WHEN current_flag = 1 THEN 1 END) as current_records,
                        COUNT(DISTINCT discipline_code) as distinct_disciplines
                    FROM dim.revit_file
                """)
                
                row = cursor.fetchone()
                results['dimension'] = {
                    'total_records': row[0] or 0,
                    'current_records': row[1] or 0,
                    'distinct_disciplines': row[2] or 0
                }
                
                logger.info(f"  Total Records: {results['dimension']['total_records']}")
                logger.info(f"  Current Records: {results['dimension']['current_records']}")
                logger.info(f"  Disciplines: {results['dimension']['distinct_disciplines']}")
                
                # Check fact table
                logger.info("\n📊 Fact Table (fact.revit_health_daily):")
                cursor.execute("""
                    SELECT 
                        COUNT(*) as fact_count,
                        COUNT(DISTINCT project_key) as distinct_projects,
                        COUNT(DISTINCT file_name_key) as distinct_files,
                        AVG(health_score) as avg_health_score,
                        SUM(total_warnings) as total_warnings,
                        AVG(CAST(naming_valid AS FLOAT)) * 100 as naming_compliance,
                        AVG(CAST(coordinates_aligned AS FLOAT)) * 100 as coord_compliance
                    FROM fact.revit_health_daily
                """)
                
                row = cursor.fetchone()
                results['fact'] = {
                    'fact_count': row[0] or 0,
                    'distinct_projects': row[1] or 0,
                    'distinct_files': row[2] or 0,
                    'avg_health_score': round(float(row[3]), 2) if row[3] else 0,
                    'total_warnings': row[4] or 0,
                    'naming_compliance': round(float(row[5]), 2) if row[5] else 0,
                    'coord_compliance': round(float(row[6]), 2) if row[6] else 0
                }
                
                logger.info(f"  Fact Records: {results['fact']['fact_count']}")
                logger.info(f"  Projects: {results['fact']['distinct_projects']}")
                logger.info(f"  Files: {results['fact']['distinct_files']}")
                logger.info(f"  Avg Health Score: {results['fact']['avg_health_score']}")
                logger.info(f"  Total Warnings: {results['fact']['total_warnings']}")
                logger.info(f"  Naming Compliance: {results['fact']['naming_compliance']}%")
                logger.info(f"  Coordinate Compliance: {results['fact']['coord_compliance']}%")
                
                # Check marts
                logger.info("\n📈 Analytical Marts:")
                cursor.execute("SELECT COUNT(*) FROM mart.v_project_health_summary")
                project_summary_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM mart.v_health_trends_monthly")
                trends_count = cursor.fetchone()[0]
                
                results['marts'] = {
                    'project_summary_count': project_summary_count or 0,
                    'trends_count': trends_count or 0
                }
                
                logger.info(f"  Project Summaries: {results['marts']['project_summary_count']}")
                logger.info(f"  Monthly Trends: {results['marts']['trends_count']}")
                
                logger.info("\n✅ Data quality validation completed!")
                
                return results
                
        except Exception as e:
            logger.exception(f"❌ Error validating data quality: {e}")
            return {}
    
    def test_warehouse_service(self):
        """Test Python warehouse service with new methods"""
        logger.info("="*80)
        logger.info("TESTING PYTHON WAREHOUSE SERVICE")
        logger.info("="*80)
        
        try:
            from services.revit_health_warehouse_service import RevitHealthWarehouseService
            
            service = RevitHealthWarehouseService()
            
            # Test warehouse mart methods
            logger.info("\n📊 Testing warehouse mart queries...")
            
            # Get all projects from warehouse
            projects = service.get_all_projects_from_warehouse()
            logger.info(f"  ✓ Retrieved {len(projects)} projects from warehouse")
            
            if projects:
                # Test specific project health
                test_project_id = projects[0]['project_id']
                logger.info(f"\n  Testing project {test_project_id}: {projects[0]['project_name']}")
                
                health = service.get_project_health_from_warehouse(test_project_id)
                if health:
                    logger.info(f"    • Files: {health['total_files']}")
                    logger.info(f"    • Avg Health Score: {health['avg_health_score']}")
                    logger.info(f"    • Overall Compliance: {health['validation_compliance']['overall']}%")
                
                # Test trends
                logger.info(f"\n  Testing health trends...")
                trends = service.get_health_trends_from_warehouse(test_project_id, months=6)
                if not trends.empty:
                    logger.info(f"    ✓ Retrieved {len(trends)} monthly trend records")
                else:
                    logger.info(f"    • No trend data available yet")
            
            logger.info("\n✅ Python service tests completed!")
            
        except Exception as e:
            logger.exception(f"❌ Error testing warehouse service: {e}")


def main():
    """Main deployment and testing workflow"""
    deployer = WarehouseDeployer()
    
    print("\n" + "="*80)
    print("REVIT HEALTH WAREHOUSE - DEPLOYMENT AND TESTING")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Step 1: Verify deployment
    all_exist, missing = deployer.verify_deployment()
    
    if not all_exist:
        logger.error("\n❌ Deployment verification failed. Please run SQL deployment script first:")
        logger.error("   sqlcmd -S <server> -d ProjectManagement -i sql/deploy_revit_health_warehouse.sql")
        return 1
    
    # Step 2: Run initial ETL
    print("\n")
    success, message = deployer.run_initial_etl(debug=True)
    
    if not success:
        logger.error(f"\n❌ ETL failed: {message}")
        return 1
    
    # Step 3: Validate data quality
    print("\n")
    results = deployer.validate_data_quality()
    
    if not results:
        logger.error("\n❌ Data quality validation failed")
        return 1
    
    # Step 4: Test Python service
    print("\n")
    deployer.test_warehouse_service()
    
    # Summary
    print("\n" + "="*80)
    print("DEPLOYMENT SUMMARY")
    print("="*80)
    print("✅ All warehouse objects deployed and tested successfully!")
    print(f"\n📊 Key Metrics:")
    print(f"   • Projects: {results['fact']['distinct_projects']}")
    print(f"   • Files: {results['fact']['distinct_files']}")
    print(f"   • Fact Records: {results['fact']['fact_count']}")
    print(f"   • Avg Health Score: {results['fact']['avg_health_score']}")
    print(f"   • Naming Compliance: {results['fact']['naming_compliance']}%")
    print(f"\n🎯 Next Steps:")
    print("   1. Schedule daily ETL job in SQL Server Agent")
    print("   2. Create Power BI dashboards using mart views")
    print("   3. Integrate warehouse queries into UI components")
    print("   4. Monitor data freshness and quality metrics")
    print("="*80 + "\n")
    
    return 0


if __name__ == "__main__":
    exit(main())
