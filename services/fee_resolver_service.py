"""
Fee Resolver Service

Centralizes all fee calculation and resolution logic for ServiceReviews and ServiceItems.
Uses existing schema columns (billing_amount, fee_amount, weight_factor, etc.) 
to derive "fee_final" with transparency about the source (override, calculated, etc.).

No new database columns required.
"""

from typing import Tuple, Optional, Dict, Any
from constants.schema import ServiceReviews, ServiceItems, ProjectServices


class FeeResolverService:
    """
    Resolves final fee values for reviews and items using existing schema columns.
    
    All calculations are based on:
    - ServiceReviews.billing_amount (per-review fee, may be override)
    - ServiceReviews.weight_factor (proportional weight 0.0-1.0)
    - ServiceReviews.is_user_modified (was this row manually edited?)
    - ServiceItems.fee_amount (per-item fee override or explicit)
    - ProjectServices.agreed_fee (service-level contract fee)
    - ProjectServices.review_count_planned (expected number of reviews for equal split)
    """

    @staticmethod
    def resolve_review_fee(
        review_row: Dict[str, Any],
        service_row: Optional[Dict[str, Any]] = None,
        actual_review_count: Optional[int] = None
    ) -> Tuple[float, str]:
        """
        Resolve the final fee for a single ServiceReview.
        
        **DETERMINISTIC MODEL** (matches Deliverables tab behavior):
        - Deliverables edits ServiceReviews.fee_amount (NOT billing_amount)
        - fee_amount is the single source of truth for review fees
        - If fee_amount is NULL, fall back to equal split calculation
        
        Args:
            review_row: Dict with keys 'review_id', 'fee_amount', 'is_user_modified'
            service_row: Optional dict from ProjectServices (agreed_fee, review_count_planned)
            actual_review_count: Optional count of actual reviews (for equal split when planned is NULL)
        
        Returns:
            Tuple of (fee_value: float, fee_source: str)
            fee_source in: 'override', 'explicit', 'calculated_equal_split'
        
        Logic:
            1. If fee_amount is set (not NULL):
               - If is_user_modified = 1: treat as 'override' (user edited via Deliverables)
               - Else: treat as 'explicit' (set programmatically or imported)
            2. Else if service_row provided with agreed_fee > 0:
               - Calculate equal split: agreed_fee / actual_review_count
               - Returns 'calculated_equal_split'
            3. Else: return 0 (review has no fee)
        
        Examples:
            # User edited this review in Deliverables - override
            review = {'review_id': 1, 'fee_amount': 6000.0, 'is_user_modified': 1}
            fee, source = FeeResolverService.resolve_review_fee(review)
            # Returns: (6000.0, 'override')
            
            # Automatic equal split across 15 actual reviews
            service = {'agreed_fee': 90000.0, 'review_count_planned': None}
            review = {'review_id': 1, 'fee_amount': None, 'is_user_modified': 0}
            fee, source = FeeResolverService.resolve_review_fee(review, service, actual_review_count=15)
            # Returns: (6000.0, 'calculated_equal_split')
        """
        # Extract values with safe defaults
        fee_amount = review_row.get(ServiceReviews.FEE_AMOUNT)
        is_user_modified = review_row.get(ServiceReviews.IS_USER_MODIFIED, 0)

        # Rule 1: If fee_amount is set (edited in Deliverables or imported), use it
        if fee_amount is not None:
            fee_amount_float = float(fee_amount)
            if is_user_modified:
                return (fee_amount_float, 'override')
            return (fee_amount_float, 'explicit')

        # Rule 2: Calculate equal split from service agreed_fee
        if service_row and actual_review_count and actual_review_count > 0:
            agreed_fee = float(service_row.get(ProjectServices.AGREED_FEE) or 0)
            if agreed_fee > 0:
                fee = agreed_fee / actual_review_count
                return (fee, 'calculated_equal_split')

        # No fee available
        return (0.0, 'none')

    @staticmethod
    def resolve_item_fee(
        item_row: Dict[str, Any],
        service_row: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, str]:
        """
        Resolve the final fee for a single ServiceItem.
        
        **DETERMINISTIC MODEL** (matches Deliverables tab behavior):
        - Deliverables edits ServiceItems.fee_amount
        - fee_amount is the ONLY source of truth for item fees
        - Items do NOT inherit from service agreed_fee
        - If fee_amount is NULL, item has no fee (returns 0)
        
        Args:
            item_row: Dict with keys 'item_id', 'fee_amount', 'is_user_modified'
            service_row: Not used (kept for API compatibility)
        
        Returns:
            Tuple of (fee_value: float, fee_source: str)
            fee_source in: 'override', 'explicit', 'none'
        
        Logic:
            1. If fee_amount is set (not NULL):
               - If is_user_modified = 1: treat as 'override' (user edited)
               - Else: treat as 'explicit' (set programmatically)
            2. Else: return 0 (item has no fee)
        
        Examples:
            # Item with explicit fee set by user
            item = {'item_id': 1, 'fee_amount': 5000.0, 'is_user_modified': 1}
            fee, source = FeeResolverService.resolve_item_fee(item)
            # Returns: (5000.0, 'override')
            
            # Item with NULL fee - no fee
            item = {'item_id': 1, 'fee_amount': None, 'is_user_modified': 0}
            fee, source = FeeResolverService.resolve_item_fee(item)
            # Returns: (0.0, 'none')
        """
        fee_amount = item_row.get(ServiceItems.FEE_AMOUNT)
        is_user_modified = item_row.get(ServiceItems.IS_USER_MODIFIED, 0)

        # If fee_amount is set, use it
        if fee_amount is not None:
            fee_amount_float = float(fee_amount)
            if is_user_modified:
                return (fee_amount_float, 'override')
            return (fee_amount_float, 'explicit')
        
        # No fee available (items do NOT inherit from service)
        return (0.0, 'none')

    @staticmethod
    def can_edit_fee(invoice_status: Optional[str], is_billed: int) -> bool:
        """
        Determine if a review/item fee can be edited based on invoice status.
        
        Args:
            invoice_status: string like 'draft', 'ready', 'issued', 'paid', or None
            is_billed: bit (0 or 1)
        
        Returns:
            bool: True if fee can be edited, False if locked
        
        Rule:
            Fee cannot be edited if:
            - invoice_status is 'issued' or 'paid'
            - is_billed = 1
        """
        if is_billed:
            return False
        
        if invoice_status and invoice_status.lower() in ('issued', 'paid'):
            return False
        
        return True

    @staticmethod
    def validate_fee_value(fee: float, min_value: float = 0, max_value: float = 1_000_000_000) -> bool:
        """
        Basic validation for fee values.
        
        Args:
            fee: Fee amount to validate
            min_value: Minimum allowed (default 0)
            max_value: Maximum allowed (default 1 billion)
        
        Returns:
            bool: True if valid
        """
        try:
            f = float(fee)
            return min_value <= f <= max_value
        except (TypeError, ValueError):
            return False

    @staticmethod
    def calculate_invoice_month_final(
        override: Optional[str],
        auto_derived: Optional[str],
        due_date: Optional[str] = None
    ) -> str:
        """
        Determine the final invoice month using the three-tier fallback logic.
        
        Args:
            override: invoice_month_override from database (YYYY-MM or None)
            auto_derived: invoice_month_auto from database (YYYY-MM or None)
            due_date: ISO date string (YYYY-MM-DD), used if auto_derived is None
        
        Returns:
            str: YYYY-MM format invoice month, or 'TBD' if cannot determine
        
        Tier 1: override > Tier 2: auto_derived > Tier 3: due_date month > TBD
        """
        if override:
            return override.strip()
        
        if auto_derived:
            return auto_derived.strip()
        
        if due_date:
            # Extract YYYY-MM from ISO date
            try:
                date_str = str(due_date).strip()
                # Validate it looks like YYYY-MM-DD format (at least 7 chars and has hyphens)
                if len(date_str) >= 7 and date_str[4] == '-' and date_str[7] == '-':
                    return date_str[:7]  # "2026-02-15" -> "2026-02"
            except (TypeError, IndexError, AttributeError):
                pass
        
        return 'TBD'

    @staticmethod
    def compute_reconciliation_variance(agreed_fee: float, line_items_total: float) -> float:
        """
        Compute variance between agreed fee and line items total.
        
        Positive variance means line items are less than agreed fee (potential billing shortfall).
        Negative variance means line items exceed agreed fee (potential overbilling).
        
        Args:
            agreed_fee: Total agreed fee from ProjectServices
            line_items_total: Sum of resolved fees from all reviews + items
        
        Returns:
            float: agreed_fee - line_items_total
        """
        return agreed_fee - line_items_total


