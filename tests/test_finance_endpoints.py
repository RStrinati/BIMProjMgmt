"""
Integration tests for Finance Endpoints

Tests the unified line-items and reconciliation endpoints without mocking database.
These tests verify the full data flow from database through fee resolution.

Note: Requires database to be running and accessible.
"""

import pytest
import json
from datetime import datetime, timedelta
from services.financial_data_service import FinancialDataService
from services.fee_resolver_service import FeeResolverService


class TestFinancialDataService:
    """Integration tests for FinancialDataService"""

    def test_get_line_items_returns_dict_with_expected_keys(self):
        """Line items endpoint returns expected structure"""
        # This test checks structure; real data depends on database state
        # Using project_id that may or may not exist
        result = FinancialDataService.get_line_items(project_id=999999)
        
        # Should return dict (either with data or error)
        assert isinstance(result, dict)
        
        # If error, should have 'error' key
        if 'error' in result:
            assert isinstance(result['error'], str)
        else:
            # If success, should have required keys
            assert 'project_id' in result
            assert 'line_items' in result
            assert 'totals' in result
            assert isinstance(result['line_items'], list)
            assert isinstance(result['totals'], dict)

    def test_line_items_totals_computation(self):
        """Line items totals should sum correctly"""
        result = FinancialDataService.get_line_items(project_id=999999)
        
        if 'error' not in result and len(result['line_items']) > 0:
            # Manually compute expected totals
            manual_total = sum(item['fee'] for item in result['line_items'])
            manual_billed = sum(item['fee'] for item in result['line_items'] if item['is_billed'])
            
            assert abs(result['totals']['total_fee'] - manual_total) < 0.01
            assert abs(result['totals']['billed_fee'] - manual_billed) < 0.01
            assert abs(result['totals']['outstanding_fee'] - (manual_total - manual_billed)) < 0.01

    def test_get_reconciliation_returns_expected_structure(self):
        """Reconciliation endpoint returns expected structure"""
        result = FinancialDataService.get_reconciliation(project_id=999999)
        
        assert isinstance(result, dict)
        
        if 'error' not in result:
            assert 'project' in result
            assert 'by_service' in result
            assert isinstance(result['project'], dict)
            assert isinstance(result['by_service'], list)
            
            # Check project level fields
            project = result['project']
            assert 'project_id' in project
            assert 'agreed_fee' in project
            assert 'line_items_total_fee' in project
            assert 'billed_total_fee' in project
            assert 'outstanding_total_fee' in project
            assert 'variance' in project

    def test_reconciliation_variance_calculation(self):
        """Variance should be agreed_fee - line_items_total"""
        result = FinancialDataService.get_reconciliation(project_id=999999)
        
        if 'error' not in result:
            project = result['project']
            expected_variance = project['agreed_fee'] - project['line_items_total_fee']
            
            # Allow for floating point precision
            assert abs(project['variance'] - expected_variance) < 0.01

    def test_reconciliation_outstanding_calculation(self):
        """Outstanding should be line_items_total - billed"""
        result = FinancialDataService.get_reconciliation(project_id=999999)
        
        if 'error' not in result:
            project = result['project']
            expected_outstanding = project['line_items_total_fee'] - project['billed_total_fee']
            
            assert abs(project['outstanding_total_fee'] - expected_outstanding) < 0.01
            
            # Service level checks
            for service in result['by_service']:
                expected = service['line_items_total_fee'] - service['billed_total_fee']
                assert abs(service['outstanding_total_fee'] - expected) < 0.01

    def test_line_items_include_both_reviews_and_items(self):
        """Line items should include both review and item type rows"""
        result = FinancialDataService.get_line_items(project_id=999999)
        
        if 'error' not in result and len(result['line_items']) > 0:
            types = set(item['type'] for item in result['line_items'])
            # May have only reviews or items, but should be one of these types
            assert all(t in ('review', 'item') for t in types)

    def test_line_items_filter_by_service(self):
        """Service filter should limit results to that service"""
        # First, get all items for a project
        all_result = FinancialDataService.get_line_items(project_id=999999)
        
        if 'error' not in all_result and len(all_result['line_items']) > 0:
            # Get a service_id from results
            service_id = all_result['line_items'][0]['service_id']
            
            # Filter by that service
            filtered_result = FinancialDataService.get_line_items(
                project_id=999999,
                service_id=service_id
            )
            
            if 'error' not in filtered_result:
                # All results should be for that service
                assert all(item['service_id'] == service_id for item in filtered_result['line_items'])

    def test_line_items_filter_by_invoice_status(self):
        """Invoice status filter should limit results"""
        result = FinancialDataService.get_line_items(
            project_id=999999,
            invoice_status='draft'
        )
        
        if 'error' not in result and len(result['line_items']) > 0:
            # All items should be draft (or None, which shouldn't match)
            assert all(item['invoice_status'] == 'draft' for item in result['line_items'])


