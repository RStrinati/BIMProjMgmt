# Fee Resolution End-to-End Trace

This document traces the complete flow of fee data from database to API response.

## Example: Review 5233 (Project 4, Service 187)

### Step 1: Database State

```sql
-- ServiceReviews row
SELECT 
    review_id,           -- 5233
    service_id,          -- 187
    fee_amount,          -- 6000.00
    is_user_modified,    -- 1 (True)
    deliverables         -- 'progress_report,issues'
FROM ServiceReviews
WHERE review_id = 5233;

-- ProjectServices row
SELECT 
    service_id,          -- 187
    project_id,          -- 4
    agreed_fee,          -- 90000.00
    review_count_planned -- NULL
FROM ProjectServices
WHERE service_id = 187;
```

### Step 2: API Request

```bash
GET /api/projects/4/finance/line-items
```

### Step 3: Financial Data Service Query

**File**: `services/financial_data_service.py`

**Query Executed**:
```sql
SELECT 
    sr.review_id as id,
    'review' as type,
    sr.service_id,
    ps.service_code,
    ps.service_name,
    sr.billing_phase as phase,
    COALESCE(sr.deliverables, '') as title,
    sr.planned_date,
    sr.due_date,
    sr.status,
    sr.fee_amount,              -- ✅ Uses fee_amount (not billing_amount)
    sr.is_user_modified,
    sr.invoice_status,
    sr.invoice_reference,
    sr.invoice_date,
    sr.invoice_month_final,
    sr.is_billed,
    ps.agreed_fee,
    ps.review_count_planned
FROM ServiceReviews sr
JOIN ProjectServices ps 
    ON sr.service_id = ps.service_id
WHERE ps.project_id = 4       -- ✅ Joins via ps.project_id (not sr.project_id which is NULL)
```

**Query Result** (for review 5233):
```python
{
    'id': 5233,
    'type': 'review',
    'service_id': 187,
    'service_code': 'CONST',
    'service_name': 'Construction Phase Reviews',
    'phase': 'CONST',
    'title': 'progress_report,issues',
    'fee_amount': 6000.00,       # ✅ User set this via Deliverables
    'is_user_modified': 1,       # ✅ Marked as modified
    'agreed_fee': 90000.00,
    'review_count_planned': None
}
```

### Step 4: Actual Review Count Calculation

**Code**:
```python
# Calculate actual review count per service for equal split
service_review_counts = {}
for row in reviews:
    row_dict = dict(zip(reviews_cols, row))
    service_id = row_dict.get(ServiceReviews.SERVICE_ID)
    service_review_counts[service_id] = service_review_counts.get(service_id, 0) + 1

# For Service 187: actual_review_count = 15 (counted from all 15 reviews)
```

### Step 5: Fee Resolution

**File**: `services/fee_resolver_service.py`

**Function**: `resolve_review_fee(review_row, service_row, actual_review_count)`

**Input**:
```python
review_row = {
    'review_id': 5233,
    'fee_amount': 6000.00,       # ✅ Set by user
    'is_user_modified': 1
}

service_row = {
    'agreed_fee': 90000.00,
    'review_count_planned': None
}

actual_review_count = 15
```

**Logic Flow**:
```python
# Step 1: Extract values
fee_amount = review_row.get(ServiceReviews.FEE_AMOUNT)  # 6000.00
is_user_modified = review_row.get(ServiceReviews.IS_USER_MODIFIED, 0)  # 1

# Step 2: Check if fee_amount is set
if fee_amount is not None:  # ✅ TRUE (6000.00 is not None)
    fee_amount_float = float(fee_amount)  # 6000.00
    
    # Step 3: Check if user modified
    if is_user_modified:  # ✅ TRUE (1)
        return (6000.00, 'override')  # ✅ RETURNS HERE
```

**Return Value**:
```python
(6000.00, 'override')
```

### Step 6: Response Construction

**Code**:
```python
line_item = {
    'type': 'review',
    'id': 5233,
    'service_id': 187,
    'service_code': 'CONST',
    'service_name': 'Construction Phase Reviews',
    'phase': 'CONST',
    'title': 'progress_report,issues',
    'fee': 6000.00,              # ✅ From fee resolver
    'fee_source': 'override',    # ✅ From fee resolver
    'invoice_status': None,
    'invoice_reference': None,
    'invoice_date': None,
    'invoice_month': '2024-01',
    'is_billed': 0
}
```

### Step 7: API Response

```json
{
  "project_id": 4,
  "line_items": [
    {
      "type": "review",
      "id": 5233,
      "service_id": 187,
      "service_code": "CONST",
      "service_name": "Construction Phase Reviews",
      "phase": "CONST",
      "title": "progress_report,issues",
      "planned_date": "2024-01-05",
      "due_date": "2024-01-12",
      "status": "complete",
      "fee": 6000.0,
      "fee_source": "override",
      "invoice_status": null,
      "invoice_reference": null,
      "invoice_date": null,
      "invoice_month": "2024-01",
      "is_billed": 0
    }
  ],
  "totals": {
    "total_fee": 111000.0,
    "billed_fee": 0.0,
    "outstanding_fee": 111000.0
  }
}
```

---

## Example 2: Review 5245 (Equal Split)

### Database State

```sql
-- ServiceReviews row
SELECT 
    review_id,           -- 5245
    service_id,          -- 187
    fee_amount,          -- NULL ✅
    is_user_modified,    -- 0 (False)
    deliverables         -- 'progress_report,issues'
FROM ServiceReviews
WHERE review_id = 5245;

-- Same ProjectServices row (Service 187)
```

