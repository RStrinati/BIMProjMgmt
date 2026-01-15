"""
Integration tests for vw_Issues_Reconciled display_id logic.

These tests query the live database view and verify:
1. Display_id format for each source system
2. ACC mapping correlation
3. Pagination and filtering
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from database import get_db_connection, get_reconciled_issues_table
from config import Config


class TestVwIssuesReconciledLive:
    """Live database tests for vw_Issues_Reconciled view."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure database is available before running tests."""
        try:
            with get_db_connection(Config.PROJECT_MGMT_DB) as conn:
                if not conn:
                    pytest.skip("Database connection failed")
        except Exception:
            pytest.skip("Database connection failed")
    
    def test_view_exists_and_returns_data(self):
        """Test that vw_Issues_Reconciled view exists and returns data."""
        result = get_reconciled_issues_table(page=1, page_size=1)
        
        assert result is not None
        assert 'total_count' in result
        assert result['total_count'] > 0, "View should contain issues"
        assert 'rows' in result
        assert len(result['rows']) <= 1
    
    def test_acc_mapped_issues_have_numeric_display_id(self):
        """
        Test that ACC issues with mapping have display_id = 'ACC-' + number.
        
        Verification: Query for issues where:
        - source_system = 'ACC'
        - acc_issue_number IS NOT NULL
        - display_id should start with 'ACC-' and end with digits
        """
        result = get_reconciled_issues_table(
            source_system='ACC',
            page=1,
            page_size=100
        )
        
        assert result['total_count'] > 0
        
        acc_mapped_rows = [
            row for row in result['rows']
            if row.get('acc_issue_number') is not None
        ]
        
        for row in acc_mapped_rows:
            display_id = row.get('display_id')
            assert display_id is not None
            assert display_id.startswith('ACC-'), f"Expected ACC-<number>, got {display_id}"
            # Extract number part and verify it's numeric
            number_part = display_id[4:]  # Remove "ACC-"
            assert number_part.isdigit(), f"Expected numeric suffix in {display_id}"
            assert int(number_part) == row.get('acc_issue_number'), \
                f"Display ID number {number_part} != acc_issue_number {row.get('acc_issue_number')}"
    
    def test_acc_unmapped_issues_have_uuid_prefix_display_id(self):
        """
        Test that ACC issues without mapping have display_id = 'ACC-' + UUID prefix.
        
        Verification: Query for issues where:
        - source_system = 'ACC'
        - acc_issue_number IS NULL
        - display_id should start with 'ACC-' and be followed by 8 hex characters
        """
        result = get_reconciled_issues_table(
            source_system='ACC',
            page=1,
            page_size=100
        )
        
        acc_unmapped_rows = [
            row for row in result['rows']
            if row.get('acc_issue_number') is None
        ]
        
        for row in acc_unmapped_rows:
            display_id = row.get('display_id')
            assert display_id is not None
            assert display_id.startswith('ACC-'), f"Expected ACC-<prefix>, got {display_id}"
            # Extract prefix part (should be 8 hex chars or similar)
            prefix_part = display_id[4:]  # Remove "ACC-"
            assert len(prefix_part) >= 8, f"Expected at least 8 chars in {display_id}"
    
    def test_revizto_issues_have_rev_display_id(self):
        """
        Test that Revizto issues have display_id = 'REV-' + issue ID.
        
        Verification: Query for issues where:
        - source_system = 'Revizto'
        - display_id should start with 'REV-'
        """
        result = get_reconciled_issues_table(
            source_system='Revizto',
            page=1,
            page_size=100
        )
        
        if result['total_count'] > 0:
            for row in result['rows']:
                display_id = row.get('display_id')
                assert display_id is not None
                assert display_id.startswith('REV-'), \
                    f"Expected REV-<id>, got {display_id}"
    
    def test_display_ids_are_unique_within_page(self):
        """Test that display_ids don't repeat within a paginated result."""
        result = get_reconciled_issues_table(page=1, page_size=100)
        
        display_ids = [row.get('display_id') for row in result['rows']]
        unique_display_ids = set(display_ids)
        
        assert len(display_ids) == len(unique_display_ids), \
            f"Found duplicate display_ids: {len(display_ids)} total, {len(unique_display_ids)} unique"
    
    def test_title_field_populated(self):
        """Test that title field is always populated."""
        result = get_reconciled_issues_table(page=1, page_size=50)
        
        for row in result['rows']:
            title = row.get('title')
            assert title is not None and str(title).strip() != '', \
                f"Row {row.get('issue_key')} has empty title"
    
    def test_source_system_values_valid(self):
        """Test that source_system is either 'ACC' or 'Revizto'."""
        result = get_reconciled_issues_table(page=1, page_size=100)
        
        valid_sources = {'ACC', 'Revizto'}
        for row in result['rows']:
            source = row.get('source_system')
            assert source in valid_sources, \
                f"Invalid source_system: {source}"
    
    def test_pagination_page_size_respected(self):
        """Test that page_size parameter is respected."""
        page_size = 25
        result = get_reconciled_issues_table(page=1, page_size=page_size)
        
        assert len(result['rows']) <= page_size, \
            f"Expected {page_size} rows, got {len(result['rows'])}"
    
    def test_pagination_offset_correct(self):
        """Test that pagination offset is calculated correctly."""
        # Get page 1
        page1 = get_reconciled_issues_table(page=1, page_size=10)
        # Get page 2
        page2 = get_reconciled_issues_table(page=2, page_size=10)
        
        if page1['total_count'] > 10 and page2['total_count'] > 0:
            # Verify that page 2 doesn't contain page 1 items
            page1_ids = {row['issue_key'] for row in page1['rows']}
            page2_ids = {row['issue_key'] for row in page2['rows']}
            
            overlap = page1_ids.intersection(page2_ids)
            assert len(overlap) == 0, f"Pages overlap: {overlap}"
    
    def test_filter_by_source_system_works(self):
        """Test filtering by source_system parameter."""
        result = get_reconciled_issues_table(source_system='ACC', page_size=100)
        
        if result['total_count'] > 0:
            for row in result['rows']:
                assert row['source_system'] == 'ACC', \
                    f"Filter failed: got {row['source_system']}"
    
    def test_search_parameter_filters_on_display_id(self):
        """Test that search parameter can filter by display_id."""
        # Get all ACC issues first to find a valid display_id
        acc_issues = get_reconciled_issues_table(source_system='ACC', page_size=10)
        
        if acc_issues['rows']:
            # Take first display_id and search for it
            target_display_id = acc_issues['rows'][0]['display_id']
            
            # Search for partial match
            search_term = target_display_id[:6]  # e.g., "ACC-92"
            result = get_reconciled_issues_table(search=search_term, page_size=100)
            
            # Verify results contain matching display_ids
            matching_rows = [
                row for row in result['rows']
                if search_term in row.get('display_id', '')
            ]
            assert len(matching_rows) > 0, \
                f"Search for '{search_term}' returned no matches"
    
    def test_total_count_consistency(self):
        """Test that total_count is consistent across pages."""
        page1 = get_reconciled_issues_table(page=1, page_size=50)
        page2 = get_reconciled_issues_table(page=2, page_size=50)
        
        assert page1['total_count'] == page2['total_count'], \
            "Total count should be consistent across pages"


class TestReconciledIssuesRowCounts:
    """Test that row counts match expectations from reconciliation."""
    
    def test_total_issues_count(self):
        """Test that total issue count is as expected."""
        result = get_reconciled_issues_table(page_size=50000)  # Large page to get all
        
        # We expect:
        # - 4,748 ACC issues (3,696 mapped + 1,052 unmapped)
        # - 8,092 Revizto issues
        # - Total: 12,840
        
        assert result['total_count'] == 12840, \
            f"Expected 12,840 total issues, got {result['total_count']}"
    
    def test_acc_issues_count(self):
        """Test that ACC issue count is 4,748."""
        result = get_reconciled_issues_table(
            source_system='ACC',
            page_size=50000
        )
        
        assert result['total_count'] == 4748, \
            f"Expected 4,748 ACC issues, got {result['total_count']}"
    
    def test_revizto_issues_count(self):
        """Test that Revizto issue count is 8,092."""
        result = get_reconciled_issues_table(
            source_system='Revizto',
            page_size=50000
        )
        
        assert result['total_count'] == 8092, \
            f"Expected 8,092 Revizto issues, got {result['total_count']}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
