"""Test that project_type is now included in project details"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_projects, get_project_details, get_projects_full
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_project_type_display():
    """Test that project_type is correctly returned in all data access methods"""
    
    logger.info("=" * 60)
    logger.info("Testing Project Type Display Fix")
    logger.info("=" * 60)
    
    # Get a sample project
    projects = get_projects()
    if not projects:
        logger.error("❌ No projects found in database")
        return False
    
    project_id, project_name = projects[0]
    logger.info(f"\nTesting with Project: {project_id} - {project_name}")
    
    # Test 1: get_project_details
    logger.info("\n--- Test 1: get_project_details() ---")
    details = get_project_details(project_id)
    if details:
        project_type = details.get('project_type')
        logger.info(f"✓ Project Name: {details.get('project_name')}")
        logger.info(f"✓ Status: {details.get('status')}")
        logger.info(f"✓ Priority: {details.get('priority')}")
        logger.info(f"✓ Project Type: {project_type}")
        
        if project_type is not None:
            logger.info("✅ SUCCESS: project_type is included in get_project_details()")
        else:
            logger.error("❌ FAIL: project_type is None")
            return False
    else:
        logger.error("❌ FAIL: get_project_details() returned None")
        return False
    
    # Test 2: get_projects_full
    logger.info("\n--- Test 2: get_projects_full() ---")
    projects_full = get_projects_full()
    if projects_full:
        sample_project = next((p for p in projects_full if p['project_id'] == project_id), None)
        if sample_project:
            project_type = sample_project.get('project_type')
            logger.info(f"✓ Project Name: {sample_project.get('project_name')}")
            logger.info(f"✓ Status: {sample_project.get('status')}")
            logger.info(f"✓ Project Type: {project_type}")
            
            if project_type is not None:
                logger.info("✅ SUCCESS: project_type is included in get_projects_full()")
            else:
                logger.error("❌ FAIL: project_type is None in get_projects_full()")
                return False
        else:
            logger.error(f"❌ FAIL: Project {project_id} not found in get_projects_full()")
            return False
    else:
        logger.error("❌ FAIL: get_projects_full() returned empty list")
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ ALL TESTS PASSED - Project Type is now displayed correctly!")
    logger.info("=" * 60)
    return True

if __name__ == "__main__":
    success = test_project_type_display()
    sys.exit(0 if success else 1)
