# Deliverables PATCH Endpoint Documentation

**Endpoint**: `PATCH /api/projects/{project_id}/services/{service_id}/reviews/{review_id}`

**Purpose**: Enable editing of Deliverables fields from the Deliverables list by supporting partial updates on ServiceReviews.

## Supported Fields

All fields are optional. Only include fields you want to update.

| Field | Type | Description | Notes |
|-------|------|-------------|-------|
| `due_date` | ISO date string or null | When the deliverable is due | Format: `YYYY-MM-DD`, or null to clear |
| `status` | string | Delivery status | Max 60 chars, trimmed. Examples: `pending`, `in-progress`, `completed` |
| `invoice_reference` | string | Invoice/billing reference number | UI label: "Invoice Number". Any string. |
| `invoice_date` | ISO date string or null | Date the invoice was issued | Format: `YYYY-MM-DD`, or null to clear |
| `is_billed` | boolean | Whether this deliverable has been billed | UI label: "Billing Status" (displays "Billed"/"Not billed") |

## Request Format

```json
PATCH /api/projects/1/services/5/reviews/10
Content-Type: application/json

{
  "due_date": "2025-02-15",
  "status": "in-progress",
  "invoice_reference": "INV-2025-001",
  "invoice_date": "2025-01-16",
  "is_billed": true
}
```

### Field-by-Field Examples

#### 1. Update due_date (DATE)

```json
{
  "due_date": "2025-02-15"
}
```

Clear due_date:
```json
{
  "due_date": null
}
```

#### 2. Update status (string)

```json
{
  "status": "completed"
}
```

Valid status examples: `pending`, `in-progress`, `completed`, `reviewed`, `approved`

#### 3. Update invoice_reference (string)

```json
{
  "invoice_reference": "INV-2025-001-A"
}
```

#### 4. Update invoice_date (DATE)

```json
{
  "invoice_date": "2025-01-16"
}
```

Clear invoice_date:
```json
{
  "invoice_date": null
}
```

#### 5. Update is_billed (boolean)

Mark as billed:
```json
{
  "is_billed": true
}
```

Mark as not billed:
```json
{
  "is_billed": false
}
```

#### 6. Multiple Fields in One Request

```json
{
  "status": "completed",
  "is_billed": true,
  "invoice_reference": "INV-2025-001",
  "invoice_date": "2025-01-16"
}
```

## Response Format

**Success (200 OK)**: Returns the updated review object in the same format as `GET /api/projects/{id}/reviews`:

```json
{
  "review_id": 10,
  "service_id": 5,
  "project_id": 1,
  "cycle_no": 1,
  "planned_date": "2025-01-15",
  "due_date": "2025-02-15",
  "status": "completed",
  "disciplines": "Structural",
  "deliverables": "Design documents",
  "is_billed": true,
  "billing_amount": 5000.00,
  "invoice_reference": "INV-2025-001-A",
  "invoice_date": "2025-01-16",
  "service_name": "Design Review",
  "service_code": "DES-001",
  "phase": "Design"
}
```

### Possible Response Fields

- `review_id` (int): Unique review identifier
- `service_id` (int): Associated service ID
- `project_id` (int): Associated project ID
- `cycle_no` (int): Review cycle number
- `planned_date` (date): Planned review date
- `due_date` (date or null): Due date for deliverable
- `status` (string): Current status
- `disciplines` (string): Related disciplines
- `deliverables` (string): Deliverable description
- `is_billed` (boolean): Billing status
- `billing_amount` (float): Billing amount if applicable
- `invoice_reference` (string): Invoice number
- `invoice_date` (date or null): Invoice date
- `service_name` (string): Service name
- `service_code` (string): Service code
- `phase` (string): Project phase

## Error Responses

**400 Bad Request**: Invalid request (e.g., no fields to update, invalid date format)

```json
{
  "error": "No valid fields to update"
}
```

```json
{
  "error": "Invalid date format 'invalid-date'. Expected YYYY-MM-DD."
}
```

**404 Not Found**: Review not found in the specified project/service

```json
{
  "error": "Review not found in this project"
}
```

**500 Internal Server Error**: Database or processing error

```json
{
  "error": "Failed to update review"
}
```

## Validation Rules

- **Scope Validation**: Review must belong to the specified service and service must belong to the specified project. Invalid project_id/service_id/review_id combinations are rejected with 404.

- **Date Format**: ISO format `YYYY-MM-DD` only. Any other format will be logged and the field skipped (update continues with other fields).

- **Status Trimming**: Status strings longer than 60 characters are automatically truncated.

- **Boolean Conversion**: `is_billed` accepts any JSON boolean value and converts to 0 (false) or 1 (true) in database.

- **Null Handling**: All date fields accept null to clear the value.

- **Extra Fields**: Any fields not in the allowed list are silently ignored.

## Curl Examples

### Update single field

```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"due_date": "2025-02-15"}' \
  http://localhost:5000/api/projects/1/services/5/reviews/10
```

### Update multiple fields

```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "is_billed": true,
    "invoice_reference": "INV-2025-001",
    "invoice_date": "2025-01-16"
  }' \
  http://localhost:5000/api/projects/1/services/5/reviews/10
```

### Clear a date field

```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"invoice_date": null}' \
  http://localhost:5000/api/projects/1/services/5/reviews/10
```

### Toggle billing status

```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"is_billed": true}' \
  http://localhost:5000/api/projects/1/services/5/reviews/10
```

## Database Schema (ServiceReviews)

The underlying table contains these columns (relevant to this endpoint):

- `review_id` (INT, PK)
- `service_id` (INT, FK)
- `due_date` (DATE, nullable)
- `status` (NVARCHAR(60))
- `invoice_reference` (NVARCHAR(MAX))
- `invoice_date` (DATE, nullable)
- `is_billed` (BIT)

## Implementation Details

### Backend Changes

**File**: `database.py`
- Added `_parse_iso_date()` helper for date validation
- Extended `update_service_review()` to support invoice_date and improve validation
- Allowed fields now include: due_date, status, invoice_reference, invoice_date, is_billed

**File**: `backend/app.py`
- Enhanced `api_update_service_review()` endpoint to:
  - Validate project scope (review must belong to service in project)
  - Filter to only allowed fields
  - Return updated review in same format as GET
  - Handle date parsing with ISO format validation
  - Return 404 for invalid scope
  - Return 400 for invalid input

### Constants Used

All database table/column references use `constants/schema.py`:
- `ServiceReviews.TABLE`, `ServiceReviews.REVIEW_ID`, `ServiceReviews.SERVICE_ID`, etc.
- `ProjectServices.TABLE`, `ProjectServices.PROJECT_ID`, `ProjectServices.SERVICE_ID`, etc.

## Testing

Run the verification script to test all 5 fields:

```bash
python tools/verify_deliverables_update.py --discover
```

Or with specific IDs:

```bash
python tools/verify_deliverables_update.py --project-id 1 --service-id 5 --review-id 10
```

The script tests:
1. Update due_date
2. Update status
3. Update invoice_reference
4. Update invoice_date
5. Toggle is_billed (true/false)
6. Clear dates (set to null)
7. Multiple fields in one request

## Notes

- All updates use SQL Server connection pooling via `database_pool.py`
- Response always returns the complete updated review object (same as GET)
- Invalid date formats are logged and skipped; other fields continue to update
- Status auto-alignment with is_billed is disabled for explicit PATCH updates (respects manual is_billed value)
