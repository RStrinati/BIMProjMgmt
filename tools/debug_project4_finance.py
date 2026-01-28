"""
Debug script to check project 4 finance data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from constants.schema import ServiceReviews, ServiceItems, ProjectServices

with get_db_connection() as conn:
    cursor = conn.cursor()
    
    # Check reviews for project 4
    query = f"""
    SELECT 
        sr.{ServiceReviews.REVIEW_ID},
        sr.{ServiceReviews.FEE_AMOUNT},
        sr.{ServiceReviews.IS_BILLED},
        sr.{ServiceReviews.INVOICE_STATUS},
        sr.{ServiceReviews.STATUS}
    FROM {ServiceReviews.TABLE} sr
    INNER JOIN {ProjectServices.TABLE} ps ON ps.{ProjectServices.SERVICE_ID} = sr.{ServiceReviews.SERVICE_ID}
    WHERE ps.{ProjectServices.PROJECT_ID} = 4
    ORDER BY sr.{ServiceReviews.REVIEW_ID}
    """
    
    cursor.execute(query)
    reviews = cursor.fetchall()
    
    print("Reviews for Project 4:")
    print("-" * 80)
    total_fee = 0
    billed_fee = 0
    for row in reviews:
        review_id, fee_amount, is_billed, invoice_status, status = row
        total_fee += float(fee_amount or 0)
        if is_billed:
            billed_fee += float(fee_amount or 0)
        print(f"  Review {review_id}: fee=${fee_amount}, is_billed={is_billed}, invoice_status={invoice_status}, status={status}")
    
    print()
    print(f"Total fee: ${total_fee:,.2f}")
    print(f"Billed fee: ${billed_fee:,.2f}")
    print()
    
    # Check items for project 4
    query_items = f"""
    SELECT 
        si.{ServiceItems.ITEM_ID},
        si.{ServiceItems.FEE_AMOUNT},
        si.{ServiceItems.IS_BILLED},
        si.{ServiceItems.INVOICE_STATUS},
        si.{ServiceItems.STATUS}
    FROM {ServiceItems.TABLE} si
    INNER JOIN {ProjectServices.TABLE} ps ON ps.{ProjectServices.SERVICE_ID} = si.{ServiceItems.SERVICE_ID}
    WHERE ps.{ProjectServices.PROJECT_ID} = 4
    ORDER BY si.{ServiceItems.ITEM_ID}
    """
    
    cursor.execute(query_items)
    items = cursor.fetchall()
    
    print("Items for Project 4:")
    print("-" * 80)
    item_total = 0
    item_billed = 0
    for row in items:
        item_id, fee_amount, is_billed, invoice_status, status = row
        item_total += float(fee_amount or 0)
        if is_billed:
            item_billed += float(fee_amount or 0)
        print(f"  Item {item_id}: fee=${fee_amount}, is_billed={is_billed}, invoice_status={invoice_status}, status={status}")
    
    print()
    print(f"Item total fee: ${item_total:,.2f}")
    print(f"Item billed fee: ${item_billed:,.2f}")
    print()
    print(f"Grand total: ${total_fee + item_total:,.2f}")
    print(f"Grand billed: ${billed_fee + item_billed:,.2f}")

