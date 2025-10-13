# Quick Start: Testing Data Import APIs

**5-Minute Guide to Test Backend Endpoints**

---

## Step 1: Start Backend Server

```powershell
# Navigate to project directory
cd C:\Users\RicoStrinati\Documents\research\BIMProjMngmt

# Activate virtual environment (if using one)
.\.venv\Scripts\Activate.ps1

# Start backend
python backend/app.py
```

**Expected Output**:
```
 * Running on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
```

---

## Step 2: Verify Server Running

```powershell
curl http://localhost:5000/api/projects
```

**Expected**: JSON array of projects

---

## Step 3: Test ACC Desktop Connector Endpoints

### A. Save Folder Path
```powershell
curl -X POST http://localhost:5000/api/projects/1/acc-connector-folder `
  -H "Content-Type: application/json" `
  -d "{`"folder_path`": `"C:/TestFolder`"}"
```

**Expected**:
```json
{
  "success": true,
  "project_id": 1,
  "folder_path": "C:/TestFolder"
}
```

### B. Get Folder Path
```powershell
curl http://localhost:5000/api/projects/1/acc-connector-folder
```

**Expected**:
```json
{
  "project_id": 1,
  "folder_path": "C:/TestFolder",
  "exists": false
}
```

### C. Extract Files (requires existing folder)
```powershell
curl -X POST http://localhost:5000/api/projects/1/acc-connector-extract
```

**Expected** (if folder doesn't exist):
```json
{
  "error": "Desktop Connector folder does not exist: C:/TestFolder"
}
```

### D. Get Extracted Files
```powershell
curl http://localhost:5000/api/projects/1/acc-connector-files
```

---

## Step 4: Test ACC Issues Endpoints

### Get All Issues
```powershell
curl http://localhost:5000/api/projects/1/acc-issues
```

### Get Issue Statistics
```powershell
curl http://localhost:5000/api/projects/1/acc-issues/stats
```

---

## Step 5: Test Revizto Endpoints

### Start Extraction
```powershell
curl -X POST http://localhost:5000/api/revizto/start-extraction `
  -H "Content-Type: application/json" `
  -d "{`"export_folder`": `"C:/Test`", `"notes`": `"Test`"}"
```

### Get Extraction Runs
```powershell
curl http://localhost:5000/api/revizto/extraction-runs
```

### Get Last Run
```powershell
curl http://localhost:5000/api/revizto/extraction-runs/last
```

---

## Step 6: Test Health Check Endpoints

### Get Health Files
```powershell
curl http://localhost:5000/api/projects/1/health-files
```

### Get Health Summary
```powershell
curl http://localhost:5000/api/projects/1/health-summary
```

---

## Common Issues & Solutions

### Issue: "Connection refused"
**Solution**: Backend server not running. Start with `python backend/app.py`

### Issue: "Database connection failed"
**Solution**: Check environment variables (DB_SERVER, DB_USER, DB_PASSWORD)

### Issue: "No folder configured"
**Solution**: First save folder path using POST endpoint

### Issue: "Folder does not exist"
**Solution**: Create folder or use valid path

---

## Using Postman Instead of cURL

1. **Create Collection**: "BIM Data Imports"
2. **Set Base URL**: Variable `{{base_url}}` = `http://localhost:5000`
3. **Import Endpoints**: Use URLs from API reference doc
4. **Test**: Send requests and inspect responses

---

## Next: Build React Components

Once endpoints are tested and working:

1. Create React components in `frontend/src/components/data-imports/`
2. Use `fetch()` or `axios` to call endpoints
3. Implement UI for each feature
4. Add error handling and loading states

**Reference**: See `REACT_DATA_IMPORTS_IMPLEMENTATION_ROADMAP.md` for component specs

---

**Need Help?**
- API Docs: `docs/DATA_IMPORTS_API_REFERENCE.md`
- Implementation: `docs/BACKEND_API_IMPLEMENTATION_COMPLETE.md`
- Roadmap: `docs/REACT_DATA_IMPORTS_IMPLEMENTATION_ROADMAP.md`
