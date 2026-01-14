# Data Imports API Reference

**Complete API documentation for all 5 data import features**

**Status**: ✅ **ALL ENDPOINTS IMPLEMENTED** (October 13, 2025)

---

## Table of Contents

1. [ACC Desktop Connector Endpoints](#acc-desktop-connector-endpoints)
2. [ACC Data Import Endpoints](#acc-data-import-endpoints)
3. [ACC Issues Display Endpoints](#acc-issues-display-endpoints)
4. [Revizto Import Endpoints](#revizto-import-endpoints)
5. [Revit Health Check Endpoints](#revit-health-check-endpoints)
6. [Testing Guide](#testing-guide)
7. [Error Handling](#error-handling)

---

## ACC Desktop Connector Endpoints

### 1. Get Desktop Connector Folder Path

**GET** `/api/projects/<project_id>/acc-connector-folder`

Get the configured ACC Desktop Connector folder path for a project.

**Response**:
```json
{
  "project_id": 1,
  "folder_path": "C:/ACC/Project123",
  "exists": true
}
```

**cURL Example**:
```bash
curl http://localhost:5000/api/projects/1/acc-connector-folder
```

---

### 2. Save Desktop Connector Folder Path

**POST** `/api/projects/<project_id>/acc-connector-folder`

Save the ACC Desktop Connector folder path for a project.

**Request Body**:
```json
{
  "folder_path": "C:/ACC/Project123"
}
```

**Response**:
```json
{
  "success": true,
  "project_id": 1,
  "folder_path": "C:/ACC/Project123"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:5000/api/projects/1/acc-connector-folder \
  -H "Content-Type: application/json" \
  -d "{\"folder_path\": \"C:/ACC/Project123\"}"
```

---

### 3. Extract Files from Desktop Connector

**POST** `/api/projects/<project_id>/acc-connector-extract`

Extract all files from the Desktop Connector folder and insert metadata into `tblACCDocs`.

**Behavior**:
- Deletes existing records for the project
- Recursively scans folder
- Extracts file metadata (name, path, type, size, modified date)
- Inserts into `ProjectManagement.dbo.tblACCDocs`

**Response**:
```json
{
  "success": true,
  "project_id": 1,
  "files_processed": 120,
  "execution_time_seconds": 15.3
}
```

**Error Responses**:
- `400`: No folder configured or folder doesn't exist
- `500`: Extraction failed

**cURL Example**:
```bash
curl -X POST http://localhost:5000/api/projects/1/acc-connector-extract \
  -H "Content-Type: application/json"
```

---

### 4. Get Extracted Files

**GET** `/api/projects/<project_id>/acc-connector-files`

Get paginated list of files extracted from Desktop Connector.

**Query Parameters**:
- `limit` (int, default: 100) - Number of files per page
- `offset` (int, default: 0) - Offset for pagination
- `file_type` (string, optional) - Filter by file type (e.g., "Revit", "CAD", "IFC")

**Response**:
```json
{
  "files": [
    {
      "id": 1,
      "file_name": "Building_A.rvt",
      "file_path": "C:/ACC/Project123/Building_A.rvt",
      "file_type": "Revit",
      "file_size_kb": 45678.23,
      "date_modified": "2024-10-01T14:30:00",
      "created_at": "2024-10-13T10:15:00"
    }
  ],
  "total_count": 120,
  "page": 1,
  "page_size": 100
}
```

**cURL Examples**:
```bash
# Get first page
curl "http://localhost:5000/api/projects/1/acc-connector-files"

# Get second page with limit 50
curl "http://localhost:5000/api/projects/1/acc-connector-files?limit=50&offset=50"

# Filter by Revit files only
curl "http://localhost:5000/api/projects/1/acc-connector-files?file_type=Revit"
```

---

## ACC Data Import Endpoints

### 5. Get ACC Data Folder Path

**GET** `/api/projects/<project_id>/acc-data-folder`

Get the configured ACC data export folder path.

**Response**:
```json
{
  "project_id": 1,
  "folder_path": "C:/ACC/Exports/Project123",
  "exists": true
}
```

---

### 6. Save ACC Data Folder Path

**POST** `/api/projects/<project_id>/acc-data-folder`

Save the ACC data export folder path.

**Request Body**:
```json
{
  "folder_path": "C:/ACC/Exports/Project123"
}
```

**Response**:
```json
{
  "success": true,
  "project_id": 1,
  "folder_path": "C:/ACC/Exports/Project123"
}
```

---

### 7. Import ACC Data (CSV/ZIP)

**POST** `/api/projects/<project_id>/acc-data-import`

Import ACC data export (CSV/ZIP files) to `acc_data_schema` database.

**Request Body** (optional):
```json
{
  "folder_path": "C:/ACC/Exports/Project123"
}
```

**Note**: If `folder_path` is not provided, uses saved folder path from database.

**Behavior**:
- Imports 20+ CSV files to `acc_data_schema` staging tables
- Runs merge scripts to update main tables
- Logs import to database
- Handles issues, projects, users, custom attributes

**Response**:
```json
{
  "success": true,
  "project_id": 1,
  "folder_path": "C:/ACC/Exports/Project123",
  "execution_time_seconds": 45.8,
  "message": "ACC data imported successfully"
}
```

**Error Responses**:
- `400`: No folder configured or folder doesn't exist
- `500`: Import failed

**cURL Example**:
```bash
curl -X POST http://localhost:5000/api/projects/1/acc-data-import \
  -H "Content-Type: application/json" \
  -d "{\"folder_path\": \"C:/ACC/Exports/Project123\"}"
```

---

### 8. Get ACC Import Logs

**GET** `/api/projects/<project_id>/acc-data-import-logs`

Get ACC data import history for project.

**Response**:
```json
{
  "logs": [
    {
      "id": 1,
      "project_id": 1,
      "folder_name": "Project123",
      "summary": "Imported ACC data from C:/ACC/Exports/Project123 in 45.80s",
      "imported_at": "2024-10-13T10:30:00"
    }
  ]
}
```

**cURL Example**:
```bash
curl http://localhost:5000/api/projects/1/acc-data-import-logs
```

---

## ACC Issues Display Endpoints

### 9. Get ACC Issues

**GET** `/api/projects/<project_id>/acc-issues`

Get ACC issues from `acc_data_schema.dbo.vw_issues_expanded_pm` view.

**Query Parameters**:
- `limit` (int, default: 100) - Number of issues per page
- `offset` (int, default: 0) - Offset for pagination
- `status` (string, optional) - Filter by status (e.g., "Open", "Closed")
- `priority` (string, optional) - Filter by priority (e.g., "High", "Medium", "Low")
- `assigned_to` (string, optional) - Filter by assignee

**Response**:
```json
{
  "issues": [
    {
      "issue_id": "abc-123",
      "title": "Structural beam interference",
      "description": "Beam clashes with MEP duct",
      "status": "Open",
      "priority": "High",
      "assigned_to": "John Doe",
      "created_at": "2024-10-01T09:00:00",
      "due_date": "2024-10-15T17:00:00",
      "owner": "Jane Smith",
      "project_name": "Project 123"
    }
  ],
  "total_count": 45,
  "page": 1,
  "page_size": 100
}
```

**cURL Examples**:
```bash
# Get all issues
curl "http://localhost:5000/api/projects/1/acc-issues"

# Get open issues only
curl "http://localhost:5000/api/projects/1/acc-issues?status=Open"

# Get high priority issues
curl "http://localhost:5000/api/projects/1/acc-issues?priority=High"

# Get issues assigned to specific user
curl "http://localhost:5000/api/projects/1/acc-issues?assigned_to=John%20Doe"

# Combined filters with pagination
curl "http://localhost:5000/api/projects/1/acc-issues?status=Open&priority=High&limit=20&offset=0"
```

---

### 10. Get ACC Issues Statistics

**GET** `/api/projects/<project_id>/acc-issues/stats`

Get ACC issues statistics (counts by status and priority).

**Response**:
```json
{
  "total_issues": 45,
  "by_status": {
    "Open": 20,
    "In Progress": 15,
    "Closed": 10
  },
  "by_priority": {
    "High": 8,
    "Medium": 25,
    "Low": 12
  }
}
```

**cURL Example**:
```bash
curl http://localhost:5000/api/projects/1/acc-issues/stats
```

---

## Revizto Import Endpoints

### 11. Start Revizto Extraction

**POST** `/api/revizto/start-extraction`

Start a Revizto data extraction run.

**Request Body**:
```json
{
  "export_folder": "C:/Revizto/Exports/Project123",
  "notes": "Weekly extraction for Project 123"
}
```

**Response**:
```json
{
  "success": true,
  "run_id": 42,
  "export_folder": "C:/Revizto/Exports/Project123",
  "notes": "Weekly extraction for Project 123"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:5000/api/revizto/start-extraction \
  -H "Content-Type: application/json" \
  -d "{\"export_folder\": \"C:/Revizto/Exports/Project123\", \"notes\": \"Weekly extraction\"}"
```

---

### 12. Get Revizto Extraction Runs

**GET** `/api/revizto/extraction-runs`

Get Revizto extraction run history.

**Query Parameters**:
- `limit` (int, default: 50) - Number of runs to return

**Response**:
```json
{
  "runs": [
    {
      "run_id": 42,
      "export_folder": "C:/Revizto/Exports/Project123",
      "notes": "Weekly extraction for Project 123",
      "started_at": "2024-10-13T10:00:00",
      "completed_at": "2024-10-13T10:15:00",
      "status": "Completed",
      "issues_extracted": 35
    }
  ]
}
```

**cURL Example**:
```bash
curl "http://localhost:5000/api/revizto/extraction-runs?limit=20"
```

---

### 13. Get Last Revizto Extraction Run

**GET** `/api/revizto/extraction-runs/last`

Get the most recent Revizto extraction run.

**Response**:
```json
{
  "run_id": 42,
  "export_folder": "C:/Revizto/Exports/Project123",
  "notes": "Weekly extraction for Project 123",
  "started_at": "2024-10-13T10:00:00",
  "completed_at": "2024-10-13T10:15:00",
  "status": "Completed",
  "issues_extracted": 35
}
```

**Error Response**:
- `404`: No extraction runs found

**cURL Example**:
```bash
curl http://localhost:5000/api/revizto/extraction-runs/last
```

---

## Revit Health Check Endpoints

### 14. Import Revit Health Data

**POST** `/api/projects/<project_id>/health-import`

Import Revit health check data file.

**Request Body**:
```json
{
  "file_path": "C:/Health/Project123_Health.xlsx"
}
```

**Response**:
```json
{
  "success": true,
  "project_id": 1,
  "file_path": "C:/Health/Project123_Health.xlsx",
  "execution_time_seconds": 8.5,
  "message": "Health data imported successfully"
}
```

**Error Responses**:
- `400`: file_path is required or file doesn't exist
- `500`: Import failed

**cURL Example**:
```bash
curl -X POST http://localhost:5000/api/projects/1/health-import \
  -H "Content-Type: application/json" \
  -d "{\"file_path\": \"C:/Health/Project123_Health.xlsx\"}"
```

---

### 15. Get Health Check Files

**GET** `/api/projects/<project_id>/health-files`

Get list of health check files for project.

**Response**:
```json
{
  "files": [
    {
      "file_id": 1,
      "file_name": "Project123_Health.xlsx",
      "file_path": "C:/Health/Project123_Health.xlsx",
      "imported_at": "2024-10-13T09:00:00",
      "checks_count": 150
    }
  ]
}
```

**cURL Example**:
```bash
curl http://localhost:5000/api/projects/1/health-files
```

---

### 16. Get Health Check Summary

**GET** `/api/projects/<project_id>/health-summary`

Get health check summary statistics.

**Response**:
```json
{
  "total_checks": 150,
  "passed": 120,
  "failed": 20,
  "warnings": 10
}
```

**cURL Example**:
```bash
curl http://localhost:5000/api/projects/1/health-summary
```

---

## Testing Guide

### Prerequisites

1. **Start Backend Server**:
```bash
cd C:/Users/RicoStrinati/Documents/research/BIMProjMngmt
python backend/app.py
```

2. **Verify Server Running**:
```bash
curl http://localhost:5000/api/projects
```

### Testing with cURL (Windows PowerShell)

**Note**: In PowerShell, use backtick (`) for line continuation instead of backslash (\).

#### Test ACC Desktop Connector Flow

```powershell
# 1. Save folder path
curl -X POST http://localhost:5000/api/projects/1/acc-connector-folder `
  -H "Content-Type: application/json" `
  -d "{`"folder_path`": `"C:/TestFolder`"}"

# 2. Get folder path
curl http://localhost:5000/api/projects/1/acc-connector-folder

# 3. Extract files (if folder exists)
curl -X POST http://localhost:5000/api/projects/1/acc-connector-extract

# 4. Get extracted files
curl http://localhost:5000/api/projects/1/acc-connector-files
```

#### Test ACC Data Import Flow

```powershell
# 1. Save data folder path
curl -X POST http://localhost:5000/api/projects/1/acc-data-folder `
  -H "Content-Type: application/json" `
  -d "{`"folder_path`": `"C:/ACC/Exports`"}"

# 2. Import data (if folder exists with CSV files)
curl -X POST http://localhost:5000/api/projects/1/acc-data-import

# 3. Get import logs
curl http://localhost:5000/api/projects/1/acc-data-import-logs
```

#### Test ACC Issues Display

```powershell
# 1. Get all issues
curl http://localhost:5000/api/projects/1/acc-issues

# 2. Get open issues
curl "http://localhost:5000/api/projects/1/acc-issues?status=Open"

# 3. Get statistics
curl http://localhost:5000/api/projects/1/acc-issues/stats
```

#### Test Revizto Import

```powershell
# 1. Start extraction
curl -X POST http://localhost:5000/api/revizto/start-extraction `
  -H "Content-Type: application/json" `
  -d "{`"export_folder`": `"C:/Revizto/Test`", `"notes`": `"Test run`"}"

# 2. Get runs history
curl http://localhost:5000/api/revizto/extraction-runs

# 3. Get last run
curl http://localhost:5000/api/revizto/extraction-runs/last
```

#### Test Revit Health Check

```powershell
# 1. Import health data (if file exists)
curl -X POST http://localhost:5000/api/projects/1/health-import `
  -H "Content-Type: application/json" `
  -d "{`"file_path`": `"C:/Health/test.xlsx`"}"

# 2. Get health files
curl http://localhost:5000/api/projects/1/health-files

# 3. Get health summary
curl http://localhost:5000/api/projects/1/health-summary
```

### Testing with Postman

1. **Import Collection**: Create a new Postman collection named "BIM Data Imports"

2. **Set Base URL**: Create environment variable `base_url = http://localhost:5000`

3. **Add Requests**: Use the endpoint URLs from this document

4. **Test Scenarios**:
   - Valid inputs
   - Missing required fields
   - Non-existent project IDs
   - Invalid folder paths
   - Invalid file paths
   - Pagination edge cases (offset > total)

---

## Error Handling

### Standard Error Response Format

All endpoints return errors in this format:

```json
{
  "error": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- **200 OK**: Request succeeded
- **201 Created**: Resource created successfully
- **400 Bad Request**: Missing required fields or invalid input
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side error (database connection, file I/O, etc.)
- **502 Bad Gateway**: External service unavailable (proxy endpoints)

### Common Error Scenarios

#### 400 Bad Request Examples

```json
// Missing required field
{
  "error": "folder_path is required"
}

// Folder doesn't exist
{
  "error": "Desktop Connector folder does not exist: C:/NonExistent"
}

// No folder configured
{
  "error": "No Desktop Connector folder configured for this project"
}
```

#### 500 Internal Server Error Examples

```json
// Database connection failed
{
  "error": "Database connection failed"
}

// File extraction failed
{
  "error": "File extraction failed"
}

// Import error with details
{
  "error": "Failed to import ACC data: [specific error details]"
}
```

#### 404 Not Found Examples

```json
// No extraction runs
{
  "message": "No extraction runs found"
}
```

### Error Logging

All errors are logged using Python's `logging` module:

```python
logging.exception(f"Error getting ACC connector folder for project {project_id}")
```

Check backend console output for detailed error traces.

---

## Database Connections

### Databases Used

1. **ProjectManagement** (default):
   - `tblACCDocs` - Desktop Connector file metadata
   - `tblProjects` - Project information
   - `tblAccImportLog` - ACC import logs
   - `tblReviztoExtractionRuns` - Revizto extraction runs

2. **acc_data_schema**:
   - `dbo.vw_issues_expanded_pm` - Issues view
   - `staging.*` - Staging tables for import
   - `dbo.issues`, `dbo.projects`, `dbo.users`, etc.

3. **RevitHealthCheckDB**:
   - `dbo.HealthChecks` - Health check results
   - `dbo.HealthCheckFiles` - Imported files

### Connection Configuration

Database connections are configured in `config.py`:

```python
PROJECT_MGMT_DB = os.getenv('PROJECT_MGMT_DB', 'ProjectManagement')
ACC_DB = os.getenv('ACC_DB', 'acc_data_schema')
REVIT_HEALTH_DB = os.getenv('REVIT_HEALTH_DB', 'RevitHealthCheckDB')
```

---

## Implementation Notes

### Backend Functions Used

**ACC Desktop Connector**:
- `database.get_acc_folder_path(project_id)`
- `database.save_acc_folder_path(project_id, folder_path)`
- `database.insert_files_into_tblACCDocs(project_id, folder_path)`

**ACC Data Import**:
- `handlers.acc_handler.import_acc_data(folder_path, db, merge_dir, show_skip_summary)`
- `database.log_acc_import(project_id, folder_name, summary)`
- `database.get_acc_import_logs(project_id)`

**Revizto**:
- `database.start_revizto_extraction_run(export_folder, notes)`
- `database.get_revizto_extraction_runs(limit)`
- `database.get_last_revizto_extraction_run()`

**Revit Health**:
- `handlers.rvt_health_importer.import_health_data(file_path, project_id)`
- `database.get_project_health_files(project_id)`

### File System Access

**Browser Limitations**: React frontend cannot access local file system directly.

**Solutions Implemented**:
1. ✅ **Manual Path Entry**: User types path in text input
2. ✅ **Backend Validation**: Server checks if path exists before operations
3. ⚠️ **Future**: Backend file browser service (not yet implemented)

---

## Next Steps

### Phase 2: React Components (Week 2)

Create React components that consume these endpoints:

1. **`ACCConnectorPanel.tsx`**:
   - Configure folder path
   - Trigger extraction
   - Display extracted files

2. **`ACCDataImportPanel.tsx`**:
   - Configure data folder
   - Trigger import
   - View import logs

3. **`ACCIssuesPanel.tsx`**:
   - Display issues list
   - Filter by status/priority
   - Show statistics dashboard

4. **`ReviztoImportPanel.tsx`**:
   - Start extraction
   - View run history
   - Display last run status

5. **`RevitHealthPanel.tsx`**:
   - Import health files
   - View file history
   - Display health summary

---

**Last Updated**: October 13, 2025  
**Status**: ✅ ALL 16 ENDPOINTS IMPLEMENTED AND DOCUMENTED  
**Ready For**: React component development
