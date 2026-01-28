# Fee Resolution - Deterministic Model (FIXED - January 2026)

## Summary

Fixed the fee calculation logic to match the **deterministic model** that aligns with how the Deliverables tab actually works.

## The Deterministic Model

### Reviews
- **Source Field**: `ServiceReviews.fee_amount` (editable in Deliverables)
- **Resolution Logic**:
  1. If `fee_amount` IS SET (not NULL):
     - If `is_user_modified = 1`: Return as `override` (user edited via Deliverables)
     - Else: Return as `explicit` (set programmatically)
  2. Else (fee_amount IS NULL):
     - Calculate equal split: `agreed_fee / actual_review_count`
     - Return as `calculated_equal_split`

### Items
- **Source Field**: `ServiceItems.fee_amount` (editable in Deliverables)
- **Resolution Logic**:
  1. If `fee_amount` IS SET (not NULL):
     - If `is_user_modified = 1`: Return as `override`
     - Else: Return as `explicit`
  2. Else: Return 0 as `none` (**NO inheritance from service**)

## Key Fixes

### 1. Changed Review Fee Source from `billing_amount` to `fee_amount`
**OLD (INCORRECT)**:
- Used `ServiceReviews.billing_amount` as the fee source
- This is a legacy field that is no longer used

**NEW (CORRECT)**:
- Uses `ServiceReviews.fee_amount` (the field Deliverables edits)
- Matches the actual user experience in the UI

### 2. Removed Item Fee Inheritance
**OLD (INCORRECT)**:
- Items with `fee_amount=NULL` inherited from `ProjectServices.agreed_fee`
- This created unexpected behavior where empty items showed service fees

**NEW (CORRECT)**:
- Items with `fee_amount=NULL` return $0 (`none` source)
- Only items with explicit `fee_amount` values show fees
- No inheritance - items are independent deliverables

### 3. Fixed Equal Split Calculation
**OLD (INCORRECT)**:
- Used `review_count_planned` from ProjectServices
- This field is NULL for all services in the database
- Equal split never worked

**NEW (CORRECT)**:
- Calculates `actual_review_count` per service by counting actual reviews
- Uses this count for equal split: `agreed_fee / actual_review_count`
- Works even when `review_count_planned` is NULL

### 4. Fixed Database Query JOIN
**OLD (INCORRECT)**:
- Queried `WHERE ServiceReviews.project_id = ?`
- But `ServiceReviews.project_id` is NULL for all reviews!

**NEW (CORRECT)**:
- Joins via `ProjectServices.project_id`
- Query: `WHERE ps.project_id = ?`
- Now returns all reviews for the project

## Example: Project 4

### Database State
- **Service 187** (Construction Phase Reviews):
  - `agreed_fee = $90,000`
  - `review_count_planned = NULL` (not set)
  - 15 actual reviews exist

### Review Fee Breakdown
| Review ID | fee_amount | is_user_modified | Resolved Fee | Source |
|-----------|------------|------------------|--------------|--------|
| 5233-5244 | $6,000 | True | $6,000 | `override` (user edited) |
| 5245-5247 | NULL | False | $6,000 | `calculated_equal_split` ($90k / 15) |

**Total Reviews**: 15 × $6,000 = **$90,000** ✅

### Item Fee Breakdown
| Item ID | fee_amount | Resolved Fee | Source |
|---------|------------|--------------|--------|
| 5 | $14,000 | $14,000 | `override` |
| 35 | $7,000 | $7,000 | `override` |
| 6, 17, 34 | NULL | $0 | `none` (no fee) |

**Total Items**: **$21,000** ✅

**Grand Total**: $90,000 + $21,000 = **$111,000** ✅

## API Behavior

### GET `/api/projects/{project_id}/finance/line-items`

**Response Structure**:
```json
{
  "project_id": 4,
  "line_items": [
    {
      "type": "review",
      "id": 5233,
      "service_id": 187,
      "fee": 6000.0,
      "fee_source": "override"
    },
    {
      "type": "review",
      "id": 5245,
      "fee": 6000.0,
      "fee_source": "calculated_equal_split"
    },
    {
      "type": "item",
      "id": 34,
      "fee": 0.0,
      "fee_source": "none"
    }
  ],
  "totals": {
    "total_fee": 111000.0,
    "billed_fee": 0.0,
    "outstanding_fee": 111000.0
  }
}
```

## Files Changed

1. **services/fee_resolver_service.py**
   - `resolve_review_fee()`: Now uses `fee_amount`, not `billing_amount`
   - Accepts `actual_review_count` parameter for equal split
   - Removed weighted split logic (not used)

2. **services/financial_data_service.py**
   - Changed reviews query to select `fee_amount` instead of `billing_amount`
   - Removed `weight_factor` column (not needed)
   - Calculate `actual_review_count` per service before fee resolution
   - Pass `actual_review_count` to `resolve_review_fee()`
   - Remove `service_row` from `resolve_item_fee()` (no inheritance)
   - Fixed JOIN: Use `ps.project_id` instead of `sr.project_id`

## Testing

### Manual Test Script
```bash
python tools/check_finance_api.py
```

**Expected Output**:
```
Total: $111,000.00
Reviews: 15
Items: 5

Reviews total: $90,000.00
Items total: $21,000.00
```

### Unit Tests (Need Update)
- `tests/test_fee_resolver.py` - Tests still expect old logic (billing_amount, weight_factor)
- `tests/test_finance_endpoints.py` - Tests expect item inheritance (now removed)

**Action Required**: Update tests to match new deterministic model.

## Migration Notes

### No Database Schema Changes Required
All fixes use existing columns:
- `ServiceReviews.fee_amount` (already exists, used by Deliverables)
- `ServiceItems.fee_amount` (already exists, used by Deliverables)
- `ProjectServices.agreed_fee` (already exists)

### Backward Compatibility
- Old `billing_amount` field is still in database but no longer used for fee calculation
- Equal split now works even when `review_count_planned` is NULL (uses actual count)
- Items with NULL fees now return $0 instead of inheriting service fee (breaking change but correct)

## Future Enhancements

### Optional: Populate `review_count_planned`
Currently NULL for all services. Could be populated by:
```sql
UPDATE ProjectServices
SET review_count_planned = (
    SELECT COUNT(*) 
    FROM ServiceReviews sr 
    WHERE sr.service_id = ProjectServices.service_id
)
```

But this is NOT required - equal split works using `actual_review_count`.

### Optional: Add `fee_amount` Column Index
If performance becomes an issue:
```sql
CREATE INDEX idx_servicereview_fee_amount 
ON ServiceReviews(fee_amount) 
WHERE fee_amount IS NOT NULL;

CREATE INDEX idx_serviceitem_fee_amount 
ON ServiceItems(fee_amount) 
WHERE fee_amount IS NOT NULL;
```

## Verification Checklist

- [x] Finance endpoints return non-zero totals for projects with agreed fees
- [x] Reviews with explicit `fee_amount` show as `override` source
- [x] Reviews with NULL `fee_amount` calculate equal split
- [x] Equal split uses actual review count (not review_count_planned)
- [x] Items with explicit `fee_amount` show that value
- [x] Items with NULL `fee_amount` show $0 (no inheritance)
- [x] Total fees sum correctly across reviews and items
- [x] Deliverables tab fee edits update `fee_amount` column
- [ ] Unit tests updated to match new model
- [ ] Integration tests pass
