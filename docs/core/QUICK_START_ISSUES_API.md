# Quick Start Guide - Reconciled Issues API

**Status**: ✅ Ready for Integration  
**Date**: January 2025

---

## 30-Second Summary

New API endpoint delivers **all ACC and Revizto issues** with human-friendly IDs:
- **URL**: `GET /api/issues/table`
- **Display IDs**: `ACC-924`, `ACC-66C8A7AA`, `REV-12345`
- **Total Issues**: 12,840 (4,748 ACC + 8,092 Revizto)
- **Tested**: ✅ 15 integration tests passing

---

## Start Using the API

### 1. Simple Request
```bash
curl "http://localhost:5000/api/issues/table"
```

**Response**: First 50 issues with display_ids, pagination info

### 2. Filter by Source System
```bash
# Get only ACC issues
curl "http://localhost:5000/api/issues/table?source_system=ACC"

# Get only Revizto issues
curl "http://localhost:5000/api/issues/table?source_system=Revizto"
```

### 3. Search for Specific Issue
```bash
# Find issue by display_id
curl "http://localhost:5000/api/issues/table?search=ACC-924"

# Find issues by title keyword
curl "http://localhost:5000/api/issues/table?search=clash+detection"
```

### 4. Filter & Paginate
```bash
# Revizto issues only, page 2, 100 per page
curl "http://localhost:5000/api/issues/table?source_system=Revizto&page=2&page_size=100"

# Open ACC issues, sorted by priority
curl "http://localhost:5000/api/issues/table?source_system=ACC&status_normalized=Open&sort_by=priority_normalized&sort_dir=asc"
```

---

## Response Format

```json
{
  "page": 1,
  "page_size": 50,
  "total_count": 12840,
  "rows": [
    {
      "issue_key": "ACC-924",
      "display_id": "ACC-924",
      "source_system": "ACC",
      "acc_issue_number": 924,
      "title": "Fix clash in HVAC model",
      "status_normalized": "Open",
      "priority_normalized": "High",
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2025-01-20T14:45:00",
      ... (25 total columns)
    }
  ]
}
```

---

## Key Display ID Formats

| Type | Format | Example | Count |
|------|--------|---------|-------|
| ACC (mapped) | ACC-<number> | ACC-924 | 3,696 |
| ACC (unmapped) | ACC-<prefix> | ACC-66C8A7AA | 1,052 |
| Revizto | REV-<id> | REV-12345 | 8,092 |

---

## Available Query Parameters

```
- source_system:        'ACC' or 'Revizto'
- status_normalized:    'Open', 'Closed', etc.
- priority_normalized:  'High', 'Medium', 'Low', etc.
- discipline_normalized: discipline name
- assignee_user_key:    user identifier
- search:               substring in title/display_id/issue_key
- page:                 page number (default 1)
- page_size:            items per page (default 50, max 500)
- sort_by:              column name for sorting
- sort_dir:             'asc' or 'desc' (default 'desc')
```

---

## React Frontend Example

```javascript
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

function IssuesTable() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    source_system: 'ACC',
    status_normalized: 'Open'
  });

  const { data, isLoading } = useQuery({
    queryKey: ['issues', page, filters],
    queryFn: async () => {
      const params = new URLSearchParams({ ...filters, page });
      const res = await fetch(`/api/issues/table?${params}`);
      return res.json();
    }
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <table>
        <thead>
          <tr>
            <th>Display ID</th>
            <th>Title</th>
            <th>Status</th>
            <th>Priority</th>
          </tr>
        </thead>
        <tbody>
          {data.rows.map(issue => (
            <tr key={issue.issue_key}>
              <td>{issue.display_id}</td>
              <td>{issue.title}</td>
              <td>{issue.status_normalized}</td>
              <td>{issue.priority_normalized}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div>
        Page {page} of {Math.ceil(data.total_count / data.page_size)}
      </div>
    </div>
  );
}
```

---

## Verification

### Check View Exists
```sql
SELECT COUNT(*) FROM dbo.vw_Issues_Reconciled;
-- Result: 12,840 ✅
```

### Check API Endpoint
```bash
curl -s "http://localhost:5000/api/issues/table?page_size=1" | jq '.total_count'
# Result: 12840 ✅
```

### Run Tests
```bash
python -m pytest tests/test_vw_issues_reconciled_live.py -v
# Result: 15 passed ✅
```

---

## Troubleshooting

**Q: Endpoint returns error?**  
A: Check Flask is running (`python backend/app.py`). Check database connection in config.py.

**Q: No results from search?**  
A: Search uses substring match. Try broader search term.

**Q: Too many results for filter?**  
A: Use pagination (`page`, `page_size`) or add more filters.

**Q: Need different column?**  
A: Endpoint returns 25+ columns from view. Check full response JSON.

---

## Related Documentation

- **Full API Docs**: [EXECUTION_MISSION_COMPLETE.md](EXECUTION_MISSION_COMPLETE.md) (Task 2 section)
- **Test Suite**: [tests/test_vw_issues_reconciled_live.py](../tests/test_vw_issues_reconciled_live.py)
- **Warehouse Guide**: [WAREHOUSE_BACKFILL_GUIDE.md](WAREHOUSE_BACKFILL_GUIDE.md) (Phase 5 follow-up)

---

**Status**: ✅ Production Ready  
**Tests**: 15/15 Passing  
**Performance**: <1 second per request
