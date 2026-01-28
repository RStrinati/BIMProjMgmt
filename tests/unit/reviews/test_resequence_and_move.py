#!/usr/bin/env python3
"""
Unit tests for review fee calculation helper.

Tests cover:
- _calculate_review_fee helper function
- Fee priority chain: override → weighted → equal_split → none
"""

import os
import sys

import pytest

# Add root directory to path for imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database import _calculate_review_fee


class TestCalculateReviewFee:
    """Test the _calculate_review_fee helper function."""

    def test_fee_override_takes_precedence(self):
        result = _calculate_review_fee(
            billing_amount=5000,
            fee_amount_override=1500,
            agreed_fee=2000,
            review_count_planned=4,
        )
        assert result["fee"] == 1500
        assert result["fee_source"] == "override"

    def test_weighted_fee_when_billing_amount_exists(self):
        result = _calculate_review_fee(
            billing_amount=5000,
            fee_amount_override=None,
            agreed_fee=2000,
            review_count_planned=4,
        )
        assert result["fee"] == 5000
        assert result["fee_source"] == "weighted"

    def test_equal_split_fee_when_agreed_fee_exists(self):
        result = _calculate_review_fee(
            billing_amount=None,
            fee_amount_override=None,
            agreed_fee=2000,
            review_count_planned=4,
        )
        assert result["fee"] == 500
        assert result["fee_source"] == "equal_split"

    def test_equal_split_with_different_counts(self):
        test_cases = [
            (1000, 1, 1000),
            (1000, 2, 500),
            (1000, 5, 200),
            (2400, 12, 200),
        ]
        for agreed_fee, count, expected_fee in test_cases:
            result = _calculate_review_fee(
                billing_amount=None,
                fee_amount_override=None,
                agreed_fee=agreed_fee,
                review_count_planned=count,
            )
            assert result["fee"] == expected_fee
            assert result["fee_source"] == "equal_split"

    def test_none_fee_when_no_sources(self):
        result = _calculate_review_fee(
            billing_amount=None,
            fee_amount_override=None,
            agreed_fee=None,
            review_count_planned=0,
        )
        assert result["fee"] is None
        assert result["fee_source"] == "none"

    def test_zero_review_count_returns_none(self):
        result = _calculate_review_fee(
            billing_amount=None,
            fee_amount_override=None,
            agreed_fee=2000,
            review_count_planned=0,
        )
        assert result["fee"] is None
        assert result["fee_source"] == "none"

    def test_override_zero_is_valid(self):
        result = _calculate_review_fee(
            billing_amount=5000,
            fee_amount_override=0,
            agreed_fee=2000,
            review_count_planned=4,
        )
        assert result["fee"] == 0
        assert result["fee_source"] == "override"

    def test_billing_zero_falls_through_to_agreed_fee(self):
        result = _calculate_review_fee(
            billing_amount=0,
            fee_amount_override=None,
            agreed_fee=2000,
            review_count_planned=4,
        )
        assert result["fee"] == 500
        assert result["fee_source"] == "equal_split"

    def test_fee_priority_chain_override_beats_all(self):
        result = _calculate_review_fee(
            billing_amount=10000,
            fee_amount_override=100,
            agreed_fee=5000,
            review_count_planned=10,
        )
        assert result["fee"] == 100
        assert result["fee_source"] == "override"

    def test_fee_priority_chain_weighted_beats_equal_split(self):
        result = _calculate_review_fee(
            billing_amount=7500,
            fee_amount_override=None,
            agreed_fee=2000,
            review_count_planned=4,
        )
        assert result["fee"] == 7500
        assert result["fee_source"] == "weighted"

    def test_negative_fees_allowed(self):
        result = _calculate_review_fee(
            billing_amount=-500,
            fee_amount_override=None,
            agreed_fee=None,
            review_count_planned=1,
        )
        assert result["fee"] == -500
        assert result["fee_source"] == "weighted"

    def test_large_fee_values(self):
        result = _calculate_review_fee(
            billing_amount=None,
            fee_amount_override=None,
            agreed_fee=1000000,
            review_count_planned=100,
        )
        assert result["fee"] == 10000
        assert result["fee_source"] == "equal_split"


class TestResequenceServiceReviews:
    """Test the resequence_service_reviews function."""
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
