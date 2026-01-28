#!/usr/bin/env python3
"""Check what data exists."""

import sys
sys.path.insert(0, '.')

from database_pool import get_db_connection
from constants.schema import ProjectServices, ServiceReviews, ServiceItems

with get_db_connection() as conn:
    cursor = conn.cursor()
    
    # Count reviews
    cursor.execute(f'SELECT COUNT(*) FROM {ServiceReviews.TABLE}')
    review_count = cursor.fetchone()[0]
    print(f"Total reviews in DB: {review_count}")
    
    # Count items
    cursor.execute(f'SELECT COUNT(*) FROM {ServiceItems.TABLE}')
    item_count = cursor.fetchone()[0]
    print(f"Total items in DB: {item_count}")
    
    # Find services with agreed_fee
    cursor.execute(f"""
    SELECT project_id, service_id, service_code, agreed_fee, review_count_planned
    FROM {ProjectServices.TABLE}
    WHERE agreed_fee > 0
    ORDER BY project_id
    """)
    
    services = cursor.fetchall()
    print(f"\nServices with agreed_fee > 0: {len(services)}")
    for svc in services[:10]:
        print(f"  Project {svc[0]}, Service {svc[1]} ({svc[2]}): agreed_fee=${svc[3]}, planned={svc[4]}")
