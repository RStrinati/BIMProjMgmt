# Deliverables Update - Quick Reference

## Endpoint

```
PATCH /api/projects/{project_id}/services/{service_id}/reviews/{review_id}
```

## Quick Curl Examples

### 1. Update Due Date
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"due_date": "2025-02-15"}' \
  http://localhost:5000/api/projects/1/services/5/reviews/10
```

**Response** (200 OK):
```json
{
  "review_id": 10,
  "service_id": 5,
  "project_id": 1,
  "due_date": "2025-02-15",
  "status": "pending",
  "invoice_reference": null,
  "invoice_date": null,
  "is_billed": false,
  "...": "... other fields ..."
}
```

---

### 2. Update Status
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"status": "in-progress"}' \
  http://localhost:5000/api/projects/1/services/5/reviews/10
```

---

### 3. Update Invoice Number
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"invoice_reference": "INV-2025-001-A"}' \
  http://localhost:5000/api/projects/1/services/5/reviews/10
```

---

### 4. Update Invoice Date
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"invoice_date": "2025-01-16"}' \
  http://localhost:5000/api/projects/1/services/5/reviews/10
```

---

### 5. Mark as Billed
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"is_billed": true}' \
  http://localhost:5000/api/projects/1/services/5/reviews/10
```

---

### 6. Mark as Not Billed
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"is_billed": false}' \
  http://localhost:5000/api/projects/1/services/5/reviews/10
```

---

### 7. Clear Due Date (set to null)
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"due_date": null}' \
  http://localhost:5000/api/projects/1/services/5/reviews/10
```

---

### 8. Clear Invoice Date (set to null)
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"invoice_date": null}' \
  http://localhost:5000/api/projects/1/services/5/reviews/10
```

---

### 9. Update Multiple Fields at Once
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

---

## Error Cases

### Invalid Project/Service/Review Combination
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}' \
  http://localhost:5000/api/projects/999/services/999/reviews/999
```

**Response** (404 Not Found):
```json
{
  "error": "Review not found in this project"
}
```

---

### Invalid Date Format
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"due_date": "15-02-2025"}' \
  http://localhost:5000/api/projects/1/services/5/reviews/10
```

**Response** (400 Bad Request):
```json
{
  "error": "Invalid date format '15-02-2025'. Expected YYYY-MM-DD."
}
```

---

### No Fields to Update
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"invalid_field": "value"}' \
  http://localhost:5000/api/projects/1/services/5/reviews/10
```

**Response** (400 Bad Request):
```json
{
  "error": "No valid fields to update"
}
```

---

## Valid Date Format

All dates must be in ISO 8601 format: **YYYY-MM-DD**

✅ Valid:
- `"2025-02-15"`
- `"2025-01-01"`
- `"2024-12-31"`

❌ Invalid:
- `"02-15-2025"` (MM-DD-YYYY)
- `"15-02-2025"` (DD-MM-YYYY)
- `"15/02/2025"` (slashes)
- `"2025-02-15T10:30:00"` (with time - use date only)

---

## Valid Status Values

Examples (any string max 60 chars):
- `"pending"`
- `"in-progress"`
- `"completed"`
- `"reviewed"`
- `"approved"`
- `"rejected"`
- `"on-hold"`

---

## Automatic Behavior

- ✅ When `status` is set to `"completed"`, `is_billed` is **not** automatically set (use explicit `is_billed` if needed)
- ✅ Status strings > 60 chars are automatically trimmed
- ✅ Status is trimmed of leading/trailing whitespace
- ✅ Extra fields in request are silently ignored
- ✅ Dates can be null to clear them
- ✅ Multiple fields update atomically in one transaction

---

## Testing Script

Run automated tests:

```bash
# Auto-discover test data and run all 9 test cases
python tools/verify_deliverables_update.py --discover

# Or use specific IDs
python tools/verify_deliverables_update.py \
  --project-id 1 \
  --service-id 5 \
  --review-id 10
```

Tests:
1. Update due_date to tomorrow
2. Update status to 'in-progress'
3. Update invoice_reference with timestamp
4. Update invoice_date to today
5. Set is_billed = true
6. Set is_billed = false
7. Clear invoice_date (null)
8. Clear due_date (null)
9. Update 3 fields at once

---

## PowerShell Examples

If using PowerShell instead of bash:

```powershell
$headers = @{"Content-Type" = "application/json"}
$body = ConvertTo-Json @{"status" = "completed"}

Invoke-RestMethod `
  -Uri "http://localhost:5000/api/projects/1/services/5/reviews/10" `
  -Method PATCH `
  -Headers $headers `
  -Body $body
```

---

## Python Example

Using `requests` library:

```python
import requests
import json

url = "http://localhost:5000/api/projects/1/services/5/reviews/10"
payload = {
    "status": "completed",
    "is_billed": True,
    "invoice_reference": "INV-2025-001",
    "invoice_date": "2025-01-16"
}

response = requests.patch(url, json=payload)
print(response.status_code)
print(json.dumps(response.json(), indent=2))
```

---

## JavaScript/Fetch Example

Using browser fetch API:

```javascript
const url = "http://localhost:5000/api/projects/1/services/5/reviews/10";
const payload = {
  status: "completed",
  is_billed: true,
  invoice_reference: "INV-2025-001",
  invoice_date: "2025-01-16"
};

fetch(url, {
  method: "PATCH",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload)
})
  .then(r => r.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));
```
