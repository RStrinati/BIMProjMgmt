"""Check Project 4 reviews."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from constants import schema as S

with get_db_connection() as conn:
    cursor = conn.cursor()
    
    query = f"""
    SELECT 
        sr.{S.ServiceReviews.REVIEW_ID},
        sr.{S.ServiceReviews.SERVICE_ID},
        sr.{S.ServiceReviews.DELIVERABLES},
        sr.{S.ServiceReviews.FEE_AMOUNT},
        sr.{S.ServiceReviews.IS_USER_MODIFIED},
        ps.{S.ProjectServices.AGREED_FEE},
        ps.{S.ProjectServices.SERVICE_NAME}
    FROM {S.ServiceReviews.TABLE} sr
    JOIN {S.ProjectServices.TABLE} ps 
        ON sr.{S.ServiceReviews.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
    WHERE ps.{S.ProjectServices.PROJECT_ID} = 4
    ORDER BY sr.{S.ServiceReviews.REVIEW_ID}
    """
    
    cursor.execute(query)
    reviews = cursor.fetchall()
    
    print(f"Total reviews for Project 4: {len(reviews)}\n")
    
    for r in reviews:
        review_id, service_id, deliverables, fee_amount, is_modified, agreed_fee, service_name = r
        print(f"Review {review_id} (Service {service_id} - {service_name}):")
        print(f"  Deliverables: {deliverables}")
        print(f"  fee_amount: ${fee_amount:,.2f}" if fee_amount else "  fee_amount: NULL")
        print(f"  is_user_modified: {is_modified}")
        print(f"  Service agreed_fee: ${agreed_fee:,.2f}")
        print()
