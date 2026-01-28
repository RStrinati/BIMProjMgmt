"""
Unit tests for FeeResolverService

Tests all fee resolution logic without requiring database connections.
"""

import pytest
from services.fee_resolver_service import FeeResolverService
from constants.schema import ServiceReviews, ServiceItems, ProjectServices


class TestResolveReviewFee:
    """Test cases for resolve_review_fee()"""

    def test_user_override_takes_precedence(self):
        """When is_user_modified=1, use billing_amount as override"""
        review = {
            ServiceReviews.REVIEW_ID: 'rev_001',
            ServiceReviews.BILLING_AMOUNT: 7500.0,
            ServiceReviews.IS_USER_MODIFIED: 1,
            ServiceReviews.WEIGHT_FACTOR: 0.5,  # Should be ignored
        }
        service = {
            ProjectServices.AGREED_FEE: 20000.0,
            ProjectServices.REVIEW_COUNT_PLANNED: 4,
        }
        fee, source = FeeResolverService.resolve_review_fee(review, service)
        
        assert fee == 7500.0
        assert source == 'override'

    def test_equal_split_when_no_weight(self):
        """When is_user_modified=0 and no weight_factor, split equally"""
        review = {
            ServiceReviews.REVIEW_ID: 'rev_002',
            ServiceReviews.BILLING_AMOUNT: 0,
            ServiceReviews.IS_USER_MODIFIED: 0,
            ServiceReviews.WEIGHT_FACTOR: None,
        }
        service = {
            ProjectServices.AGREED_FEE: 20000.0,
            ProjectServices.REVIEW_COUNT_PLANNED: 4,
        }
        fee, source = FeeResolverService.resolve_review_fee(review, service)
        
        assert fee == 5000.0
        assert source == 'calculated_equal_split'

    def test_weighted_split_when_weight_provided(self):
        """When weight_factor is set, use proportional split"""
        review = {
            ServiceReviews.REVIEW_ID: 'rev_003',
            ServiceReviews.BILLING_AMOUNT: 0,
            ServiceReviews.IS_USER_MODIFIED: 0,
            ServiceReviews.WEIGHT_FACTOR: 0.35,
        }
        service = {
            ProjectServices.AGREED_FEE: 20000.0,
            ProjectServices.REVIEW_COUNT_PLANNED: 4,
        }
        fee, source = FeeResolverService.resolve_review_fee(review, service)
        
        assert fee == 7000.0  # 20000 * 0.35
        assert source == 'calculated_weighted'

    def test_weight_zero_ignored_falls_back_to_equal_split(self):
        """When weight_factor is 0, should not use it; fall back to equal split"""
        review = {
            ServiceReviews.REVIEW_ID: 'rev_004',
            ServiceReviews.BILLING_AMOUNT: 0,
            ServiceReviews.IS_USER_MODIFIED: 0,
            ServiceReviews.WEIGHT_FACTOR: 0.0,
        }
        service = {
            ProjectServices.AGREED_FEE: 20000.0,
            ProjectServices.REVIEW_COUNT_PLANNED: 4,
        }
        fee, source = FeeResolverService.resolve_review_fee(review, service)
        
        # 0.0 weight should not be used; fall back to equal split
        assert fee == 5000.0
        assert source == 'calculated_equal_split'

    def test_no_service_row_uses_billing_amount_fallback(self):
        """When service_row is None, use billing_amount as fallback"""
        review = {
            ServiceReviews.REVIEW_ID: 'rev_005',
            ServiceReviews.BILLING_AMOUNT: 3000.0,
            ServiceReviews.IS_USER_MODIFIED: 0,
            ServiceReviews.WEIGHT_FACTOR: None,
        }
        fee, source = FeeResolverService.resolve_review_fee(review, service_row=None)
        
        assert fee == 3000.0
        assert source == 'override'

    def test_zero_review_count_uses_fallback(self):
        """When review_count_planned is 0, fall back to billing_amount"""
        review = {
            ServiceReviews.REVIEW_ID: 'rev_006',
            ServiceReviews.BILLING_AMOUNT: 2500.0,
            ServiceReviews.IS_USER_MODIFIED: 0,
            ServiceReviews.WEIGHT_FACTOR: None,
        }
        service = {
            ProjectServices.AGREED_FEE: 20000.0,
            ProjectServices.REVIEW_COUNT_PLANNED: 0,  # Invalid
        }
        fee, source = FeeResolverService.resolve_review_fee(review, service)
        
        assert fee == 2500.0
        assert source == 'override'

    def test_missing_billing_amount_defaults_to_zero(self):
        """Missing billing_amount should default to 0"""
        review = {
            ServiceReviews.REVIEW_ID: 'rev_007',
            # billing_amount missing
            ServiceReviews.IS_USER_MODIFIED: 1,
            ServiceReviews.WEIGHT_FACTOR: None,
        }
        fee, source = FeeResolverService.resolve_review_fee(review)
        
        assert fee == 0.0
        assert source == 'override'

    def test_missing_is_user_modified_defaults_to_zero(self):
        """Missing is_user_modified should default to 0 (not modified)"""
        review = {
            ServiceReviews.REVIEW_ID: 'rev_008',
            ServiceReviews.BILLING_AMOUNT: 0,
            # is_user_modified missing
            ServiceReviews.WEIGHT_FACTOR: None,
        }
        service = {
            ProjectServices.AGREED_FEE: 20000.0,
            ProjectServices.REVIEW_COUNT_PLANNED: 4,
        }
        fee, source = FeeResolverService.resolve_review_fee(review, service)
        
        assert fee == 5000.0
        assert source == 'calculated_equal_split'

    def test_negative_weight_not_used(self):
        """Negative weight_factor should not be used"""
        review = {
            ServiceReviews.REVIEW_ID: 'rev_009',
            ServiceReviews.BILLING_AMOUNT: 0,
            ServiceReviews.IS_USER_MODIFIED: 0,
            ServiceReviews.WEIGHT_FACTOR: -0.1,
        }
        service = {
            ProjectServices.AGREED_FEE: 20000.0,
            ProjectServices.REVIEW_COUNT_PLANNED: 4,
        }
        # Negative weight should not satisfy > 0 check, fall back to equal split
        fee, source = FeeResolverService.resolve_review_fee(review, service)
        
        assert fee == 5000.0
        assert source == 'calculated_equal_split'


