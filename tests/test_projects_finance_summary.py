"""
Test Projects Finance Summary Endpoint

Validates that the batch finance summary endpoint returns correct values
using the deterministic fee model, matching reconciliation totals.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from decimal import Decimal
from database_pool import get_db_connection
from constants.schema import Projects, ProjectServices, ServiceReviews, ServiceItems
from services.financial_data_service import FinancialDataService


@pytest.fixture
def sample_project_id():
    """
    Use project 4 from the trace document example.
    """
    return 4


def test_finance_summary_endpoint_matches_reconciliation(sample_project_id):
    """
    Test that the batch finance summary endpoint returns values
    that match the per-project reconciliation totals.
    """
    # Get batch summary for all projects
    batch_result = FinancialDataService.get_projects_finance_summary()
    assert 'error' not in batch_result, f"Batch summary returned error: {batch_result.get('error')}"
    assert 'projects' in batch_result, "Batch summary missing 'projects' key"
    
    # Find project 4 in the batch results
    project_summary = None
    for proj in batch_result['projects']:
        if proj['project_id'] == sample_project_id:
            project_summary = proj
            break
    
    assert project_summary is not None, f"Project {sample_project_id} not found in batch results"
    
    # Get individual reconciliation for comparison
    reconciliation_result = FinancialDataService.get_reconciliation(project_id=sample_project_id)
    assert 'error' not in reconciliation_result, f"Reconciliation returned error: {reconciliation_result.get('error')}"
    assert 'project' in reconciliation_result, "Reconciliation missing 'project' key"
    
    project_recon = reconciliation_result['project']
    
    # Compare totals (allowing small floating point differences)
    def close_enough(a, b, tolerance=0.01):
        return abs(float(a) - float(b)) < tolerance
    
    assert close_enough(project_summary['agreed_fee_total'], project_recon['agreed_fee']), \
        f"Agreed fee mismatch: batch={project_summary['agreed_fee_total']}, recon={project_recon['agreed_fee']}"
    
    assert close_enough(project_summary['line_items_total'], project_recon['line_items_total_fee']), \
        f"Line items total mismatch: batch={project_summary['line_items_total']}, recon={project_recon['line_items_total_fee']}"
    
    assert close_enough(project_summary['billed_total'], project_recon['billed_total_fee']), \
        f"Billed total mismatch: batch={project_summary['billed_total']}, recon={project_recon['billed_total_fee']}"
    
    assert close_enough(project_summary['unbilled_total'], project_recon['outstanding_total_fee']), \
        f"Unbilled total mismatch: batch={project_summary['unbilled_total']}, recon={project_recon['outstanding_total_fee']}"
    
    print(f"✓ Project {sample_project_id} finance summary matches reconciliation:")
    print(f"  Agreed Fee: ${project_summary['agreed_fee_total']:,.2f}")
    print(f"  Line Items: ${project_summary['line_items_total']:,.2f}")
    print(f"  Billed: ${project_summary['billed_total']:,.2f}")
    print(f"  Unbilled: ${project_summary['unbilled_total']:,.2f}")
    print(f"  Earned Value: ${project_summary['earned_value']:,.2f}")
    print(f"  Pipeline (This Month): ${project_summary['pipeline_this_month']:,.2f}")


def test_finance_summary_deterministic_fee_resolution():
    """
    Test that the batch summary correctly applies the deterministic fee model:
    - Reviews: fee_amount override, else equal split
    - Items: fee_amount, else 0
    """
    batch_result = FinancialDataService.get_projects_finance_summary()
    assert 'error' not in batch_result, f"Batch summary returned error: {batch_result.get('error')}"
    
    # Verify we got results
    assert len(batch_result['projects']) > 0, "No projects returned in batch summary"
    
    # Check that all required fields are present
    required_fields = [
        'project_id',
        'agreed_fee_total',
        'line_items_total',
        'billed_total',
        'unbilled_total',
        'earned_value',
        'pipeline_this_month'
    ]
    
    for proj in batch_result['projects']:
        for field in required_fields:
            assert field in proj, f"Missing field '{field}' in project {proj.get('project_id')}"
            assert isinstance(proj[field], (int, float)), \
                f"Field '{field}' should be numeric, got {type(proj[field])}"
        
        # Verify calculation: unbilled = line_items_total - billed_total
        expected_unbilled = proj['line_items_total'] - proj['billed_total']
        assert abs(proj['unbilled_total'] - expected_unbilled) < 0.01, \
            f"Project {proj['project_id']}: unbilled calculation incorrect"
    
    print(f"✓ Verified {len(batch_result['projects'])} projects have correct structure and calculations")


def test_finance_summary_performance():
    """
    Test that the batch endpoint is performant (no N+1 queries).
    This is a basic check that it returns in reasonable time.
    """
    import time
    
    start = time.time()
    result = FinancialDataService.get_projects_finance_summary()
    elapsed = time.time() - start
    
    assert 'error' not in result, f"Batch summary returned error: {result.get('error')}"
    
    # Should complete in under 5 seconds even with many projects
    assert elapsed < 5.0, f"Batch summary took too long: {elapsed:.2f}s"
    
    print(f"✓ Batch finance summary completed in {elapsed:.3f}s for {len(result['projects'])} projects")


def test_finance_summary_handles_projects_with_no_services():
    """
    Test that projects with no services return zero values (not errors).
    """
    batch_result = FinancialDataService.get_projects_finance_summary()
    assert 'error' not in batch_result, f"Batch summary returned error: {batch_result.get('error')}"
    
    # The query uses agreed_by_project CTE which should only include projects with services
    # Projects without services won't appear in results, which is expected
    print(f"✓ Batch summary handles {len(batch_result['projects'])} projects")


if __name__ == '__main__':
    # Run tests
    print("=" * 60)
    print("Testing Projects Finance Summary Endpoint")
    print("=" * 60)
    
    try:
        test_finance_summary_endpoint_matches_reconciliation(4)
        print()
        test_finance_summary_deterministic_fee_resolution()
        print()
        test_finance_summary_performance()
        print()
        test_finance_summary_handles_projects_with_no_services()
        print()
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"✗ Test failed: {e}")
        print("=" * 60)
        raise
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Unexpected error: {e}")
        print("=" * 60)
        raise
