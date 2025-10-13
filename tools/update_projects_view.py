"""Update vw_projects_full view to include project_type name"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_view():
    """Update the vw_projects_full view to include project_type"""
    
    drop_sql = """
    IF OBJECT_ID('vw_projects_full', 'V') IS NOT NULL
        DROP VIEW vw_projects_full;
    """
    
    create_sql = """
    CREATE VIEW vw_projects_full AS
    SELECT
        p.project_id,
        p.project_name,
        c.client_name,
        c.contact_name as client_contact,
        c.contact_email,
        p.project_manager,
        p.internal_lead,
        p.contract_number,
        p.contract_value,
        p.agreed_fee,
        p.payment_terms,
        p.folder_path,
        p.ifc_folder_path,
        p.data_export_folder,
        p.start_date,
        p.end_date,
        p.status,
        p.priority,
        p.created_at,
        p.updated_at,
        p.area_hectares,
        p.mw_capacity,
        p.address,
        p.city,
        p.state,
        p.postcode,
        p.client_id,
        p.type_id,
        pt.type_name as project_type,
        p.sector_id,
        p.method_id
    FROM projects p
    LEFT JOIN clients c ON p.client_id = c.client_id
    LEFT JOIN project_types pt ON p.type_id = pt.type_id;
    """
    
    try:
        with get_db_connection("ProjectManagement") as conn:
            if conn is None:
                logger.error("Failed to connect to database")
                return False
                
            cursor = conn.cursor()
            
            # Drop existing view
            logger.info("Dropping existing view if it exists...")
            cursor.execute(drop_sql)
            conn.commit()
            
            # Create new view
            logger.info("Creating updated view with project_type...")
            cursor.execute(create_sql)
            conn.commit()
            
            logger.info("✅ Successfully updated vw_projects_full view to include project_type")
            return True
        
    except Exception as e:
        logger.error(f"❌ Error updating view: {e}")
        return False

if __name__ == "__main__":
    success = update_view()
    sys.exit(0 if success else 1)
