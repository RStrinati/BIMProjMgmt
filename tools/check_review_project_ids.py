"""Check if reviews have project_id."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from constants.schema import ServiceReviews, ProjectServices

with get_db_connection() as conn:
    cursor = conn.cursor()
    
    query = f"""
    SELECT TOP 5
        sr.{ServiceReviews.REVIEW_ID},
        sr.{ServiceReviews.PROJECT_ID},
        sr.{ServiceReviews.SERVICE_ID},
        ps.{ProjectServices.PROJECT_ID} as ps_project_id
    FROM {ServiceReviews.TABLE} sr
    JOIN {ProjectServices.TABLE} ps 
        ON sr.{ServiceReviews.SERVICE_ID} = ps.{ProjectServices.SERVICE_ID}
    WHERE ps.{ProjectServices.PROJECT_ID} = 4
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} reviews for Project 4 via ProjectServices join\n")
    
    for r in rows:
        review_id, sr_project_id, service_id, ps_project_id = r
        print(f"Review {review_id}: sr.project_id={sr_project_id}, service_id={service_id}, ps.project_id={ps_project_id}")
