# Data Imports - Quick Reference

**Purpose**: Quick reference for implementing data import features in React frontend

---

## 📋 Four Critical Features

### 1. ACC Desktop Connector File Extraction
- **What**: Extract BIM model files from ACC Desktop Connector folder on PC
- **Purpose**: Model file tracking (not issues)
- **Backend**: `database.insert_files_into_tblACCDocs()`
- **Database**: `ProjectManagement.dbo.tblACCDocs`
- **Status**: ⚠️ API endpoints needed

### 2. ACC Data Download Import
- **What**: Import ACC data export (CSV/ZIP with 20+ tables)
- **Purpose**: Issues, users, projects, custom attributes schema
- **Backend**: `handlers/acc_handler.py`
- **Database**: `acc_data_schema` (separate database)
- **Status**: ⚠️ API endpoints needed

### 3. ACC Issues Display
- **What**: View/manage imported ACC issues
- **Purpose**: Issue tracking and reporting
- **Backend**: Query `acc_data_schema.dbo.vw_issues_expanded_pm`
- **Database**: `acc_data_schema`
- **Status**: ⚠️ API endpoints needed

### 4. Revizto Issues
- **What**: Sync Revizto collaboration issues
- **Backend**: `services/revizto-dotnet/`
- **Database**: `RevitHealthCheckDB` or `ProjectManagement`
- **Status**: ⚠️ API endpoints needed

### 5. Revit Health Check
- **What**: Import BIM model quality data
- **Backend**: `handlers/rvt_health_importer.py`
- **Database**: `RevitHealthCheckDB.dbo.tblRvtProjHealth`
- **Status**: ⚠️ API endpoints needed

---

## 🔨 Implementation Steps

### Step 1: Backend APIs (Week 1)
```python
# Add to backend/app.py

# ACC Desktop Connector (File Extraction)
@app.route('/api/projects/<int:project_id>/acc-connector-folder', methods=['GET', 'POST'])
@app.route('/api/projects/<int:project_id>/acc-connector-extract', methods=['POST'])
@app.route('/api/projects/<int:project_id>/acc-connector-files', methods=['GET'])

# ACC Data Download Import (Issues Schema)
@app.route('/api/projects/<int:project_id>/acc-data-folder', methods=['GET', 'POST'])
@app.route('/api/projects/<int:project_id>/acc-data-import', methods=['POST'])
@app.route('/api/projects/<int:project_id>/acc-data-import-logs', methods=['GET'])

# ACC Issues Display
@app.route('/api/projects/<int:project_id>/acc-issues', methods=['GET'])
@app.route('/api/projects/<int:project_id>/acc-issues/stats', methods=['GET'])

# Revizto
@app.route('/api/revizto/start-extraction', methods=['POST'])
@app.route('/api/revizto/extraction-runs', methods=['GET'])

# Revit Health
@app.route('/api/projects/<int:project_id>/health-import', methods=['POST'])
@app.route('/api/projects/<int:project_id>/health-summary', methods=['GET'])
```

### Step 2: React Components (Week 2)
```typescript
// Create components
src/components/data-imports/
  - ACCConnectorPanel.tsx       # Desktop connector file extraction
  - ACCDataImportPanel.tsx       # CSV/ZIP data import
  - ACCIssuesPanel.tsx           # Issues display
  - ReviztoImportPanel.tsx       # Revizto import
  - RevitHealthPanel.tsx         # Revit health
  - ImportHistoryTable.tsx       # Shared history table
```

### Step 3: File Browser (Week 3)
```typescript
// Add folder path input component
<TextField
  label="Folder Path"
  value={path}
  onChange={(e) => setPath(e.target.value)}
  placeholder="C:\Path\To\Folder"
/>
```

### Step 4: Testing (Week 4)
- Unit tests for APIs
- Integration tests for imports
- Manual testing with real data

---

## 🚨 Critical Browser Limitations

**Problem**: Browsers can't access local file system directly

**Solutions**:
1. ✅ **Manual Path Entry** - User types path (easiest)
2. ✅ **Backend File Browser** - Server lists folders (secure)
3. ⚠️ **Electron App** - Native desktop app (future)

---

## 📊 Existing Database Functions

### ACC Desktop Connector Functions (database.py)
**Current Location**: Project Setup Tab (NOT Data Imports)  
**Tkinter Code**: `phase1_enhanced_ui.py` lines 1346-1650

```python
# Folder path management
get_project_folders(project_id)                          # Line 1429 - Get all project folder paths
update_project_folders(project_id, folder_path, ifc_...)  # Line 1443 - Update folder paths
save_acc_folder_path(project_id, folder_path)            # Line 683 - Save ACC connector path
get_acc_folder_path(project_id)                          # Line 703 - Get ACC connector path

# File extraction
insert_files_into_tblACCDocs(project_id, folder_path, include_dirs)  # Line 542 - Extract files to tblACCDocs

# Tkinter UI Functions
configure_paths()                                # Line 1301 - Configure Desktop Connector folder
extract_acc_files()                              # Line 1346 - Trigger extraction with validation
_perform_desktop_connector_extraction()          # Line 1391 - Main extraction with progress dialog
```

