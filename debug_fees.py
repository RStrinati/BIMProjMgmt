#!/usr/bin/env python3
"""Debug script to check actual database fee values."""

import sys
sys.path.insert(0, '.')

from database_pool import get_db_connection
from constants.schema import ServiceReviews, ServiceItems, ProjectServices

project_id = 4

with get_db_connection() as conn:
    cursor = conn.cursor()
    
    # Check ServiceReviews for project 4
    cursor.execute(f"""
    SELECT sr.{ServiceReviews.REVIEW_ID}, sr.{ServiceReviews.BILLING_AMOUNT}, sr.{ServiceReviews.FEE_AMOUNT}, 
           sr.{ServiceReviews.IS_USER_MODIFIED}, sr.{ServiceReviews.WEIGHT_FACTOR},
           ps.{ProjectServices.AGREED_FEE}, ps.{ProjectServices.REVIEW_COUNT_PLANNED}
    FROM {ServiceReviews.TABLE} sr
    JOIN {ProjectServices.TABLE} ps ON sr.{ServiceReviews.SERVICE_ID} = ps.{ProjectServices.SERVICE_ID}
    WHERE sr.{ServiceReviews.PROJECT_ID} = ?
    """, [project_id])
    
    reviews = cursor.fetchall()
    print("=== ServiceReviews for Project 4 ===")
    if reviews:
        for review in reviews:
            print(f"Review {review[0]}: billing_amount={review[1]}, fee_amount={review[2]}, is_user_modified={review[3]}, weight={review[4]}, agreed_fee={review[5]}, review_count={review[6]}")
    else:
        print("No reviews found")
    
    # Check ServiceItems for project 4
    cursor.execute(f"""
    SELECT si.{ServiceItems.ITEM_ID}, si.{ServiceItems.FEE_AMOUNT}, si.{ServiceItems.IS_USER_MODIFIED},
           ps.{ProjectServices.AGREED_FEE}
    FROM {ServiceItems.TABLE} si
    JOIN {ProjectServices.TABLE} ps ON si.{ServiceItems.SERVICE_ID} = ps.{ProjectServices.SERVICE_ID}
    WHERE si.{ServiceItems.PROJECT_ID} = ?
    """, [project_id])
    
    items = cursor.fetchall()
    print("\n=== ServiceItems for Project 4 ===")
    if items:
        for item in items:
            print(f"Item {item[0]}: fee_amount={item[1]}, is_user_modified={item[2]}, agreed_fee={item[3]}")
    else:
        print("No items found")