# Example usage (for testing/documentation)
if __name__ == '__main__':
    # Example 1: User override
    review1 = {
        ServiceReviews.REVIEW_ID: 'rev_001',
        ServiceReviews.BILLING_AMOUNT: 5500.0,
        ServiceReviews.IS_USER_MODIFIED: 1,
        ServiceReviews.WEIGHT_FACTOR: None,
    }
    fee, source = FeeResolverService.resolve_review_fee(review1)
    print(f"Review with user override: fee={fee}, source={source}")
    # Output: Review with user override: fee=5500.0, source=override

    # Example 2: Equal split
    service = {
        ProjectServices.AGREED_FEE: 20000.0,
        ProjectServices.REVIEW_COUNT_PLANNED: 4,
    }
    review2 = {
        ServiceReviews.REVIEW_ID: 'rev_002',
        ServiceReviews.BILLING_AMOUNT: 0,
        ServiceReviews.IS_USER_MODIFIED: 0,
        ServiceReviews.WEIGHT_FACTOR: None,
    }
    fee, source = FeeResolverService.resolve_review_fee(review2, service)
    print(f"Review with equal split: fee={fee}, source={source}")
    # Output: Review with equal split: fee=5000.0, source=calculated_equal_split

    # Example 3: Weighted split
    review3 = {
        ServiceReviews.REVIEW_ID: 'rev_003',
        ServiceReviews.BILLING_AMOUNT: 0,
        ServiceReviews.IS_USER_MODIFIED: 0,
        ServiceReviews.WEIGHT_FACTOR: 0.35,
    }
    fee, source = FeeResolverService.resolve_review_fee(review3, service)
    print(f"Review with weighted split (35%): fee={fee}, source={source}")
    # Output: Review with weighted split (35%): fee=7000.0, source=calculated_weighted

    # Example 4: Item fee
    item = {
        ServiceItems.ITEM_ID: 'item_001',
        ServiceItems.FEE_AMOUNT: 2500.0,
        ServiceItems.IS_USER_MODIFIED: 0,
    }
    fee, source = FeeResolverService.resolve_item_fee(item)
    print(f"Item fee: fee={fee}, source={source}")
    # Output: Item fee: fee=2500.0, source=explicit

    # Example 5: Can edit fee?
    can_edit1 = FeeResolverService.can_edit_fee('draft', 0)
    print(f"Can edit draft, not billed: {can_edit1}")
    # Output: Can edit draft, not billed: True

    can_edit2 = FeeResolverService.can_edit_fee('paid', 0)
    print(f"Can edit paid: {can_edit2}")
    # Output: Can edit paid: False

    can_edit3 = FeeResolverService.can_edit_fee('ready', 1)
    print(f"Can edit when is_billed=1: {can_edit3}")
    # Output: Can edit when is_billed=1: False
