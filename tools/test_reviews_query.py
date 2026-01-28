"""Test reviews query."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from constants.schema import ServiceReviews, ProjectServices

with get_db_connection() as conn:
    cursor = conn.cursor()
    
    query = f"""
    SELECT 
        sr.{ServiceReviews.REVIEW_ID} as id,
        'review' as type,
        sr.{ServiceReviews.SERVICE_ID},
        ps.{ProjectServices.SERVICE_CODE},
        ps.{ProjectServices.SERVICE_NAME},
        sr.{ServiceReviews.BILLING_PHASE} as phase,
        COALESCE(sr.{ServiceReviews.DELIVERABLES}, '') as title,
        sr.{ServiceReviews.PLANNED_DATE},
        sr.{ServiceReviews.DUE_DATE},
        sr.{ServiceReviews.STATUS},
        sr.{ServiceReviews.FEE_AMOUNT},
        sr.{ServiceReviews.IS_USER_MODIFIED},
        sr.{ServiceReviews.INVOICE_STATUS},
        sr.{ServiceReviews.INVOICE_REFERENCE},
        sr.{ServiceReviews.INVOICE_DATE},
        sr.{ServiceReviews.INVOICE_MONTH_FINAL},
        sr.{ServiceReviews.IS_BILLED},
        ps.{ProjectServices.AGREED_FEE},
        ps.{ProjectServices.REVIEW_COUNT_PLANNED}
    FROM {ServiceReviews.TABLE} sr
    JOIN {ProjectServices.TABLE} ps ON sr.{ServiceReviews.SERVICE_ID} = ps.{ProjectServices.SERVICE_ID}
    WHERE sr.{ServiceReviews.PROJECT_ID} = ?
    """
    
    cursor.execute(query, [4])
    reviews = cursor.fetchall()
    cols = [col[0] for col in cursor.description]
    
    print(f"Query returned {len(reviews)} reviews")
    print(f"Columns: {cols}\n")
    
    if reviews:
        row_dict = dict(zip(cols, reviews[0]))
        print(f"First review id={row_dict.get('id')}")
        print(f"  service_id={row_dict.get(ServiceReviews.SERVICE_ID)}")
        print(f"  fee_amount={row_dict.get(ServiceReviews.FEE_AMOUNT)}")
        print(f"  agreed_fee={row_dict.get(ProjectServices.AGREED_FEE)}")
