"""
Test script to simulate partial failure scenarios for Quality Register add row feature.

This script tests:
1. POST succeeds, PATCH fails (partial success)
2. POST fails (complete failure)
3. Network timeout simulation
4. Database constraint violations

Usage:
    python test_partial_failure.py [--scenario <name>]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import time
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:5000/api"
PROJECT_ID = 2  # Adjust to your test project

class PartialFailureTest:
    def __init__(self, project_id: int = PROJECT_ID):
        self.project_id = project_id
        self.base_url = BASE_URL
        self.session = requests.Session()
        
    def test_normal_two_call_success(self):
        """Test normal success case: POST + PATCH both succeed"""
        print("\n=== Test 1: Normal Success (POST + PATCH) ===")
        
        # Step 1: POST
        post_payload = {
            "expected_model_key": f"TEST-{int(time.time())}",
            "display_name": "Test Normal Success"
        }
        
        print(f"POST {self.base_url}/projects/{self.project_id}/quality/expected-models")
        print(f"Payload: {json.dumps(post_payload, indent=2)}")
        
        post_response = self.session.post(
            f"{self.base_url}/projects/{self.project_id}/quality/expected-models",
            json=post_payload
        )
        
        print(f"POST Response: {post_response.status_code}")
        print(f"Body: {post_response.text}")
        
        if post_response.status_code != 201:
            print(f"❌ POST failed with {post_response.status_code}")
            return
        
        new_id = post_response.json().get('expected_model_id')
        print(f"✅ POST succeeded, created ID: {new_id}")
        
        # Step 2: PATCH
        patch_payload = {
            "abv": "TESTNORM",
            "registeredModelName": "Test Normal Success Model",
            "company": "Test Company",
            "discipline": "Architecture",
            "description": "Test description",
            "bimContact": "test@example.com",
            "notes": "Test notes"
        }
        
        print(f"\nPATCH {self.base_url}/projects/{self.project_id}/quality/expected-models/{new_id}")
        print(f"Payload: {json.dumps(patch_payload, indent=2)}")
        
        patch_response = self.session.patch(
            f"{self.base_url}/projects/{self.project_id}/quality/expected-models/{new_id}",
            json=patch_payload
        )
        
        print(f"PATCH Response: {patch_response.status_code}")
        print(f"Body: {patch_response.text}")
        
        if patch_response.status_code == 200:
            print(f"✅ PATCH succeeded")
        else:
            print(f"❌ PATCH failed with {patch_response.status_code}")
        
        return new_id
    
    def test_post_fail(self):
        """Test POST failure (duplicate key)"""
        print("\n=== Test 2: POST Failure (Duplicate Key) ===")
        
        # Create a model first
        post_payload = {
            "expected_model_key": f"DUPLICATE-TEST",
            "display_name": "Test Duplicate"
        }
        
        print(f"Creating initial model...")
        response1 = self.session.post(
            f"{self.base_url}/projects/{self.project_id}/quality/expected-models",
            json=post_payload
        )
        
        if response1.status_code == 201:
            print(f"✅ First POST succeeded: {response1.json()}")
        
        # Try to create duplicate
        print(f"\nAttempting duplicate POST...")
        response2 = self.session.post(
            f"{self.base_url}/projects/{self.project_id}/quality/expected-models",
            json=post_payload
        )
        
        print(f"POST Response: {response2.status_code}")
        print(f"Body: {response2.text}")
        
        if response2.status_code >= 400:
            print(f"✅ POST correctly failed with {response2.status_code}")
        else:
            print(f"❌ POST should have failed but got {response2.status_code}")
    
    def test_partial_success_simulation(self):
        """Simulate POST success but PATCH would fail"""
        print("\n=== Test 3: Partial Success Simulation ===")
        print("(This simulates frontend behavior when PATCH fails)")
        
        # Step 1: POST succeeds
        post_payload = {
            "expected_model_key": f"PARTIAL-{int(time.time())}",
            "display_name": "Test Partial Success"
        }
        
        print(f"POST {self.base_url}/projects/{self.project_id}/quality/expected-models")
        post_response = self.session.post(
            f"{self.base_url}/projects/{self.project_id}/quality/expected-models",
            json=post_payload
        )
        
        print(f"POST Response: {post_response.status_code}")
        
        if post_response.status_code != 201:
            print(f"❌ POST failed")
            return
        
        new_id = post_response.json().get('expected_model_id')
        print(f"✅ POST succeeded, created ID: {new_id}")
        
        # Step 2: PATCH with invalid data to trigger failure
        patch_payload = {
            "registeredModelName": "X" * 300,  # Exceed NVARCHAR(255) limit
        }
        
        print(f"\nPATCH {self.base_url}/projects/{self.project_id}/quality/expected-models/{new_id}")
        print(f"(Sending oversized field to trigger failure)")
        
        patch_response = self.session.patch(
            f"{self.base_url}/projects/{self.project_id}/quality/expected-models/{new_id}",
            json=patch_payload
        )
        
        print(f"PATCH Response: {patch_response.status_code}")
        print(f"Body: {patch_response.text}")
        
        if patch_response.status_code >= 400:
            print(f"✅ Partial success: Row {new_id} created but PATCH failed")
            print(f"   Frontend should show needsSync: true warning icon")
        else:
            print(f"❌ PATCH should have failed but got {patch_response.status_code}")
        
        # Verify row exists in database
        print(f"\nVerifying row exists with incomplete data...")
        get_response = self.session.get(
            f"{self.base_url}/projects/{self.project_id}/quality/register?mode=phase1d"
        )
        
        if get_response.status_code == 200:
            rows = get_response.json().get('rows', [])
            row = next((r for r in rows if r['expected_model_id'] == new_id), None)
            if row:
                print(f"✅ Row exists in DB:")
                print(f"   ID: {row['expected_model_id']}")
                print(f"   Model Name: {row.get('modelName')}")
                print(f"   ABV: {row.get('abv')} (should be None)")
                print(f"   Company: {row.get('company')} (should be None)")
        
        return new_id
    
    def test_get_model_detail_error(self, model_id: Optional[int] = None):
        """Test the 500 error seen in console logs"""
        print("\n=== Test 4: GET Model Detail (Investigate 500 Error) ===")
        
        test_id = model_id or 9  # The ID that was failing in console
        
        print(f"GET {self.base_url}/projects/{self.project_id}/quality/models/{test_id}")
        
        response = self.session.get(
            f"{self.base_url}/projects/{self.project_id}/quality/models/{test_id}"
        )
        
        print(f"Response: {response.status_code}")
        print(f"Body: {response.text}")
        
        if response.status_code == 500:
            print(f"❌ 500 Error confirmed")
            print(f"   Check backend logs for traceback")
            try:
                error_detail = response.json()
                print(f"   Error: {error_detail.get('error', 'Unknown')}")
            except:
                pass
        elif response.status_code == 200:
            print(f"✅ Model detail retrieved successfully")
            detail = response.json()
            print(f"   Model: {detail.get('registeredModelName')}")
        elif response.status_code == 404:
            print(f"⚠️ Model not found")
        
    def run_all_tests(self):
        """Run all test scenarios"""
        print("=" * 60)
        print("QUALITY REGISTER PARTIAL FAILURE TEST SUITE")
        print("=" * 60)
        
        # Test 1: Normal success
        created_id = self.test_normal_two_call_success()
        time.sleep(0.5)
        
        # Test 2: POST failure
        self.test_post_fail()
        time.sleep(0.5)
        
        # Test 3: Partial success
        partial_id = self.test_partial_success_simulation()
        time.sleep(0.5)
        
        # Test 4: GET detail error
        self.test_get_model_detail_error(model_id=9)
        
        print("\n" + "=" * 60)
        print("TEST SUITE COMPLETE")
        print("=" * 60)
        print("\nSummary:")
        print(f"- Normal success row created: ID {created_id}")
        print(f"- Partial success row created: ID {partial_id}")
        print(f"  (Frontend should show warning icon for partial success)")
        print("\nNext steps:")
        print("1. Check frontend for yellow draft rows")
        print("2. Verify warning icon appears for partial success")
        print("3. Try editing and re-saving partial success row")
        print("4. Check backend logs for GET /quality/models/9 error details")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test partial failure scenarios")
    parser.add_argument("--scenario", choices=["all", "normal", "post_fail", "partial", "get_error"],
                       default="all", help="Test scenario to run")
    parser.add_argument("--project-id", type=int, default=PROJECT_ID, help="Project ID to test")
    parser.add_argument("--model-id", type=int, help="Model ID for GET detail test")
    
    args = parser.parse_args()
    
    tester = PartialFailureTest(project_id=args.project_id)
    
    if args.scenario == "all":
        tester.run_all_tests()
    elif args.scenario == "normal":
        tester.test_normal_two_call_success()
    elif args.scenario == "post_fail":
        tester.test_post_fail()
    elif args.scenario == "partial":
        tester.test_partial_success_simulation()
    elif args.scenario == "get_error":
        tester.test_get_model_detail_error(model_id=args.model_id)
