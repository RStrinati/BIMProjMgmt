"""Test end-to-end project type display by assigning a type and verifying display"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection, get_project_details, get_projects_full, get_available_project_types
from constants import schema as S
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_end_to_end():
    """Assign a project type to a project and verify it displays correctly"""
    
    # Get available project types
    project_types = get_available_project_types()
    if not project_types:
        logger.error("❌ No project types found in database")
        return False
    
    type_id, type_name = project_types[0]
    logger.info(f"Using project type: {type_id} - {type_name}")
    
    # Assign this type to project 1
    test_project_id = 1
    
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE {S.Projects.TABLE} SET {S.Projects.TYPE_ID} = ? WHERE {S.Projects.ID} = ?",
                (type_id, test_project_id)
            )
            conn.commit()
            logger.info(f"✓ Assigned type '{type_name}' to project {test_project_id}")
    except Exception as e:
        logger.error(f"❌ Failed to assign project type: {e}")
        return False
    
    # Now test that it displays correctly
    logger.info("\n--- Testing get_project_details() ---")
    details = get_project_details(test_project_id)
    if details:
        project_type = details.get('project_type')
        logger.info(f"Project Name: {details.get('project_name')}")
        logger.info(f"Project Type: {project_type}")
        
        if project_type == type_name:
            logger.info(f"✅ SUCCESS: get_project_details() returns correct project_type: '{project_type}'")
        else:
            logger.error(f"❌ FAIL: Expected '{type_name}', got '{project_type}'")
            return False
    else:
        logger.error("❌ FAIL: get_project_details() returned None")
        return False
    
    # Test get_projects_full
    logger.info("\n--- Testing get_projects_full() ---")
    projects_full = get_projects_full()
    project = next((p for p in projects_full if p['project_id'] == test_project_id), None)
    if project:
        project_type = project.get('project_type')
        logger.info(f"Project Name: {project.get('project_name')}")
        logger.info(f"Project Type: {project_type}")
        
        if project_type == type_name:
            logger.info(f"✅ SUCCESS: get_projects_full() returns correct project_type: '{project_type}'")
        else:
            logger.error(f"❌ FAIL: Expected '{type_name}', got '{project_type}'")
            return False
    else:
        logger.error("❌ FAIL: Project not found in get_projects_full()")
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ END-TO-END TEST PASSED!")
    logger.info("Project type is now correctly saved and displayed.")
    logger.info("=" * 60)
    return True

if __name__ == "__main__":
    success = test_end_to_end()
    sys.exit(0 if success else 1)