class TestResolveItemFee:
    """Test cases for resolve_item_fee()"""

    def test_item_with_user_modified_override(self):
        """When is_user_modified=1, return fee_amount as override"""
        item = {
            ServiceItems.ITEM_ID: 'item_001',
            ServiceItems.FEE_AMOUNT: 3500.0,
            ServiceItems.IS_USER_MODIFIED: 1,
        }
        fee, source = FeeResolverService.resolve_item_fee(item)
        
        assert fee == 3500.0
        assert source == 'override'

    def test_item_with_explicit_fee(self):
        """When is_user_modified=0, return fee_amount as explicit"""
        item = {
            ServiceItems.ITEM_ID: 'item_002',
            ServiceItems.FEE_AMOUNT: 2500.0,
            ServiceItems.IS_USER_MODIFIED: 0,
        }
        fee, source = FeeResolverService.resolve_item_fee(item)
        
        assert fee == 2500.0
        assert source == 'explicit'

    def test_item_with_zero_fee(self):
        """Items with zero fee are valid"""
        item = {
            ServiceItems.ITEM_ID: 'item_003',
            ServiceItems.FEE_AMOUNT: 0.0,
            ServiceItems.IS_USER_MODIFIED: 0,
        }
        fee, source = FeeResolverService.resolve_item_fee(item)
        
        assert fee == 0.0
        assert source == 'explicit'

    def test_item_missing_fee_amount_defaults_to_zero(self):
        """Missing fee_amount should default to 0"""
        item = {
            ServiceItems.ITEM_ID: 'item_004',
            # fee_amount missing
            ServiceItems.IS_USER_MODIFIED: 0,
        }
        fee, source = FeeResolverService.resolve_item_fee(item)
        
        assert fee == 0.0
        assert source == 'explicit'

    def test_item_missing_is_user_modified_defaults_to_zero(self):
        """Missing is_user_modified should default to 0"""
        item = {
            ServiceItems.ITEM_ID: 'item_005',
            ServiceItems.FEE_AMOUNT: 1500.0,
            # is_user_modified missing
        }
        fee, source = FeeResolverService.resolve_item_fee(item)
        
        assert fee == 1500.0
        assert source == 'explicit'


class TestCanEditFee:
    """Test cases for can_edit_fee()"""

    def test_can_edit_draft_and_not_billed(self):
        """Fee can be edited when status is draft and not billed"""
        assert FeeResolverService.can_edit_fee('draft', 0) is True

    def test_can_edit_ready_and_not_billed(self):
        """Fee can be edited when status is ready and not billed"""
        assert FeeResolverService.can_edit_fee('ready', 0) is True

    def test_cannot_edit_when_issued(self):
        """Fee cannot be edited when invoice_status is issued"""
        assert FeeResolverService.can_edit_fee('issued', 0) is False

    def test_cannot_edit_when_paid(self):
        """Fee cannot be edited when invoice_status is paid"""
        assert FeeResolverService.can_edit_fee('paid', 0) is False

    def test_cannot_edit_when_is_billed_one(self):
        """Fee cannot be edited when is_billed = 1"""
        assert FeeResolverService.can_edit_fee('draft', 1) is False

    def test_cannot_edit_when_paid_and_billed(self):
        """Fee cannot be edited when both status is paid and is_billed = 1"""
        assert FeeResolverService.can_edit_fee('paid', 1) is False

    def test_can_edit_none_status_and_not_billed(self):
        """Fee can be edited when status is None and not billed"""
        assert FeeResolverService.can_edit_fee(None, 0) is True

    def test_case_insensitive_status_check(self):
        """Status check should be case-insensitive"""
        assert FeeResolverService.can_edit_fee('ISSUED', 0) is False
        assert FeeResolverService.can_edit_fee('PAID', 0) is False
        assert FeeResolverService.can_edit_fee('Issued', 0) is False