class TestFeeResolutionInFinancialData:
    """Test that fee resolution works correctly in financial data service"""

    def test_fee_source_populated_in_line_items(self):
        """Each line item should have a fee_source"""
        result = FinancialDataService.get_line_items(project_id=999999)
        
        if 'error' not in result and len(result['line_items']) > 0:
            for item in result['line_items']:
                assert 'fee_source' in item
                assert item['fee_source'] in (
                    'override', 
                    'calculated_equal_split', 
                    'calculated_weighted',
                    'explicit'
                )

    def test_fee_values_are_numeric(self):
        """All fee values should be floats >= 0"""
        result = FinancialDataService.get_line_items(project_id=999999)
        
        if 'error' not in result:
            for item in result['line_items']:
                assert isinstance(item['fee'], (int, float))
                assert item['fee'] >= 0
            
            totals = result['totals']
            assert totals['total_fee'] >= 0
            assert totals['billed_fee'] >= 0
            assert totals['outstanding_fee'] >= 0


class TestInvoiceMonthHandling:
    """Test invoice month calculation in line items"""

    def test_invoice_month_populated_for_all_items(self):
        """All items should have an invoice_month"""
        result = FinancialDataService.get_line_items(project_id=999999)
        
        if 'error' not in result and len(result['line_items']) > 0:
            for item in result['line_items']:
                assert 'invoice_month' in item
                assert isinstance(item['invoice_month'], str)
                # Should be YYYY-MM format or 'TBD'
                if item['invoice_month'] != 'TBD':
                    assert len(item['invoice_month']) == 7
                    assert item['invoice_month'][4] == '-'


