#!/usr/bin/env python
"""
Verification script for Deliverables PATCH endpoint.

Tests the PATCH /api/projects/<project_id>/reviews endpoint with all 5 fields:
- due_date (DATE/nullable)
- status (nvarchar)
- invoice_reference (nvarchar)
- invoice_date (DATE/nullable)
- is_billed (bit)

Usage:
    python tools/verify_deliverables_update.py [--project-id PROJECT_ID] [--service-id SERVICE_ID] [--review-id REVIEW_ID]
    
    Or use discovery mode to find test data:
    python tools/verify_deliverables_update.py --discover

Example:
    python tools/verify_deliverables_update.py --project-id 1 --service-id 5 --review-id 10
"""

import sys
import os
import json
import argparse
import subprocess
from datetime import datetime, date, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection, get_project_reviews
from constants.schema import ServiceReviews as S_SR, ProjectServices as S_PS, Projects as S_P

BASE_URL = "http://localhost:5000"


def discover_test_data():
    """Discover valid project/service/review IDs for testing."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Find a project with reviews
            cursor.execute(f"""
                SELECT TOP 1 p.{S_P.ID}, s.{S_PS.SERVICE_ID}, sr.{S_SR.REVIEW_ID}, s.{S_PS.SERVICE_NAME}
                FROM {S_P.TABLE} p
                JOIN {S_PS.TABLE} s ON p.{S_P.ID} = s.{S_PS.PROJECT_ID}
                JOIN {S_SR.TABLE} sr ON s.{S_PS.SERVICE_ID} = sr.{S_SR.SERVICE_ID}
                ORDER BY p.{S_P.ID} DESC
            """)
            row = cursor.fetchone()
            if row:
                return {
                    "project_id": row[0],
                    "service_id": row[1],
                    "review_id": row[2],
                    "service_name": row[3]
                }
    except Exception as e:
        print(f"Error discovering test data: {e}")
    return None


def fetch_review_before(project_id, service_id, review_id):
    """Fetch review state before updates."""
    try:
        data = get_project_reviews(project_id, service_id=service_id, limit=1000)
        if data and data.get('items'):
            for item in data['items']:
                if item['review_id'] == review_id:
                    return item
    except Exception as e:
        print(f"Error fetching review: {e}")
    return None


def run_curl_test(project_id, service_id, review_id, field, value, description):
    """Run a PATCH request via curl and return parsed response."""
    url = f"{BASE_URL}/api/projects/{project_id}/services/{service_id}/reviews/{review_id}"
    payload = {field: value}
    
    cmd = [
        "curl", "-s",
        "-X", "PATCH",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
        url
    ]
    
    print(f"\n{'='*70}")
    print(f"Test: {description}")
    print(f"URL: PATCH {url}")
    print(f"Request: {json.dumps(payload, indent=2)}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"❌ CURL Error: {result.stderr}")
            return None
        
        response_text = result.stdout.strip()
        try:
            response = json.loads(response_text)
            return response
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {response_text[:200]}")
            return None
    except subprocess.TimeoutExpired:
        print(f"❌ Request timeout")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def verify_field_update(response, field, expected_value, field_label):
    """Verify that the field in the response matches expected value."""
    if not response:
        print(f"❌ No response received")
        return False
    
    # Handle field mapping (camelCase to snake_case)
    response_field = field
    actual_value = response.get(response_field)
    
    # Special handling for boolean fields
    if field == 'is_billed':
        expected = bool(expected_value)
        actual = bool(actual_value)
        match = expected == actual
    else:
        match = actual_value == expected_value or (
            expected_value is None and actual_value is None
        )
    
    if match:
        print(f"✅ {field_label}: {actual_value}")
        return True
    else:
        print(f"❌ {field_label}: expected {expected_value}, got {actual_value}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Verify Deliverables PATCH endpoint updates"
    )
    parser.add_argument(
        "--discover", action="store_true",
        help="Discover test data from database"
    )
    parser.add_argument(
        "--project-id", type=int,
        help="Project ID to test"
    )
    parser.add_argument(
        "--service-id", type=int,
        help="Service ID to test"
    )
    parser.add_argument(
        "--review-id", type=int,
        help="Review ID to test"
    )
    
    args = parser.parse_args()
    
    # Discover or validate IDs
    if args.discover or not all([args.project_id, args.service_id, args.review_id]):
        print("Discovering test data...")
        test_data = discover_test_data()
        if not test_data:
            print("❌ No test data found. Please provide --project-id, --service-id, --review-id")
            return 1
        
        project_id = test_data["project_id"]
        service_id = test_data["service_id"]
        review_id = test_data["review_id"]
        
        print(f"✅ Found: Project {project_id}, Service {service_id} ({test_data['service_name']}), Review {review_id}")
    else:
        project_id = args.project_id
        service_id = args.service_id
        review_id = args.review_id
    
    # Fetch initial state
    print(f"\nFetching initial review state...")
    review_before = fetch_review_before(project_id, service_id, review_id)
    if not review_before:
        print("❌ Could not fetch review")
        return 1
    
    print(f"✅ Review found: {json.dumps(review_before, indent=2, default=str)}")
    
    # Test 1: Update due_date
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    response = run_curl_test(
        project_id, service_id, review_id,
        'due_date', tomorrow,
        "Update due_date to tomorrow"
    )
    if response:
        verify_field_update(response, 'due_date', tomorrow, "Due Date")
    
    # Test 2: Update status
    response = run_curl_test(
        project_id, service_id, review_id,
        'status', 'in-progress',
        "Update status to 'in-progress'"
    )
    if response:
        verify_field_update(response, 'status', 'in-progress', "Status")
    
    # Test 3: Update invoice_reference
    invoice_ref = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    response = run_curl_test(
        project_id, service_id, review_id,
        'invoice_reference', invoice_ref,
        "Update invoice_reference"
    )
    if response:
        verify_field_update(response, 'invoice_reference', invoice_ref, "Invoice Reference")
    
    # Test 4: Update invoice_date
    today = datetime.now().strftime('%Y-%m-%d')
    response = run_curl_test(
        project_id, service_id, review_id,
        'invoice_date', today,
        "Update invoice_date to today"
    )
    if response:
        verify_field_update(response, 'invoice_date', today, "Invoice Date")
    
    # Test 5: Update is_billed to true
    response = run_curl_test(
        project_id, service_id, review_id,
        'is_billed', True,
        "Set is_billed to true"
    )
    if response:
        verify_field_update(response, 'is_billed', True, "Is Billed")
    
    # Test 6: Update is_billed to false
    response = run_curl_test(
        project_id, service_id, review_id,
        'is_billed', False,
        "Set is_billed to false"
    )
    if response:
        verify_field_update(response, 'is_billed', False, "Is Billed")
    
    # Test 7: Clear invoice_date (null)
    response = run_curl_test(
        project_id, service_id, review_id,
        'invoice_date', None,
        "Clear invoice_date (set to null)"
    )
    if response:
        verify_field_update(response, 'invoice_date', None, "Invoice Date")
    
    # Test 8: Clear due_date (null)
    response = run_curl_test(
        project_id, service_id, review_id,
        'due_date', None,
        "Clear due_date (set to null)"
    )
    if response:
        verify_field_update(response, 'due_date', None, "Due Date")
    
    # Test 9: Multiple fields in one update
    payload_multi = {
        'status': 'completed',
        'is_billed': True,
        'invoice_reference': f"FINAL-{datetime.now().strftime('%Y%m%d')}"
    }
    url = f"{BASE_URL}/api/projects/{project_id}/services/{service_id}/reviews/{review_id}"
    cmd = [
        "curl", "-s",
        "-X", "PATCH",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload_multi),
        url
    ]
    print(f"\n{'='*70}")
    print(f"Test: Multiple fields in one request")
    print(f"Request: {json.dumps(payload_multi, indent=2)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            response = json.loads(result.stdout.strip())
            verify_field_update(response, 'status', 'completed', "Status")
            verify_field_update(response, 'is_billed', True, "Is Billed")
            verify_field_update(response, 'invoice_reference', payload_multi['invoice_reference'], "Invoice Reference")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n{'='*70}")
    print("✅ All tests completed. Check results above.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
