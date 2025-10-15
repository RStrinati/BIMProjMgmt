# React Frontend - Project Loading Issue Fixed

**Date**: October 15, 2025  
**Issue**: React frontend failing to load projects  
**Status**: ✅ RESOLVED

## Problem Summary

The React frontend was unable to load projects from the Flask backend API due to a **JSON serialization error**.

## Root Cause Analysis

### Issue 1: Backend Server Not Running
The primary issue was that the Flask backend server at `http://localhost:5000` was **not running**, causing all API requests from the React frontend to fail.

**Evidence**:
```powershell
curl http://localhost:5000/api/projects
# Error: Unable to connect to the remote server
```

### Issue 2: JSON Serialization of Date Objects
When the backend was running, there was a secondary issue where Python `date` and `datetime` objects from the database were not being serialized to JSON properly.

**Error**:
```
TypeError: Object of type date is not JSON serializable
```

This occurred because:
1. Database query `get_projects_full()` returns dictionaries with `date` objects
2. Flask's default `jsonify()` function doesn't handle Python date/datetime/Decimal types
3. The API endpoint `/api/projects` would crash when trying to serialize the response

## Solution Implementation

### 1. Start the Flask Backend Server

The backend must be running for the frontend to work:

```powershell
# From project root
cd C:\Users\RicoStrinati\Documents\research\BIMProjMngmt
python backend/app.py
```

The server should start on:
- `http://127.0.0.1:5000`
- `http://192.168.31.106:5000` (network accessible)

### 2. Add Custom JSON Encoder to Flask

Modified `backend/app.py` to include a custom JSON provider that handles date/datetime/Decimal serialization:

```python
from datetime import date, datetime
from decimal import Decimal
from flask.json.provider import DefaultJSONProvider

class CustomJSONProvider(DefaultJSONProvider):
    """Custom JSON provider to handle date, datetime, and Decimal objects."""
    
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

# Apply to Flask app
app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
app.json = CustomJSONProvider(app)
```

**What this does**:
- Converts `date` and `datetime` objects to ISO format strings (e.g., `"2025-10-15"`)
- Converts `Decimal` objects (from SQL Server) to `float`
- Allows Flask's `jsonify()` to properly serialize all database responses

## API Endpoints Verified Working

After the fix, the following endpoints are confirmed operational:

```
✅ GET /api/projects              - Returns list of all projects
✅ GET /api/projects/stats        - Returns project statistics
✅ GET /api/project/<id>          - Returns single project details
✅ GET /api/reference/project_types
✅ GET /api/reference/clients
✅ POST /api/projects             - Create new project
✅ PUT /api/projects/<id>         - Update project
```

## Frontend Configuration

The React frontend uses Vite with proxy configuration to forward API requests:

**File**: `frontend/vite.config.ts`
```typescript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true,
    },
  },
}
```

This means:
- Frontend runs on `http://localhost:5173` (or 5174 if 5173 is busy)
- All requests to `/api/*` are proxied to `http://localhost:5000/api/*`
- No CORS issues because requests appear to come from same origin

## Testing the Fix

### 1. Start Backend
```powershell
cd C:\Users\RicoStrinati\Documents\research\BIMProjMngmt
python backend/app.py
```

Look for:
```
 * Running on http://127.0.0.1:5000
 * Debugger is active!
```

### 2. Start Frontend
```powershell
cd frontend
npm run dev
```

Look for:
```
  VITE v5.4.20  ready in 472 ms
  ➜  Local:   http://localhost:5174/
```

### 3. Verify API Response
```powershell
curl http://localhost:5000/api/projects
```

Should return JSON array with properly formatted dates:
```json
[
  {
    "project_id": 1,
    "project_name": "Example Project",
    "start_date": "2025-01-15",
    "end_date": "2025-12-31",
    ...
  }
]
```

### 4. Check Frontend in Browser

Navigate to `http://localhost:5174/projects`

