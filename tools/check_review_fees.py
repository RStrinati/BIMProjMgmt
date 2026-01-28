"""Check actual review fee data."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from constants import schema as S

with get_db_connection() as conn:
    cursor = conn.cursor()
    
    # Get reviews with fee data
    query = f"""
    SELECT TOP 20
        sr.{S.ServiceReviews.REVIEW_ID},
        sr.{S.ServiceReviews.SERVICE_ID},
        sr.{S.ServiceReviews.DELIVERABLES},
        sr.{S.ServiceReviews.FEE_AMOUNT},
        sr.{S.ServiceReviews.BILLING_AMOUNT},
        sr.{S.ServiceReviews.IS_USER_MODIFIED},
        sr.{S.ServiceReviews.USER_MODIFIED_FIELDS},
        ps.{S.ProjectServices.PROJECT_ID},
        ps.{S.ProjectServices.AGREED_FEE},
        ps.{S.ProjectServices.REVIEW_COUNT_PLANNED}
    FROM {S.ServiceReviews.TABLE} sr
    JOIN {S.ProjectServices.TABLE} ps 
        ON sr.{S.ServiceReviews.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
    WHERE ps.{S.ProjectServices.AGREED_FEE} > 0
    ORDER BY sr.{S.ServiceReviews.REVIEW_ID}
    """
    
    cursor.execute(query)
    reviews = cursor.fetchall()
    
    print(f"\nTotal reviews with agreed_fee > 0: {len(reviews)}\n")
    
    for r in reviews:
        review_id, service_id, deliverables, fee_amount, billing_amount, is_modified, modified_fields, project_id, agreed_fee, review_count_planned = r
        
        print(f"Review {review_id} (Service {service_id}, Project {project_id}):")
        print(f"  Deliverables: {deliverables}")
        print(f"  fee_amount: {fee_amount}")
        print(f"  billing_amount: {billing_amount}")
        print(f"  is_user_modified: {is_modified}")
        print(f"  user_modified_fields: {modified_fields}")
        print(f"  Service agreed_fee: ${agreed_fee:,.2f}" if agreed_fee else f"  Service agreed_fee: None")
        print(f"  Service review_count_planned: {review_count_planned}")
        print()
