#!/usr/bin/env python3
"""
Fee Trace - End-to-end investigation of fee resolution.

This script traces fees from database through to API endpoints to understand
the deterministic fee model.
"""

import sys
sys.path.insert(0, '.')

from database_pool import get_db_connection
from constants.schema import ServiceReviews, ServiceItems, ProjectServices

print("="*80)
print("FEE TRACE INVESTIGATION")
print("="*80)

# Find a service with both agreed_fee and reviews
with get_db_connection() as conn:
    cursor = conn.cursor()
    
    # Find services with reviews
    cursor.execute(f"""
    SELECT 
        ps.{ProjectServices.SERVICE_ID},
        ps.{ProjectServices.PROJECT_ID},
        ps.{ProjectServices.SERVICE_CODE},
        ps.{ProjectServices.SERVICE_NAME},
        ps.{ProjectServices.AGREED_FEE},
        ps.{ProjectServices.REVIEW_COUNT_PLANNED},
        COUNT(sr.{ServiceReviews.REVIEW_ID}) as actual_review_count
    FROM {ProjectServices.TABLE} ps
    LEFT JOIN {ServiceReviews.TABLE} sr ON ps.{ProjectServices.SERVICE_ID} = sr.{ServiceReviews.SERVICE_ID}
    WHERE ps.{ProjectServices.AGREED_FEE} IS NOT NULL 
      AND ps.{ProjectServices.AGREED_FEE} > 0
      AND ps.{ProjectServices.REVIEW_COUNT_PLANNED} > 0
    GROUP BY 
        ps.{ProjectServices.SERVICE_ID},
        ps.{ProjectServices.PROJECT_ID},
        ps.{ProjectServices.SERVICE_CODE},
        ps.{ProjectServices.SERVICE_NAME},
        ps.{ProjectServices.AGREED_FEE},
        ps.{ProjectServices.REVIEW_COUNT_PLANNED}
    HAVING COUNT(sr.{ServiceReviews.REVIEW_ID}) > 0
    ORDER BY ps.{ProjectServices.PROJECT_ID}
    """)
    
    services = cursor.fetchall()
    
    if not services:
        print("\n❌ No services found with agreed_fee, planned reviews, and actual reviews")
        sys.exit(1)
    
    # Pick the first service
    service = services[0]
    service_id, project_id, service_code, service_name, agreed_fee, review_count_planned, actual_review_count = service
    
    print(f"\n📋 SELECTED SERVICE")
    print(f"Service ID: {service_id}")
    print(f"Project ID: {project_id}")
    print(f"Service Code: {service_code}")
    print(f"Service Name: {service_name}")
    print(f"Agreed Fee: ${agreed_fee:,.2f}")
    print(f"Review Count Planned: {review_count_planned}")
    print(f"Actual Review Count: {actual_review_count}")
    print(f"Expected Per-Review Fee (equal split): ${agreed_fee / review_count_planned:,.2f}")
    
    # Get all reviews for this service
    cursor.execute(f"""
    SELECT 
        {ServiceReviews.REVIEW_ID},
        {ServiceReviews.DELIVERABLES},
        {ServiceReviews.BILLING_AMOUNT},
        {ServiceReviews.FEE_AMOUNT},
        {ServiceReviews.IS_USER_MODIFIED},
        {ServiceReviews.USER_MODIFIED_FIELDS},
        {ServiceReviews.PLANNED_DATE},
        {ServiceReviews.STATUS}
    FROM {ServiceReviews.TABLE}
    WHERE {ServiceReviews.SERVICE_ID} = ?
    ORDER BY {ServiceReviews.PLANNED_DATE}
    """, [service_id])
    
    reviews = cursor.fetchall()
    
    print(f"\n📝 REVIEWS ({len(reviews)} found)")
    print("-" * 80)
    for review in reviews:
        review_id, deliverables, billing_amount, fee_amount, is_user_modified, user_modified_fields, planned_date, status = review
        print(f"\nReview ID: {review_id}")
        print(f"  Deliverables: {deliverables}")
        print(f"  billing_amount: {billing_amount}")
        print(f"  fee_amount: {fee_amount}")
        print(f"  is_user_modified: {is_user_modified}")
        print(f"  user_modified_fields: {user_modified_fields}")
        print(f"  Status: {status}")
        print(f"  Planned Date: {planned_date}")
    
    # Get items for this service
    cursor.execute(f"""
    SELECT 
        {ServiceItems.ITEM_ID},
        {ServiceItems.TITLE},
        {ServiceItems.FEE_AMOUNT},
        {ServiceItems.IS_USER_MODIFIED},
        {ServiceItems.USER_MODIFIED_FIELDS},
        {ServiceItems.STATUS}
    FROM {ServiceItems.TABLE}
    WHERE {ServiceItems.SERVICE_ID} = ?
    ORDER BY {ServiceItems.CREATED_AT}
    """, [service_id])
    
    items = cursor.fetchall()
    
    if items:
        print(f"\n📦 ITEMS ({len(items)} found)")
        print("-" * 80)
        for item in items:
            item_id, title, fee_amount, is_user_modified, user_modified_fields, status = item
            print(f"\nItem ID: {item_id}")
            print(f"  Title: {title}")
            print(f"  fee_amount: {fee_amount}")
            print(f"  is_user_modified: {is_user_modified}")
            print(f"  user_modified_fields: {user_modified_fields}")
            print(f"  Status: {status}")
    else:
        print(f"\n📦 ITEMS: None found for this service")

print("\n" + "="*80)
print("Now test the finance endpoint for this project...")
print("="*80)

# Test finance endpoint
from services.financial_data_service import FinancialDataService

result = FinancialDataService.get_line_items(project_id)

if 'error' in result:
    print(f"\n❌ ERROR: {result['error']}")
else:
    print(f"\n✅ Finance endpoint returned successfully")
    print(f"Total Fee: ${result['totals']['total_fee']:,.2f}")
    print(f"Line Items: {len(result['line_items'])}")
    
    # Find items for this service
    service_items = [item for item in result['line_items'] if item['service_id'] == service_id]
    
    print(f"\n💰 LINE ITEMS FOR SERVICE {service_code}")
    print("-" * 80)
    for item in service_items:
        print(f"\n{item['type'].upper()} {item['id']}")
        print(f"  Title: {item['title']}")
        print(f"  Fee: ${item['fee']:,.2f}")
        print(f"  Fee Source: {item['fee_source']}")
        print(f"  Invoice Month: {item['invoice_month']}")

print("\n" + "="*80)
print("FEE TRACE COMPLETE")
print("="*80)