### ACC Data Import Functions (database.py)
```python
save_acc_folder_path(project_id, folder_path)  # Line 683
get_acc_folder_path(project_id)                # Line 703
log_acc_import(project_id, folder_name, summary)  # Line 717
get_acc_import_logs(project_id)                # Needs verification
```

### Revizto Functions (database.py)
```python
start_revizto_extraction_run(export_folder, notes)  # Line 2188
get_revizto_extraction_runs(limit=50)               # Line 2243
get_last_revizto_extraction_run()                   # Line 2284
```

### Health Check Functions (database.py)
```python
get_project_health_files(project_id)  # Line 735
set_control_file(project_id, file_name)  # Line 773
get_control_file(project_id)  # Line 759
```

### Import Handlers
```python
# handlers/acc_handler.py
import_acc_data(folder_path, db, merge_dir)  # Line 262
# Imports CSV/ZIP to acc_data_schema database (issues, users, projects)

# database.py  
insert_files_into_tblACCDocs(project_id, folder_path, include_dirs)  # Line 542
# Extracts file metadata from Desktop Connector folder to ProjectManagement.dbo.tblACCDocs

# handlers/rvt_health_importer.py
import_health_data(json_folder, db_name)  # Line 27
```

---

## 🔗 Key Integration Points

### ACC Desktop Connector File Extraction Flow
1. User selects ACC Desktop Connector folder path
2. Frontend calls `/api/projects/{id}/acc-connector-extract`
3. Backend calls `insert_files_into_tblACCDocs()`
4. Files in folder scanned (optionally filtered by include_dirs)
5. File metadata extracted (name, path, size, modified date)
6. Data inserted to `ProjectManagement.dbo.tblACCDocs`
7. Frontend displays file list and statistics

### ACC Data Download Import Flow
1. User selects folder/ZIP with ACC data export
2. Frontend calls `/api/projects/{id}/acc-data-import`
3. Backend calls `import_acc_data()`
4. Data flows to `acc_data_schema.staging.*` tables (20+ CSVs)
5. Merge scripts move to `acc_data_schema.dbo.*`
6. Frontend displays import logs

### ACC Issues Display Flow
1. User navigates to Issues view
2. Frontend calls `/api/projects/{id}/acc-issues`
3. Backend queries `acc_data_schema.dbo.vw_issues_expanded_pm`
4. Issues filtered by project
5. Frontend displays in table/cards with stats

### Revizto Flow
1. User clicks "Start Extraction"
2. Frontend calls `/api/revizto/start-extraction`
3. Backend launches `ReviztoDataExporter.exe`
4. Exporter fetches data from Revizto API
5. Data saved to database
6. Frontend polls for completion

### Health Check Flow
1. User selects JSON folder
2. Frontend calls `/api/projects/{id}/health-import`
3. Backend calls `import_health_data()`
4. JSON files parsed and inserted to `tblRvtProjHealth`
5. Files moved to `processed/` subfolder
6. Frontend displays summary

---

## 📁 File Structure

```
BIMProjMngmt/
├── backend/
│   └── app.py                    # Add new API endpoints here
├── frontend/src/
│   ├── components/data-imports/  # New components here
│   └── pages/
│       └── DataImportsPage.tsx   # New page here
├── handlers/
│   ├── acc_handler.py           # ACC import logic
│   └── rvt_health_importer.py   # Health check logic
├── services/
│   └── revizto-dotnet/          # Revizto exporter tool
└── database.py                   # Database functions
```

---

## ⚡ Quick Start Commands

### Backend Development
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run Flask backend
python backend/app.py
```

### Frontend Development
```powershell
# Navigate to frontend
cd frontend

# Install dependencies (first time)
npm install

# Run dev server
npm run dev
```

### Testing Imports
```powershell
# Test ACC import
python -c "from handlers.acc_handler import import_acc_data; import_acc_data('C:/path/to/folder')"

# Test Health import
python -c "from handlers.rvt_health_importer import import_health_data; import_health_data('C:/path/to/json')"
```

---

## 🐛 Common Issues

### Issue: "Cannot access file system from browser"
**Solution**: Use manual path entry or backend file browser service

### Issue: "Import takes too long, browser times out"
**Solution**: Implement background task processing (Celery) or polling

### Issue: "Large ZIP files fail to upload"
**Solution**: Increase Flask `MAX_CONTENT_LENGTH` to 500MB+

### Issue: "Database connection fails during import"
**Solution**: Use connection pooling in `database_pool.py`

---

## 📚 Documentation References

- **Full Roadmap**: `docs/REACT_DATA_IMPORTS_IMPLEMENTATION_ROADMAP.md`
- **Tkinter Reference**: `ui/tab_data_imports.py`
- **ACC Handler**: `handlers/acc_handler.py`
- **Health Importer**: `handlers/rvt_health_importer.py`
- **Database Schema**: `constants/schema.py`
- **API Patterns**: `backend/app.py`

---

## ✅ Success Checklist

Before marking complete:
- [ ] All 4 import types work in React
- [ ] Data persists to correct databases
- [ ] Import logs display correctly
- [ ] Error handling is robust
- [ ] Tests pass
- [ ] Documentation updated

---

**Last Updated**: October 13, 2025  
**Status**: Ready to implement