class TestValidateFeeValue:
    """Test cases for validate_fee_value()"""

    def test_valid_positive_fee(self):
        """Positive fees within range are valid"""
        assert FeeResolverService.validate_fee_value(5000.0) is True
        assert FeeResolverService.validate_fee_value(1000000.0) is True

    def test_valid_zero_fee(self):
        """Zero fee is valid (default min)"""
        assert FeeResolverService.validate_fee_value(0.0) is True

    def test_negative_fee_invalid(self):
        """Negative fees are invalid"""
        assert FeeResolverService.validate_fee_value(-1000.0) is False

    def test_fee_exceeding_max_invalid(self):
        """Fees exceeding max are invalid"""
        assert FeeResolverService.validate_fee_value(2_000_000_000) is False

    def test_string_fee_converted_to_float(self):
        """String fees can be converted to float"""
        assert FeeResolverService.validate_fee_value("5000.0") is True
        assert FeeResolverService.validate_fee_value("0") is True

    def test_invalid_string_fee(self):
        """Non-numeric strings are invalid"""
        assert FeeResolverService.validate_fee_value("abc") is False
        assert FeeResolverService.validate_fee_value("") is False

    def test_custom_min_max(self):
        """Custom min/max values work"""
        assert FeeResolverService.validate_fee_value(100.0, min_value=100, max_value=1000) is True
        assert FeeResolverService.validate_fee_value(50.0, min_value=100, max_value=1000) is False
        assert FeeResolverService.validate_fee_value(1100.0, min_value=100, max_value=1000) is False


class TestCalculateInvoiceMonthFinal:
    """Test cases for calculate_invoice_month_final()"""

    def test_override_has_highest_priority(self):
        """Override takes precedence over auto_derived and due_date"""
        result = FeeResolverService.calculate_invoice_month_final(
            override='2026-03',
            auto_derived='2026-02',
            due_date='2026-01-15'
        )
        assert result == '2026-03'

    def test_auto_derived_fallback_when_no_override(self):
        """auto_derived used when override is None"""
        result = FeeResolverService.calculate_invoice_month_final(
            override=None,
            auto_derived='2026-02',
            due_date='2026-01-15'
        )
        assert result == '2026-02'

    def test_due_date_fallback_when_no_override_or_auto(self):
        """due_date used when override and auto_derived are None"""
        result = FeeResolverService.calculate_invoice_month_final(
            override=None,
            auto_derived=None,
            due_date='2026-01-15'
        )
        assert result == '2026-01'

    def test_tbd_when_all_none(self):
        """Returns 'TBD' when all sources are None"""
        result = FeeResolverService.calculate_invoice_month_final(
            override=None,
            auto_derived=None,
            due_date=None
        )
        assert result == 'TBD'

    def test_whitespace_stripped_from_override(self):
        """Whitespace is stripped from override"""
        result = FeeResolverService.calculate_invoice_month_final(
            override='  2026-03  ',
            auto_derived=None,
            due_date=None
        )
        assert result == '2026-03'

    def test_invalid_due_date_returns_tbd(self):
        """Invalid due_date format falls back to TBD"""
        result = FeeResolverService.calculate_invoice_month_final(
            override=None,
            auto_derived=None,
            due_date='invalid-date'
        )
        assert result == 'TBD'


class TestComputeReconciliationVariance:
    """Test cases for compute_reconciliation_variance()"""

    def test_positive_variance_shortfall(self):
        """Positive variance means line items are less than agreed (shortfall)"""
        variance = FeeResolverService.compute_reconciliation_variance(
            agreed_fee=100000.0,
            line_items_total=95000.0
        )
        assert variance == 5000.0

    def test_zero_variance_perfect_match(self):
        """Zero variance when line items match agreed fee"""
        variance = FeeResolverService.compute_reconciliation_variance(
            agreed_fee=100000.0,
            line_items_total=100000.0
        )
        assert variance == 0.0

    def test_negative_variance_overbilling(self):
        """Negative variance means line items exceed agreed (overbilling)"""
        variance = FeeResolverService.compute_reconciliation_variance(
            agreed_fee=100000.0,
            line_items_total=105000.0
        )
        assert variance == -5000.0

    def test_zero_agreed_fee(self):
        """Works with zero agreed fee"""
        variance = FeeResolverService.compute_reconciliation_variance(
            agreed_fee=0.0,
            line_items_total=10000.0
        )
        assert variance == -10000.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