class TestProject4FinanceData:
    """Tests for Project 4 - verifying fee resolution fixes"""

    def test_line_items_non_zero_totals_when_service_has_agreed_fee(self):
        """Project 4 items should return non-zero totals when service has agreed_fee."""
        result = FinancialDataService.get_line_items(4)
        
        assert 'error' not in result, f"Unexpected error: {result.get('error')}"
        
        line_items = result.get('line_items', [])
        assert len(line_items) >= 2, f"Expected at least 2 items, got {len(line_items)}"
        
        totals = result.get('totals', {})
        total_fee = totals.get('total_fee', 0)
        
        # Project 4 should have total_fee = 100000.0
        # Item 34: inherited_from_service = 93000.0
        # Item 35: override = 7000.0
        assert total_fee == 100000.0, f"Expected total_fee = 100000.0, got {total_fee}"
        assert totals.get('billed_fee') == 7000.0, f"Expected billed_fee = 7000.0, got {totals.get('billed_fee')}"
        assert totals.get('outstanding_fee') == 93000.0, f"Expected outstanding_fee = 93000.0, got {totals.get('outstanding_fee')}"

    def test_item_with_null_fee_amount_inherits_from_service(self):
        """Item 34 (NULL fee_amount) should inherit agreed_fee from service."""
        result = FinancialDataService.get_line_items(4)
        
        line_items = result.get('line_items', [])
        item_34 = next((i for i in line_items if i['id'] == 34), None)
        
        assert item_34 is not None, "Item 34 not found"
        assert item_34['fee'] == 93000.0, f"Expected fee 93000.0, got {item_34['fee']}"
        assert item_34['fee_source'] == 'inherited_from_service', f"Expected fee_source 'inherited_from_service', got '{item_34['fee_source']}'"

    def test_item_with_explicit_fee_amount_uses_override(self):
        """Item 35 (explicit fee_amount=7000) should use override."""
        result = FinancialDataService.get_line_items(4)
        
        line_items = result.get('line_items', [])
        item_35 = next((i for i in line_items if i['id'] == 35), None)
        
        assert item_35 is not None, "Item 35 not found"
        assert item_35['fee'] == 7000.0, f"Expected fee 7000.0, got {item_35['fee']}"
        assert item_35['fee_source'] == 'override', f"Expected fee_source 'override', got '{item_35['fee_source']}'"

    def test_invoice_month_fallback_to_due_date(self):
        """Items should fall back to due_date month when invoice_month is NULL."""
        result = FinancialDataService.get_line_items(4)
        
        line_items = result.get('line_items', [])
        item_34 = next((i for i in line_items if i['id'] == 34), None)
        
        assert item_34 is not None, "Item 34 not found"
        assert item_34['invoice_month'] == '2026-02', f"Expected invoice_month '2026-02', got '{item_34['invoice_month']}'"
        assert item_34['due_date'] == '2026-02-27', f"Expected due_date '2026-02-27', got '{item_34['due_date']}'"

    def test_reconciliation_variance_computed_correctly(self):
        """Reconciliation should compute variance = agreed_fee - line_items_total_fee."""
        result = FinancialDataService.get_reconciliation(4)
        
        assert 'error' not in result, f"Unexpected error: {result.get('error')}"
        
        project = result.get('project', {})
        agreed_fee = project.get('agreed_fee', 0)
        line_items_total = project.get('line_items_total_fee', 0)
        variance = project.get('variance', 0)
        
        # For project 4: agreed_fee (100000) should equal line_items_total (100000)
        assert agreed_fee == 100000.0, f"Expected agreed_fee 100000.0, got {agreed_fee}"
        assert line_items_total == 100000.0, f"Expected line_items_total_fee 100000.0, got {line_items_total}"
        assert variance == 0.0, f"Expected variance 0.0 (perfect match), got {variance}"

    def test_reconciliation_by_service(self):
        """Reconciliation should show 2 services with correct variance."""
        result = FinancialDataService.get_reconciliation(4)
        
        by_service = result.get('by_service', [])
        assert len(by_service) == 2, f"Expected 2 services, got {len(by_service)}"
        
        # PROD service: 93000
        prod = next((s for s in by_service if s['service_code'] == 'PROD'), None)
        assert prod is not None, "PROD service not found"
        assert prod['agreed_fee'] == 93000.0, f"Expected agreed_fee 93000.0 for PROD, got {prod['agreed_fee']}"
        assert prod['line_items_total_fee'] == 93000.0, f"Expected line_items_total_fee 93000.0 for PROD, got {prod['line_items_total_fee']}"
        assert prod['variance'] == 0.0, f"Expected variance 0.0 for PROD, got {prod['variance']}"
        
        # AUDIT service: 7000
        audit = next((s for s in by_service if s['service_code'] == 'AUDIT'), None)
        assert audit is not None, "AUDIT service not found"
        assert audit['agreed_fee'] == 7000.0, f"Expected agreed_fee 7000.0 for AUDIT, got {audit['agreed_fee']}"
        assert audit['line_items_total_fee'] == 7000.0, f"Expected line_items_total_fee 7000.0 for AUDIT, got {audit['line_items_total_fee']}"
        assert audit['variance'] == 0.0, f"Expected variance 0.0 for AUDIT, got {audit['variance']}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
