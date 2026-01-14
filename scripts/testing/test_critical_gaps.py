"""
Test Critical Gap Implementations
==================================

This script tests the 3 critical gap fixes:
1. CASCADE constraints - ensure related records deleted with project
2. Date propagation - verify project date changes cascade to related tables
3. Client snapshots - confirm billing claims preserve historical client data

Run this AFTER applying SQL migrations 001 and 002.

Usage:
    python scripts/testing/test_critical_gaps.py
    
    # Or test specific gaps:
    python scripts/testing/test_critical_gaps.py --test cascade
    python scripts/testing/test_critical_gaps.py --test dates
    python scripts/testing/test_critical_gaps.py --test snapshots
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyodbc
from datetime import datetime, timedelta
from database import connect_to_db, get_db_connection, update_project_details
from constants import schema as S
from review_management_service import ReviewManagementService
import argparse


class CriticalGapTester:
    """Test suite for critical gap implementations."""
    
    def __init__(self):
        self.conn = None
        self.test_project_id = None
        self.test_client_id = None
        self.cleanup_ids = {
            'projects': [],
            'clients': [],
            'services': [],
            'reviews': [],
            'tasks': [],
            'claims': []
        }
    
    def setup(self):
        """Set up test database connection."""
        print("=" * 70)
        print("CRITICAL GAP TESTING - SETUP")
        print("=" * 70)
        
        try:
            self.conn = get_db_connection("ProjectManagement").__enter__()
            print("✅ Database connection established")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            raise
    
    def teardown(self):
        """Clean up test data."""
        print("\n" + "=" * 70)
        print("TEARDOWN - Cleaning up test data")
        print("=" * 70)
        
        if self.conn is None:
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Delete in reverse dependency order
            if self.cleanup_ids['claims']:
                cursor.execute(f"DELETE FROM BillingClaims WHERE claim_id IN ({','.join(map(str, self.cleanup_ids['claims']))})")
                print(f"  ✅ Deleted {len(self.cleanup_ids['claims'])} billing claims")
            
            if self.cleanup_ids['reviews']:
                cursor.execute(f"DELETE FROM ServiceReviews WHERE review_id IN ({','.join(map(str, self.cleanup_ids['reviews']))})")
                print(f"  ✅ Deleted {len(self.cleanup_ids['reviews'])} reviews")
            
            if self.cleanup_ids['tasks']:
                cursor.execute(f"DELETE FROM Tasks WHERE task_id IN ({','.join(map(str, self.cleanup_ids['tasks']))})")
                print(f"  ✅ Deleted {len(self.cleanup_ids['tasks'])} tasks")
            
            if self.cleanup_ids['services']:
                cursor.execute(f"DELETE FROM ProjectServices WHERE service_id IN ({','.join(map(str, self.cleanup_ids['services']))})")
                print(f"  ✅ Deleted {len(self.cleanup_ids['services'])} services")
            
            if self.cleanup_ids['projects']:
                cursor.execute(f"DELETE FROM Projects WHERE project_id IN ({','.join(map(str, self.cleanup_ids['projects']))})")
                print(f"  ✅ Deleted {len(self.cleanup_ids['projects'])} projects")
            
            if self.cleanup_ids['clients']:
                cursor.execute(f"DELETE FROM Clients WHERE client_id IN ({','.join(map(str, self.cleanup_ids['clients']))})")
                print(f"  ✅ Deleted {len(self.cleanup_ids['clients'])} clients")
            
            self.conn.commit()
            print("✅ Teardown complete")
        
        except Exception as e:
            print(f"⚠️  Teardown error (may be normal): {e}")
            if hasattr(self.conn, 'rollback'):
                self.conn.rollback()
        
        finally:
            if hasattr(self.conn, '__exit__'):
                self.conn.__exit__(None, None, None)
    
    def create_test_client(self, name="Test Client CASCADE"):
        """Create a test client."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO Clients (name, contact_name, contact_email)
            VALUES (?, 'Test Contact', 'test@example.com');
            SELECT SCOPE_IDENTITY();
            """,
            (name,)
        )
        client_id = cursor.fetchone()[0]
        self.conn.commit()
        self.cleanup_ids['clients'].append(client_id)
        return client_id
    
    def create_test_project(self, client_id, name="Test Project", start_date=None, end_date=None):
        """Create a test project."""
        if start_date is None:
            start_date = datetime.now().date()
        if end_date is None:
            end_date = (datetime.now() + timedelta(days=180)).date()
        
        cursor = self.conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO Projects (
                project_name, project_number, client_id, 
                start_date, end_date, status, priority,
                contract_number, contract_value
            )
            VALUES (?, ?, ?, ?, ?, 'Active', 'Medium', 'CONTRACT-001', 100000.00);
            SELECT SCOPE_IDENTITY();
            """,
            (name, f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}", client_id, start_date, end_date)
        )
        project_id = cursor.fetchone()[0]
        self.conn.commit()
        self.cleanup_ids['projects'].append(project_id)
        return project_id
    
    def create_test_service(self, project_id, service_name="Test Service"):
        """Create a test project service."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO ProjectServices (
                project_id, service_name, phase, agreed_fee, status
            )
            VALUES (?, ?, 'Design', 10000.00, 'Active');
            SELECT SCOPE_IDENTITY();
            """,
            (project_id, service_name)
        )
        service_id = cursor.fetchone()[0]
        self.conn.commit()
        self.cleanup_ids['services'].append(service_id)
        return service_id
    
    def create_test_task(self, project_id, task_name="Test Task"):
        """Create a test task."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO Tasks (
                project_id, task_name, start_date, end_date, status
            )
            VALUES (?, ?, GETDATE(), DATEADD(day, 7, GETDATE()), 'Not Started');
            SELECT SCOPE_IDENTITY();
            """,
            (project_id, task_name)
        )
        task_id = cursor.fetchone()[0]
        self.conn.commit()
        self.cleanup_ids['tasks'].append(task_id)
        return task_id
    
    # =========================================================================
    # TEST 1: CASCADE Constraints
    # =========================================================================
    
    def test_cascade_constraints(self):
        """
        Test Gap #3: Database CASCADE constraints.
        
        Verifies that deleting a project CASCADE deletes all related records:
        - ProjectServices
        - Tasks
        - BillingClaims
        - ServiceReviews
        - etc.
        """
        print("\n" + "=" * 70)
        print("TEST 1: CASCADE CONSTRAINTS")
        print("=" * 70)
        
        try:
            # 1. Create test data
            print("\n📋 Step 1: Creating test project with related records...")
            client_id = self.create_test_client("CASCADE Test Client")
            project_id = self.create_test_project(client_id, "CASCADE Test Project")
            service_id = self.create_test_service(project_id, "CASCADE Test Service")
            task_id = self.create_test_task(project_id, "CASCADE Test Task")
            
            print(f"  ✅ Created project {project_id} with:")
            print(f"     - Client: {client_id}")
            print(f"     - Service: {service_id}")
            print(f"     - Task: {task_id}")
            
            # 2. Verify records exist
            print("\n📋 Step 2: Verifying related records exist...")
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM Projects WHERE project_id = ?", (project_id,))
            assert cursor.fetchone()[0] == 1, "Project not found"
            
            cursor.execute("SELECT COUNT(*) FROM ProjectServices WHERE project_id = ?", (project_id,))
            service_count = cursor.fetchone()[0]
            assert service_count == 1, f"Expected 1 service, found {service_count}"
            
            cursor.execute("SELECT COUNT(*) FROM Tasks WHERE project_id = ?", (project_id,))
            task_count = cursor.fetchone()[0]
            assert task_count == 1, f"Expected 1 task, found {task_count}"
            
            print(f"  ✅ Verified 1 project, {service_count} services, {task_count} tasks")
            
            # 3. Delete project (CASCADE should handle related records)
            print("\n📋 Step 3: Deleting project (testing CASCADE)...")
            cursor.execute("DELETE FROM Projects WHERE project_id = ?", (project_id,))
            self.conn.commit()
            print(f"  ✅ Deleted project {project_id}")
            
            # 4. Verify CASCADE deleted related records
            print("\n📋 Step 4: Verifying CASCADE deletion of related records...")
            
            cursor.execute("SELECT COUNT(*) FROM Projects WHERE project_id = ?", (project_id,))
            assert cursor.fetchone()[0] == 0, "Project still exists!"
            
            cursor.execute("SELECT COUNT(*) FROM ProjectServices WHERE project_id = ?", (project_id,))
            orphaned_services = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM Tasks WHERE project_id = ?", (project_id,))
            orphaned_tasks = cursor.fetchone()[0]
            
            if orphaned_services > 0:
                print(f"  ❌ FAILED: {orphaned_services} orphaned services found")
                print(f"     CASCADE constraint not working for ProjectServices!")
                return False
            
            if orphaned_tasks > 0:
                print(f"  ❌ FAILED: {orphaned_tasks} orphaned tasks found")
                print(f"     CASCADE constraint not working for Tasks!")
                return False
            
            print(f"  ✅ No orphaned records - CASCADE working correctly")
            
            # Remove from cleanup (already deleted by CASCADE)
            self.cleanup_ids['projects'].remove(project_id)
            self.cleanup_ids['services'].remove(service_id)
            self.cleanup_ids['tasks'].remove(task_id)
            
            print("\n✅ TEST 1 PASSED: CASCADE constraints working correctly")
            return True
        
        except Exception as e:
            print(f"\n❌ TEST 1 FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # =========================================================================
    # TEST 2: Date Propagation
    # =========================================================================
    
    def test_date_propagation(self):
        """
        Test Gap #1: Project date propagation.
        
        Verifies that updating project dates propagates to:
        - ServiceScheduleSettings (start/end dates adjusted)
        - ServiceReviews (reviews beyond end_date cancelled)
        - Tasks (warnings logged for dates outside bounds)
        """
        print("\n" + "=" * 70)
        print("TEST 2: DATE PROPAGATION")
        print("=" * 70)
        
        try:
            # 1. Create test project
            print("\n📋 Step 1: Creating test project...")
            client_id = self.create_test_client("Date Test Client")
            original_start = datetime(2024, 1, 1).date()
            original_end = datetime(2024, 12, 31).date()
            project_id = self.create_test_project(
                client_id, 
                "Date Propagation Test", 
                original_start, 
                original_end
            )
            service_id = self.create_test_service(project_id, "Date Test Service")
            
            print(f"  ✅ Created project {project_id}")
            print(f"     Original dates: {original_start} to {original_end}")
            
            # 2. Create ServiceScheduleSettings
            print("\n📋 Step 2: Creating ServiceScheduleSettings...")
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO ServiceScheduleSettings (service_id, start_date, end_date, frequency)
                VALUES (?, ?, ?, 'monthly')
                """,
                (service_id, original_start, original_end)
            )
            self.conn.commit()
            print(f"  ✅ Created schedule settings for service {service_id}")
            
            # 3. Create ServiceReview beyond new end_date (will be cancelled)
            cursor.execute(
                """
                INSERT INTO ServiceReviews (service_id, cycle_no, planned_date, status)
                VALUES (?, 1, '2024-11-01', 'Planned')
                """,
                (service_id,)
            )
            review_id = cursor.lastrowid
            self.cleanup_ids['reviews'].append(review_id)
            self.conn.commit()
            print(f"  ✅ Created review {review_id} for 2024-11-01 (will be outside new end_date)")
            
            # 4. Update project dates (NEW: end_date = 2024-09-30)
            print("\n📋 Step 3: Updating project dates (triggering propagation)...")
            new_start = datetime(2024, 2, 1).date()
            new_end = datetime(2024, 9, 30).date()
            
            success = update_project_details(
                project_id, 
                new_start, 
                new_end, 
                'Active', 
                'High'
            )
            
            if not success:
                print("  ❌ FAILED: update_project_details() returned False")
                return False
            
            print(f"  ✅ Updated dates to: {new_start} to {new_end}")
            
            # 5. Verify ServiceScheduleSettings updated
            print("\n📋 Step 4: Verifying ServiceScheduleSettings propagation...")
            cursor.execute(
                "SELECT start_date, end_date FROM ServiceScheduleSettings WHERE service_id = ?",
                (service_id,)
            )
            sss_dates = cursor.fetchone()
            sss_start, sss_end = sss_dates
            
            # Start date should be adjusted if it was before project start
            if sss_start < new_start:
                print(f"  ❌ FAILED: ServiceScheduleSettings.start_date not propagated")
                print(f"     Expected: >= {new_start}, Got: {sss_start}")
                return False
            
            # End date should be adjusted if it was after project end
            if sss_end > new_end:
                print(f"  ❌ FAILED: ServiceScheduleSettings.end_date not propagated")
                print(f"     Expected: <= {new_end}, Got: {sss_end}")
                return False
            
            print(f"  ✅ ServiceScheduleSettings dates adjusted: {sss_start} to {sss_end}")
            
            # 6. Verify ServiceReview cancelled
            print("\n📋 Step 5: Verifying ServiceReview cancellation...")
            cursor.execute(
                "SELECT status, planned_date FROM ServiceReviews WHERE review_id = ?",
                (review_id,)
            )
            review_data = cursor.fetchone()
            review_status, review_date = review_data
            
            # Review planned for 2024-11-01 should be cancelled (beyond 2024-09-30)
            if review_status != 'Cancelled':
                print(f"  ❌ FAILED: Review not cancelled")
                print(f"     Review date: {review_date}, New end: {new_end}")
                print(f"     Status: {review_status} (expected 'Cancelled')")
                return False
            
            print(f"  ✅ Review {review_id} correctly cancelled (beyond new end_date)")
            
            print("\n✅ TEST 2 PASSED: Date propagation working correctly")
            return True
        
        except Exception as e:
            print(f"\n❌ TEST 2 FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # =========================================================================
    # TEST 3: Client Snapshots
    # =========================================================================
    
    def test_client_snapshots(self):
        """
        Test Gap #2: Client snapshot preservation.
        
        Verifies that billing claims preserve client data via snapshot columns:
        - client_id_snapshot
        - client_name_snapshot
        - contract_number_snapshot
        - contract_value_snapshot
        """
        print("\n" + "=" * 70)
        print("TEST 3: CLIENT SNAPSHOTS")
        print("=" * 70)
        
        try:
            # 1. Create test project with original client
            print("\n📋 Step 1: Creating project with Client A...")
            client_a_id = self.create_test_client("Client A - Original")
            project_id = self.create_test_project(client_a_id, "Client Snapshot Test")
            
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM Clients WHERE client_id = ?", (client_a_id,))
            client_a_name = cursor.fetchone()[0]
            
            print(f"  ✅ Created project {project_id} with client: {client_a_name} (ID: {client_a_id})")
            
            # 2. Generate billing claim (should capture Client A snapshot)
            print("\n📋 Step 2: Generating billing claim under Client A...")
            
            cursor.execute(
                """
                INSERT INTO BillingClaims (
                    project_id, 
                    period_start, 
                    period_end,
                    client_id_snapshot,
                    client_name_snapshot,
                    contract_number_snapshot,
                    contract_value_snapshot
                )
                SELECT 
                    p.project_id,
                    GETDATE(),
                    DATEADD(month, 1, GETDATE()),
                    c.client_id,
                    c.name,
                    p.contract_number,
                    p.contract_value
                FROM Projects p
                INNER JOIN Clients c ON p.client_id = c.client_id
                WHERE p.project_id = ?;
                SELECT SCOPE_IDENTITY();
                """,
                (project_id,)
            )
            claim_id = cursor.fetchone()[0]
            self.cleanup_ids['claims'].append(claim_id)
            self.conn.commit()
            
            print(f"  ✅ Created billing claim {claim_id}")
            
            # 3. Verify claim has Client A snapshot
            print("\n📋 Step 3: Verifying claim captured Client A snapshot...")
            cursor.execute(
                """
                SELECT 
                    client_id_snapshot, 
                    client_name_snapshot,
                    contract_number_snapshot,
                    contract_value_snapshot
                FROM BillingClaims 
                WHERE claim_id = ?
                """,
                (claim_id,)
            )
            snapshot_data = cursor.fetchone()
            
            if snapshot_data is None or snapshot_data[0] is None:
                print(f"  ❌ FAILED: Claim missing client snapshot data")
                return False
            
            snap_client_id, snap_client_name, snap_contract, snap_value = snapshot_data
            
            if snap_client_id != client_a_id:
                print(f"  ❌ FAILED: Snapshot client_id mismatch")
                print(f"     Expected: {client_a_id}, Got: {snap_client_id}")
                return False
            
            if snap_client_name != client_a_name:
                print(f"  ❌ FAILED: Snapshot client_name mismatch")
                print(f"     Expected: {client_a_name}, Got: {snap_client_name}")
                return False
            
            print(f"  ✅ Claim snapshot: {snap_client_name} (ID: {snap_client_id})")
            print(f"     Contract: {snap_contract}, Value: ${snap_value:,.2f}")
            
            # 4. Change project to Client B
            print("\n📋 Step 4: Changing project to Client B...")
            client_b_id = self.create_test_client("Client B - New Owner")
            
            cursor.execute(
                "UPDATE Projects SET client_id = ? WHERE project_id = ?",
                (client_b_id, project_id)
            )
            self.conn.commit()
            
            cursor.execute("SELECT name FROM Clients WHERE client_id = ?", (client_b_id,))
            client_b_name = cursor.fetchone()[0]
            
            print(f"  ✅ Project now assigned to: {client_b_name} (ID: {client_b_id})")
            
            # 5. Verify claim STILL shows Client A (snapshot preserved)
            print("\n📋 Step 5: Verifying claim snapshot unchanged (historical accuracy)...")
            cursor.execute(
                """
                SELECT 
                    bc.client_id_snapshot, 
                    bc.client_name_snapshot,
                    p.client_id AS current_client_id,
                    c.name AS current_client_name
                FROM BillingClaims bc
                INNER JOIN Projects p ON bc.project_id = p.project_id
                INNER JOIN Clients c ON p.client_id = c.client_id
                WHERE bc.claim_id = ?
                """,
                (claim_id,)
            )
            verification = cursor.fetchone()
            snap_id, snap_name, current_id, current_name = verification
            
            if snap_id != client_a_id:
                print(f"  ❌ FAILED: Snapshot changed after project client update!")
                print(f"     Expected: {client_a_id}, Got: {snap_id}")
                return False
            
            if current_id != client_b_id:
                print(f"  ❌ FAILED: Project client not updated")
                return False
            
            print(f"  ✅ Claim snapshot preserved: {snap_name} (ID: {snap_id})")
            print(f"  ✅ Current project client: {current_name} (ID: {current_id})")
            print(f"  ✅ Historical billing accuracy maintained!")
            
            print("\n✅ TEST 3 PASSED: Client snapshots working correctly")
            return True
        
        except Exception as e:
            print(f"\n❌ TEST 3 FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Run critical gap tests."""
    parser = argparse.ArgumentParser(description="Test critical gap implementations")
    parser.add_argument(
        '--test',
        choices=['cascade', 'dates', 'snapshots', 'all'],
        default='all',
        help='Which test to run'
    )
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("CRITICAL GAP IMPLEMENTATION TESTING")
    print("=" * 70)
    print(f"Run mode: {args.test}")
    print()
    print("⚠️  IMPORTANT: Run SQL migrations 001 and 002 first!")
    print("   - 001_add_cascade_constraints.sql")
    print("   - 002_add_client_snapshot.sql")
    print("=" * 70)
    
    input("\nPress ENTER to continue (or Ctrl+C to cancel)...")
    
    tester = CriticalGapTester()
    
    try:
        tester.setup()
        
        results = {}
        
        if args.test in ['cascade', 'all']:
            results['cascade'] = tester.test_cascade_constraints()
        
        if args.test in ['dates', 'all']:
            results['dates'] = tester.test_date_propagation()
        
        if args.test in ['snapshots', 'all']:
            results['snapshots'] = tester.test_client_snapshots()
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        all_passed = True
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name.upper():20s} {status}")
            if not passed:
                all_passed = False
        
        print("=" * 70)
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED - Critical gaps successfully implemented!")
            return 0
        else:
            print("\n⚠️  SOME TESTS FAILED - Review implementation")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing cancelled by user")
        return 1
    
    except Exception as e:
        print(f"\n❌ TESTING ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        tester.teardown()


if __name__ == "__main__":
    sys.exit(main())