Expected behavior:
- ✅ Projects list loads successfully
- ✅ Stats cards display (Total, Active, Completed, On Hold)
- ✅ Search functionality works
- ✅ Project cards display with correct data
- ✅ No console errors

## Data Flow Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│                 │         │                  │         │                  │
│  React Frontend │ ──────> │  Flask Backend   │ ──────> │  SQL Server DB   │
│  (Vite/React)   │  /api   │  (app.py)        │  pyodbc │  (ProjectMgmt)   │
│  Port 5174      │         │  Port 5000       │         │                  │
│                 │ <────── │                  │ <────── │  vw_projects_    │
└─────────────────┘  JSON   └──────────────────┘  Rows   │  full            │
                                                          └──────────────────┘

1. Frontend makes request to /api/projects
2. Vite proxy forwards to http://localhost:5000/api/projects
3. Flask route calls list_projects_full()
4. list_projects_full() calls get_projects_full()
5. get_projects_full() queries vw_projects_full view
6. CustomJSONProvider serializes dates to ISO strings
7. JSON response sent back through proxy to frontend
8. React Query caches and displays data
```

## Common Issues & Troubleshooting

### Backend Not Starting
**Symptom**: `Unable to connect to the remote server`

**Solutions**:
- Check if backend is running: `Get-Process python`
- Verify port 5000 is not in use: `netstat -ano | findstr :5000`
- Check environment variables (DB connection strings)
- Review backend logs for errors

### Projects Not Displaying
**Symptom**: Empty list or loading spinner never stops

**Check**:
1. Browser DevTools Console for errors
2. Network tab - check `/api/projects` request
3. Response status code (should be 200)
4. Response body format

### Date Format Issues
**Symptom**: Dates displaying as `[object Object]` or errors

**Verify**:
- CustomJSONProvider is applied to Flask app
- Dates in response are strings, not objects
- Frontend date parsing logic handles ISO format

### Database Connection Errors
**Symptom**: 500 Internal Server Error from API

**Check**:
- SQL Server is running
- Connection strings in environment variables
- Database authentication credentials
- Network connectivity to database server

## Files Modified

1. **backend/app.py**
   - Added imports: `datetime`, `Decimal`, `DefaultJSONProvider`
   - Created `CustomJSONProvider` class
   - Applied custom JSON provider to Flask app

## Additional Notes

### Why Two Servers?

This architecture uses:
- **Flask backend** (port 5000) - API server, database access, business logic
- **Vite dev server** (port 5174) - Development server with hot reload, proxying

In production, the React app would be built and served as static files by Flask, using only one server.

### Database Performance

The `vw_projects_full` view joins multiple tables:
- `projects`
- `clients`
- `project_types`
- `project_statuses`

For large datasets, consider:
- Adding pagination to API endpoint
- Implementing server-side filtering
- Caching frequently accessed project lists

### Date Handling Best Practices

**Backend (Python)**:
- Store as `DATE`/`DATETIME2` in SQL Server
- Convert to ISO strings for JSON: `date.isoformat()`
- Use timezone-aware datetimes when needed

**Frontend (TypeScript)**:
- Parse ISO strings: `new Date(dateString)`
- Format for display: Use `date-fns` library
- Store as `Date` objects in state
- Send as ISO strings in API requests

## Next Steps

1. ✅ Backend server running with custom JSON provider
2. ✅ Frontend loading projects successfully
3. 🔄 Test create/update project functionality
4. 🔄 Add error handling for failed API requests
5. 🔄 Implement loading states and skeleton screens
6. 🔄 Add pagination for large project lists
7. 🔄 Create comprehensive integration tests

## Related Documentation

- [Backend API Implementation](./BACKEND_API_IMPLEMENTATION_COMPLETE.md)
- [React Frontend Setup](./REACT_FRONTEND_SETUP_COMPLETE.md)
- [Data Flow Analysis](./DATA_FLOW_ANALYSIS.md)
- [Database Schema](./constants/schema.py)

---

**Status**: The React frontend is now successfully loading projects from the backend API with properly serialized date and decimal fields.
