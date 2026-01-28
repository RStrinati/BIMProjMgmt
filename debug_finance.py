#!/usr/bin/env python
"""Debug financial data service."""

from constants.schema import ServiceReviews, ProjectServices, ServiceItems
from database_pool import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()
    query = f"""
    SELECT 
        sr.{ServiceReviews.REVIEW_ID} as id,
        'review' as type
    FROM {ServiceReviews.TABLE} sr
    WHERE sr.{ServiceReviews.PROJECT_ID} = @project_id
    """
    print("Review Query:")
    print(query)
    print("\nParams: {'project_id': 4}")
    try:
        cursor.execute(query, {'project_id': 4})
        print("✓ Reviews Query OK")
    except Exception as e:
        print(f"✗ Reviews Error: {e}")
        exit(1)
    
    # Now test items query
    cursor = conn.cursor()
    items_query = f"""
    SELECT 
        si.{ServiceItems.ITEM_ID} as id,
        'item' as type
    FROM {ServiceItems.TABLE} si
    WHERE si.{ServiceItems.PROJECT_ID} = @project_id
    """
    print("\nItems Query:")
    print(items_query)
    print("\nParams: {'project_id': 4}")
    try:
        cursor.execute(items_query, {'project_id': 4})
        print("✓ Items Query OK")
    except Exception as e:
        print(f"✗ Items Error: {e}")
        exit(1)

print("\n✓ All queries OK")