### Fee Resolution Logic

**Input**:
```python
review_row = {
    'review_id': 5245,
    'fee_amount': None,          # ✅ NULL - not set by user
    'is_user_modified': 0
}

service_row = {
    'agreed_fee': 90000.00,
    'review_count_planned': None  # ✅ NULL in database
}

actual_review_count = 15         # ✅ Counted from actual reviews
```

**Logic Flow**:
```python
# Step 1: Extract values
fee_amount = review_row.get(ServiceReviews.FEE_AMOUNT)  # None
is_user_modified = review_row.get(ServiceReviews.IS_USER_MODIFIED, 0)  # 0

# Step 2: Check if fee_amount is set
if fee_amount is not None:  # ❌ FALSE (None is None)
    # Skipped

# Step 3: Calculate equal split
if service_row and actual_review_count and actual_review_count > 0:  # ✅ TRUE
    agreed_fee = float(service_row.get(ProjectServices.AGREED_FEE) or 0)  # 90000.00
    if agreed_fee > 0:  # ✅ TRUE
        fee = agreed_fee / actual_review_count  # 90000.00 / 15 = 6000.00
        return (6000.00, 'calculated_equal_split')  # ✅ RETURNS HERE
```

**Return Value**:
```python
(6000.00, 'calculated_equal_split')
```

---

## Example 3: Item 34 (NULL Fee)

### Database State

```sql
-- ServiceItems row
SELECT 
    item_id,             -- 34
    service_id,          -- 188
    fee_amount,          -- NULL ✅
    is_user_modified,    -- 0 (False)
    title                -- 'Example Deliverable'
FROM ServiceItems
WHERE item_id = 34;

-- ProjectServices row
SELECT 
    service_id,          -- 188
    agreed_fee           -- 93000.00
FROM ProjectServices
WHERE service_id = 188;
```

### Fee Resolution Logic

**Function**: `resolve_item_fee(item_row)`

**Input**:
```python
item_row = {
    'item_id': 34,
    'fee_amount': None,          # ✅ NULL - no fee set
    'is_user_modified': 0
}

# Note: service_row is NOT passed (items don't inherit)
```

**Logic Flow**:
```python
# Step 1: Extract values
fee_amount = item_row.get(ServiceItems.FEE_AMOUNT)  # None
is_user_modified = item_row.get(ServiceItems.IS_USER_MODIFIED, 0)  # 0

# Step 2: Check if fee_amount is set
if fee_amount is not None:  # ❌ FALSE (None is None)
    # Skipped

# Step 3: No inheritance - return 0
return (0.0, 'none')  # ✅ RETURNS HERE (no service inheritance!)
```

**Return Value**:
```python
(0.0, 'none')
```

**Response**:
```json
{
  "type": "item",
  "id": 34,
  "service_id": 188,
  "fee": 0.0,
  "fee_source": "none"
}
```

---

## Deliverables Tab Integration

### User Edits Fee in Deliverables

**UI Action**: User clicks on fee cell for Review 5233, changes from $6,000 to $7,500

**Frontend Request**:
```javascript
PATCH /api/projects/4/services/187/reviews/5233
Body: { "fee_amount": 7500 }
```

**Backend Handler** (`backend/app.py`):
```python
@app.route('/api/projects/<int:project_id>/services/<int:service_id>/reviews/<int:review_id>', methods=['PATCH'])
def api_update_service_review(project_id, service_id, review_id):
    body = request.get_json() or {}
    
    # fee_amount is in allowed_fields
    allowed_fields = {
        ..., 'fee_amount', ...
    }
    
    # Maps to database column
    field_mapping = {
        ...,
        'fee_amount': S.ServiceReviews.FEE_AMOUNT,
        ...
    }
    
    # Update database
    update_service_review(review_id, fee_amount=7500)
```

**Database Update**:
```sql
UPDATE ServiceReviews
SET fee_amount = 7500,
    is_user_modified = 1  -- ✅ Marked as user modified
WHERE review_id = 5233;
```

**Next API Call**:
```bash
GET /api/projects/4/finance/line-items
```

**New Response**:
```json
{
  "type": "review",
  "id": 5233,
  "fee": 7500.0,         # ✅ Updated value
  "fee_source": "override"
}
```

---

## Summary of Deterministic Model

| Scenario | Database State | Fee Calculation | Source |
|----------|----------------|-----------------|--------|
| **Review - User Edited** | `fee_amount = $6,000`<br>`is_user_modified = 1` | Use `fee_amount` | `override` |
| **Review - Equal Split** | `fee_amount = NULL`<br>`is_user_modified = 0` | `agreed_fee / actual_count`<br>= $90,000 / 15 = $6,000 | `calculated_equal_split` |
| **Item - Explicit Fee** | `fee_amount = $7,000`<br>`is_user_modified = 1` | Use `fee_amount` | `override` |
| **Item - No Fee** | `fee_amount = NULL`<br>`is_user_modified = 0` | Return $0<br>(NO service inheritance) | `none` |

## Verification

### Check Database Values
```bash
python tools/check_project4_reviews.py
```

### Check API Response
```bash
python tools/check_finance_api.py
```

### Check Deliverables Integration
1. Open Deliverables tab for Project 4
2. Edit fee for Review 5233
3. Verify finance endpoint returns updated value
4. Verify `fee_source = 'override'`
