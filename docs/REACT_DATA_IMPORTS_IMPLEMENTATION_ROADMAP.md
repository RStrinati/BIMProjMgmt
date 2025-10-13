# React Data Imports Implementation Roadmap

**Date**: October 13, 2025  
**Status**: 📋 **PLANNING - CRITICAL FUNCTIONALITY MIGRATION**

---

## Executive Summary

This document outlines the complete implementation plan for migrating **four critical data import functionalities** from the Tkinter desktop application to the React frontend. These features are essential for daily project management workflows and must be implemented with full feature parity.

### Critical Features to Implement:

1. ✅ **ACC Desktop Connector Folder Path & Extract** - Extract and import BIM model files from ACC Desktop Connector folder for model tracking
2. ✅ **ACC Issues Import** - Import ACC data download (CSV/ZIP) containing issues, projects, users, and custom attributes schema
3. ✅ **Revizto Issues Import** - Collaboration platform issue synchronization  
4. ✅ **Revit Health Check Import** - BIM model quality assessment data

---

## Current State Analysis

### Existing Tkinter Implementation
**Location**: `ui/tab_data_imports.py`

**Current Capabilities**:
- Browse and select folder paths
- Import ACC CSV/ZIP files
- Import Revit health check JSON files
- Launch Revizto .NET exporter tool
- Display import history and logs
- Store folder paths per project
- Validate file formats before import

### Existing Backend Infrastructure
**Location**: `backend/app.py`, `handlers/`, `database.py`

**Available Components**:
- ✅ ACC import handler (`handlers/acc_handler.py`)
- ✅ Revit health importer (`handlers/rvt_health_importer.py`)
- ✅ Database functions for path storage and logging
- ✅ ACC/Revizto service configuration (`config.py`)
- ⚠️ **Missing**: Flask API endpoints for these operations

---

## Implementation Strategy

### Phase 1: Backend API Development
**Timeline**: Week 1  
**Priority**: CRITICAL

#### 1.1 ACC Desktop Connector File Extraction API Endpoints

**Current Tkinter Implementation**:
- **Location**: `ui/tab_project.py` - **Project Setup Tab** (NOT Data Imports tab)
- **UI Function**: "Extract Files from Desktop Connector" button in Project Setup
- **Folder Configuration**: Desktop Connector folder path is configured per project in Project Setup tab
- **Code Location**: `phase1_enhanced_ui.py` lines 1346-1650
  - `configure_paths()` (line 1301) - Configure Desktop Connector folder
  - `extract_acc_files()` (line 1346) - Trigger extraction
  - `_perform_desktop_connector_extraction()` (line 1391) - Main extraction logic with progress dialog
- **Database Functions**: 
  - `database.insert_files_into_tblACCDocs()` (line 542) - Insert file records
  - `database.save_acc_folder_path()` (line 683) - Save folder path
  - `database.get_acc_folder_path()` (line 703) - Retrieve folder path
  - `database.get_project_folders()` (line 1429) - Get all project folder paths
  - `database.update_project_folders()` (line 1443) - Update folder paths

**Purpose**: Extract BIM model files from the ACC Desktop Connector folder on the local PC and import them to the database for model tracking (not issue tracking).

**What This Does**:
- Scans the ACC Desktop Connector folder (typically synced to local PC)
- Extracts file metadata (name, path, size, modified date, type)
- **Overrides** existing records in `tblACCDocs` for the project (DELETE then INSERT)
- Inserts into `tblACCDocs` table in `ProjectManagement` database
- Used for tracking which files/models are in the project
- Enables file-based reporting and analytics
- Shows progress dialog with file count and processing status

**New Flask Routes Required**:

```python
# backend/app.py

# Get ACC Desktop Connector folder path for project
@app.route('/api/projects/<int:project_id>/acc-connector-folder', methods=['GET'])
def get_project_acc_connector_folder(project_id):
    """Get saved ACC Desktop Connector folder path for model tracking"""
    folder_path = get_project_folders(project_id)  # Returns folder configuration
    return jsonify({
        'project_id': project_id,
        'folder_path': folder_path.get('folder_path') if folder_path else None,
        'ifc_folder_path': folder_path.get('ifc_folder_path') if folder_path else None
    })

# Save ACC Desktop Connector folder path
@app.route('/api/projects/<int:project_id>/acc-connector-folder', methods=['POST'])
def save_project_acc_connector_folder(project_id):
    """Save ACC Desktop Connector folder path for project"""
    folder_path = request.json.get('folder_path')
    success = update_project_folders(project_id, folder_path=folder_path)
    return jsonify({
        'success': success,
        'project_id': project_id,
        'folder_path': folder_path
    })

# Extract and import files from ACC Desktop Connector folder
@app.route('/api/projects/<int:project_id>/acc-connector-extract', methods=['POST'])
def extract_acc_connector_files(project_id):
    """Extract file metadata from ACC Desktop Connector folder and import to tblACCDocs"""
    folder_path = request.json.get('folder_path')
    include_dirs = request.json.get('include_dirs', None)  # Optional filter: ["WIP", "Shared", "Published"]
    
    # Validation
    if not folder_path:
        return jsonify({'error': 'Folder path required'}), 400
    
    if not os.path.exists(folder_path):
        return jsonify({'error': 'Path does not exist'}), 404
    
    try:
        # Extract files from ACC Desktop Connector folder
        success = insert_files_into_tblACCDocs(project_id, folder_path, include_dirs)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'ACC Desktop Connector files extracted and imported to tblACCDocs'
            })
        else:
            return jsonify({'error': 'File extraction failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get extracted ACC files
@app.route('/api/projects/<int:project_id>/acc-connector-files', methods=['GET'])
def get_acc_connector_files(project_id):
    """Get files extracted from ACC Desktop Connector"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    file_name,
                    file_path,
                    date_modified,
                    file_type,
                    file_size_kb,
                    created_at
                FROM tblACCDocs
                WHERE project_id = ?
                ORDER BY date_modified DESC
            """, (project_id,))
            
            files = []
            for row in cursor.fetchall():
                files.append({
                    'file_name': row[0],
                    'file_path': row[1],
                    'date_modified': row[2].isoformat() if row[2] else None,
                    'file_type': row[3],
                    'file_size_kb': row[4],
                    'created_at': row[5].isoformat() if row[5] else None
                })
            
            return jsonify({
                'project_id': project_id,
                'files': files,
                'count': len(files)
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Database Functions Required** (Already Exist):
- ✅ `get_project_folders(project_id)` - `database.py:1429`
- ✅ `update_project_folders(project_id, folder_path, ifc_folder_path)` - `database.py:1443`
- ✅ `insert_files_into_tblACCDocs(project_id, folder_path, include_dirs)` - `database.py:542`

**Database Tables**:
- `ProjectManagement.dbo.tblACCDocs` - Stores file metadata
- `ProjectManagement.dbo.Projects` - Stores folder_path configuration

---

#### 1.2 ACC Data Download (Issues) Import API Endpoints

**Purpose**: Import the ACC data export download (CSV/ZIP files) containing the complete ACC schema - issues, projects, users, custom attributes, etc.

**What This Does**:
- Imports ACC data export ZIP files (downloaded from ACC portal)
- Contains 20+ CSV files with complete ACC project data
- Imports to `acc_data_schema` database (separate from ProjectManagement)
- Includes issues, users, projects, custom attributes, root causes, etc.
- Used for issue tracking, reporting, and analytics

**Database Integration**:
- Target Database: `acc_data_schema` (separate database)
- Staging tables: `acc_data_schema.staging.issues_*`, `staging.projects`, `staging.users`
- Production views: `acc_data_schema.dbo.vw_issues_expanded_pm`
- Merge process: CSV → staging tables → merge SQL scripts → production tables

**New Flask Routes Required**:

```python
# backend/app.py

# Get ACC data export folder path for project
@app.route('/api/projects/<int:project_id>/acc-data-folder', methods=['GET'])
def get_project_acc_data_folder(project_id):
    """Get saved ACC data export folder path (for CSV/ZIP imports)"""
    folder_path = get_acc_folder_path(project_id)
    return jsonify({
        'project_id': project_id,
        'acc_folder_path': folder_path
    })

# Save ACC data export folder path
@app.route('/api/projects/<int:project_id>/acc-data-folder', methods=['POST'])
def save_project_acc_data_folder(project_id):
    """Save ACC data export folder path for project"""
    folder_path = request.json.get('folder_path')
    success = save_acc_folder_path(project_id, folder_path)
    return jsonify({
        'success': success,
        'project_id': project_id,
        'acc_folder_path': folder_path
    })

# Import ACC CSV/ZIP data
@app.route('/api/projects/<int:project_id>/acc-data-import', methods=['POST'])
def import_acc_data_endpoint(project_id):
    """Import ACC CSV/ZIP data export to acc_data_schema database"""
    folder_path = request.json.get('folder_path')
    
    # Validation
    if not folder_path:
        return jsonify({'error': 'Folder path required'}), 400
    
    if not os.path.exists(folder_path):
        return jsonify({'error': 'Path does not exist'}), 404
    
    # Run import in background task (consider using Celery for production)
    try:
        from handlers.acc_handler import import_acc_data
        summary = import_acc_data(folder_path)  # Imports to acc_data_schema
        
        # Log import
        log_acc_import(project_id, os.path.basename(folder_path), 
                      f"Imported {len(summary)} tables to acc_data_schema")
        
        return jsonify({
            'success': True,
            'summary': summary,
            'message': f'Imported {len(summary)} ACC tables successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get ACC import logs
@app.route('/api/projects/<int:project_id>/acc-data-import-logs', methods=['GET'])
def get_project_acc_data_import_logs(project_id):
    """Get ACC data import history for project"""
    logs = get_acc_import_logs(project_id)
    return jsonify({
        'project_id': project_id,
        'logs': [{
            'folder_name': log[0],
            'import_date': log[1].isoformat() if log[1] else None,
            'summary': log[2]
        } for log in logs]
    })
```

**Database Functions Required** (Already Exist):
- ✅ `save_acc_folder_path(project_id, folder_path)` - `database.py:683`
- ✅ `get_acc_folder_path(project_id)` - `database.py:703`
- ✅ `log_acc_import(project_id, folder_name, summary)` - `database.py:717`
- ✅ `get_acc_import_logs(project_id)` - Needs verification

**Handler Functions Required** (Already Exist):
- ✅ `import_acc_data(folder_path, db, merge_dir)` - `handlers/acc_handler.py:262`

**Database Tables** (`acc_data_schema`):
- Staging: `staging.issues_issues`, `staging.projects`, `staging.users`, + 20 more
- Production: `dbo.vw_issues_expanded_pm` (view), `dbo.issues`, `dbo.projects`

---

#### 1.3 ACC Issues Display API Endpoints

**Purpose**: Query and display ACC issues that were imported via the ACC data download import (section 1.2).

**Key Insight**: These issues come from the `acc_data_schema` database after running the ACC data import.

**Database Integration**:
- ACC Issues stored in: `acc_data_schema.dbo.vw_issues_expanded_pm` (view)
- Staging table: `acc_data_schema.staging.issues_issues`
- Custom attributes: `acc_data_schema.staging.issues_custom_attributes_mappings`

**API Endpoints Required**:

```python
# Get ACC issues for project
@app.route('/api/projects/<int:project_id>/acc-issues', methods=['GET'])
def get_project_acc_issues(project_id):
    """Get ACC issues from the imported data in acc_data_schema"""
    try:
        with get_db_connection('acc_data_schema') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    issue_id,
                    title,
                    status,
                    priority,
                    assigned_to,
                    due_date,
                    created_date,
                    issue_type
                FROM dbo.vw_issues_expanded_pm
                WHERE project_id = ?
                ORDER BY created_date DESC
            """, (project_id,))
            
            issues = []
            for row in cursor.fetchall():
                issues.append({
                    'issue_id': row[0],
                    'title': row[1],
                    'status': row[2],
                    'priority': row[3],
                    'assigned_to': row[4],
                    'due_date': row[5].isoformat() if row[5] else None,
                    'created_date': row[6].isoformat() if row[6] else None,
                    'issue_type': row[7]
                })
            
            return jsonify({
                'project_id': project_id,
                'issues': issues,
                'count': len(issues)
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get ACC issue statistics
@app.route('/api/projects/<int:project_id>/acc-issues/stats', methods=['GET'])
def get_project_acc_issue_stats(project_id):
    """Get ACC issue statistics for dashboard"""
    try:
        with get_db_connection('acc_data_schema') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM dbo.vw_issues_expanded_pm
                WHERE project_id = ?
                GROUP BY status
            """, (project_id,))
            
            stats = {
                'by_status': {row[0]: row[1] for row in cursor.fetchall()}
            }
            
            return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

#### 1.3 Revizto Issues Import API Endpoints

**Current Implementation Analysis**:
- Revizto data extracted via: `services/revizto-dotnet/ReviztoDataExporter/`
- Database: `RevitHealthCheckDB` or `ProjectManagement`
- Tables: `tblReviztoProjects`, `tblReviztoIssues` (verify schema)

**Existing Database Functions**:
- ✅ `start_revizto_extraction_run()` - `database.py:2188`
- ✅ `complete_revizto_extraction_run()` - `database.py:2217`
- ✅ `get_revizto_extraction_runs()` - `database.py:2243`
- ✅ `get_revizto_projects_since_last_run()` - `database.py:2318`

**API Endpoints Required**:

```python
# Start Revizto extraction
@app.route('/api/revizto/start-extraction', methods=['POST'])
def start_revizto_extraction():
    """Launch Revizto data extraction process"""
    export_folder = request.json.get('export_folder')
    notes = request.json.get('notes')
    
    run_id = start_revizto_extraction_run(export_folder, notes)
    
    if run_id:
        # Launch the Revizto exporter tool
        exporter_path = r"services\revizto-dotnet\ReviztoDataExporter\bin\Debug\net9.0-windows\win-x64\ReviztoDataExporter.exe"
        
        # Use subprocess to launch in background
        import subprocess
        subprocess.Popen([exporter_path], shell=True)
        
        return jsonify({
            'success': True,
            'run_id': run_id,
            'message': 'Revizto extraction started'
        })
    else:
        return jsonify({'error': 'Failed to start extraction'}), 500

# Get Revizto extraction history
@app.route('/api/revizto/extraction-runs', methods=['GET'])
def get_revizto_extraction_history():
    """Get recent Revizto extraction runs"""
    limit = request.args.get('limit', 50, type=int)
    runs = get_revizto_extraction_runs(limit)
    return jsonify({
        'runs': runs,
        'count': len(runs)
    })

# Get Revizto issues for project
@app.route('/api/projects/<int:project_id>/revizto-issues', methods=['GET'])
def get_project_revizto_issues(project_id):
    """Get Revizto issues for a specific project"""
    try:
        # Implementation depends on database schema
        # This is a placeholder - adjust based on actual schema
        issues = get_project_combined_issues_overview(project_id)
        return jsonify({
            'project_id': project_id,
            'issues': issues
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sync Revizto issues
@app.route('/api/revizto/sync-issues', methods=['POST'])
def sync_revizto_issues():
    """Trigger Revizto issue synchronization"""
    # This would call the Revizto service
    # Implementation depends on service architecture
    return jsonify({
        'success': True,
        'message': 'Revizto sync initiated'
    })
```

---

#### 1.4 Revit Health Check Import API Endpoints

**Current Implementation Analysis**:
- Handler: `handlers/rvt_health_importer.py`
- Database: `RevitHealthCheckDB`
- Main table: `tblRvtProjHealth`
- Process: Imports JSON files from Revit audits

**Existing Database Functions**:
- ✅ `get_project_health_files(project_id)` - `database.py:735`
- ✅ `set_control_file(project_id, file_name)` - `database.py:773`
- ✅ `get_control_file(project_id)` - `database.py:759`

**Handler Functions**:
- ✅ `import_health_data(json_folder, db_name)` - `handlers/rvt_health_importer.py:27`

**API Endpoints Required**:

```python
# Get health check files for project
@app.route('/api/projects/<int:project_id>/health-files', methods=['GET'])
def get_project_health_files_endpoint(project_id):
    """Get available Revit health check files for project"""
    files = get_project_health_files(project_id)
    return jsonify({
        'project_id': project_id,
        'files': files,
        'count': len(files)
    })

# Get control file
@app.route('/api/projects/<int:project_id>/control-file', methods=['GET'])
def get_project_control_file(project_id):
    """Get the control model file for project"""
    control_file = get_control_file(project_id)
    return jsonify({
        'project_id': project_id,
        'control_file': control_file
    })

# Set control file
@app.route('/api/projects/<int:project_id>/control-file', methods=['POST'])
def set_project_control_file(project_id):
    """Set the control model file for project"""
    file_name = request.json.get('file_name')
    success = set_control_file(project_id, file_name)
    return jsonify({
        'success': success,
        'project_id': project_id,
        'control_file': file_name
    })

# Import health check data
@app.route('/api/projects/<int:project_id>/health-import', methods=['POST'])
def import_health_check_data(project_id):
    """Import Revit health check JSON files"""
    json_folder = request.json.get('json_folder')
    
    if not json_folder or not os.path.isdir(json_folder):
        return jsonify({'error': 'Valid JSON folder required'}), 400
    
    try:
        from handlers.rvt_health_importer import import_health_data
        import_health_data(json_folder)
        
        return jsonify({
            'success': True,
            'message': f'Health check data imported from {json_folder}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get health check summary
@app.route('/api/projects/<int:project_id>/health-summary', methods=['GET'])
def get_project_health_summary(project_id):
    """Get health check summary for project"""
    try:
        with get_db_connection('RevitHealthCheckDB') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    strRvtFileName,
                    nWarningsCount,
                    nCriticalWarningsCount,
                    nTotalViewCount,
                    nModelFileSizeMB,
                    ConvertedExportedDate
                FROM dbo.vw_LatestRvtFiles
                WHERE project_id = ?
                ORDER BY ConvertedExportedDate DESC
            """, (project_id,))
            
            files = []
            for row in cursor.fetchall():
                files.append({
                    'file_name': row[0],
                    'warnings': row[1],
                    'critical_warnings': row[2],
                    'views': row[3],
                    'file_size_mb': row[4],
                    'export_date': row[5].isoformat() if row[5] else None
                })
            
            return jsonify({
                'project_id': project_id,
                'files': files,
                'count': len(files)
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

### Phase 2: Frontend Component Development
**Timeline**: Week 2  
**Priority**: HIGH

#### 2.1 React Component Architecture

**New Components to Create**:

1. **DataImportsPage.tsx** - Main page container
2. **ACCImportPanel.tsx** - ACC data import section
3. **ACCIssuesPanel.tsx** - ACC issues display
4. **ReviztoImportPanel.tsx** - Revizto import section
5. **RevitHealthPanel.tsx** - Revit health check section
6. **ImportHistoryTable.tsx** - Reusable import log display
7. **FolderPathInput.tsx** - Reusable folder selection component

**Component Structure**:

```
src/
  pages/
    DataImportsPage.tsx          # Main page with tabs
  components/
    data-imports/
      ACCImportPanel.tsx          # ACC data import
      ACCIssuesPanel.tsx          # ACC issues
      ReviztoImportPanel.tsx      # Revizto import
      RevitHealthPanel.tsx        # Revit health
      ImportHistoryTable.tsx      # Shared history table
      FolderPathInput.tsx         # Shared folder input
```

---

#### 2.2 ACC Import Panel Component

**File**: `frontend/src/components/data-imports/ACCImportPanel.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Paper,
  Stack
} from '@mui/material';
import { FolderOpen, Upload } from '@mui/icons-material';
import axios from 'axios';
import ImportHistoryTable from './ImportHistoryTable';

interface ACCImportPanelProps {
  projectId: number;
}

export default function ACCImportPanel({ projectId }: ACCImportPanelProps) {
  const [folderPath, setFolderPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [importLogs, setImportLogs] = useState([]);

  // Load saved folder path and import logs
  useEffect(() => {
    if (projectId) {
      loadFolderPath();
      loadImportLogs();
    }
  }, [projectId]);

  const loadFolderPath = async () => {
    try {
      const response = await axios.get(`/api/projects/${projectId}/acc-folder`);
      if (response.data.acc_folder_path) {
        setFolderPath(response.data.acc_folder_path);
      }
    } catch (err) {
      console.error('Failed to load ACC folder path:', err);
    }
  };

  const loadImportLogs = async () => {
    try {
      const response = await axios.get(`/api/projects/${projectId}/acc-import-logs`);
      setImportLogs(response.data.logs);
    } catch (err) {
      console.error('Failed to load import logs:', err);
    }
  };

  const handleSavePath = async () => {
    setLoading(true);
    setError(null);
    try {
      await axios.post(`/api/projects/${projectId}/acc-folder`, {
        folder_path: folderPath
      });
      setSuccess('ACC folder path saved successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to save folder path');
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await axios.post(`/api/projects/${projectId}/acc-import`, {
        folder_path: folderPath
      });
      
      setSuccess(response.data.message);
      loadImportLogs(); // Refresh logs
      
      setTimeout(() => setSuccess(null), 5000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Import failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        ACC Data Export Folder
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <Stack spacing={2}>
        <TextField
          label="ACC Export Folder Path"
          value={folderPath}
          onChange={(e) => setFolderPath(e.target.value)}
          fullWidth
          placeholder="C:\Path\To\ACC\Export"
          helperText="Enter the folder path containing ACC CSV exports or ZIP files"
          InputProps={{
            endAdornment: (
              <Button
                startIcon={<FolderOpen />}
                onClick={() => {
                  // Note: Browser file dialogs have limitations
                  // Consider implementing a custom backend endpoint for folder browsing
                  alert('File browser dialog requires native OS integration. Please type the path manually.');
                }}
              >
                Browse
              </Button>
            )
          }}
        />

        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            onClick={handleSavePath}
            disabled={loading || !folderPath}
          >
            Save Path
          </Button>
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={20} /> : <Upload />}
            onClick={handleImport}
            disabled={loading || !folderPath}
          >
            Import ACC Data
          </Button>
        </Stack>

        <Typography variant="subtitle1" sx={{ mt: 3 }}>
          Import History
        </Typography>
        <ImportHistoryTable logs={importLogs} />
      </Stack>
    </Paper>
  );
}
```

---

#### 2.3 Revit Health Panel Component

**File**: `frontend/src/components/data-imports/RevitHealthPanel.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { Upload, FolderOpen } from '@mui/icons-material';
import axios from 'axios';

interface RevitHealthPanelProps {
  projectId: number;
}

export default function RevitHealthPanel({ projectId }: RevitHealthPanelProps) {
  const [jsonFolder, setJsonFolder] = useState('');
  const [healthFiles, setHealthFiles] = useState<string[]>([]);
  const [controlFile, setControlFile] = useState('');
  const [loading, setLoading] = useState(false);
  const [healthSummary, setHealthSummary] = useState([]);

  useEffect(() => {
    if (projectId) {
      loadHealthFiles();
      loadControlFile();
      loadHealthSummary();
    }
  }, [projectId]);

  const loadHealthFiles = async () => {
    try {
      const response = await axios.get(`/api/projects/${projectId}/health-files`);
      setHealthFiles(response.data.files);
    } catch (err) {
      console.error('Failed to load health files:', err);
    }
  };

  const loadControlFile = async () => {
    try {
      const response = await axios.get(`/api/projects/${projectId}/control-file`);
      setControlFile(response.data.control_file || '');
    } catch (err) {
      console.error('Failed to load control file:', err);
    }
  };

  const loadHealthSummary = async () => {
    try {
      const response = await axios.get(`/api/projects/${projectId}/health-summary`);
      setHealthSummary(response.data.files);
    } catch (err) {
      console.error('Failed to load health summary:', err);
    }
  };

  const handleSaveControlFile = async () => {
    try {
      await axios.post(`/api/projects/${projectId}/control-file`, {
        file_name: controlFile
      });
      alert('Control file saved successfully');
    } catch (err) {
      alert('Failed to save control file');
    }
  };

  const handleImport = async () => {
    setLoading(true);
    try {
      await axios.post(`/api/projects/${projectId}/health-import`, {
        json_folder: jsonFolder
      });
      alert('Health check data imported successfully');
      loadHealthSummary();
    } catch (err: any) {
      alert(err.response?.data?.error || 'Import failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Revit Health Check Import
      </Typography>

      <Stack spacing={3}>
        {/* Control File Selection */}
        <FormControl fullWidth>
          <InputLabel>Control Model File</InputLabel>
          <Select
            value={controlFile}
            onChange={(e) => setControlFile(e.target.value)}
            label="Control Model File"
          >
            <MenuItem value="">
              <em>None</em>
            </MenuItem>
            {healthFiles.map((file) => (
              <MenuItem key={file} value={file}>
                {file}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Button variant="outlined" onClick={handleSaveControlFile}>
          Save Control Model
        </Button>

        {/* JSON Folder Import */}
        <TextField
          label="Audit JSON Folder"
          value={jsonFolder}
          onChange={(e) => setJsonFolder(e.target.value)}
          fullWidth
          placeholder="C:\Path\To\JSON\Folder"
          helperText="Folder containing Revit audit JSON exports"
        />

        <Button
          variant="contained"
          startIcon={<Upload />}
          onClick={handleImport}
          disabled={loading || !jsonFolder}
        >
          Import Audit JSONs
        </Button>

        {/* Health Summary Table */}
        <Typography variant="subtitle1" sx={{ mt: 3 }}>
          Health Check Summary
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>File Name</TableCell>
                <TableCell align="right">Warnings</TableCell>
                <TableCell align="right">Critical</TableCell>
                <TableCell align="right">Views</TableCell>
                <TableCell align="right">Size (MB)</TableCell>
                <TableCell>Export Date</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {healthSummary.map((file: any, index) => (
                <TableRow key={index}>
                  <TableCell>{file.file_name}</TableCell>
                  <TableCell align="right">{file.warnings}</TableCell>
                  <TableCell align="right">{file.critical_warnings}</TableCell>
                  <TableCell align="right">{file.views}</TableCell>
                  <TableCell align="right">{file.file_size_mb}</TableCell>
                  <TableCell>{file.export_date}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Stack>
    </Paper>
  );
}
```

---

### Phase 3: File System Integration Challenges
**Timeline**: Week 3  
**Priority**: CRITICAL

#### 3.1 Browser Limitations

**Problem**: Browsers cannot directly access the local file system for security reasons.

**Solutions**:

1. **Manual Path Entry** (Simplest)
   - User types/pastes folder paths
   - Works for power users familiar with their file system
   - ✅ Implemented in examples above

2. **Drag & Drop** (Best UX)
   ```typescript
   const handleDrop = (e: React.DragEvent) => {
     e.preventDefault();
     const files = Array.from(e.dataTransfer.files);
     // Can only access files, not folders directly
     // May need to use webkitGetAsEntry() for folder access
   };
   ```

3. **File Input with Directory Attribute** (Limited)
   ```typescript
   <input
     type="file"
     webkitdirectory=""
     directory=""
     onChange={handleFolderSelect}
   />
   ```

4. **Backend File Browser Service** (Recommended)
   ```python
   # New endpoint to browse server-accessible paths
   @app.route('/api/file-browser/list', methods=['POST'])
   def list_directory():
       path = request.json.get('path')
       # Security: Only allow whitelisted root paths
       # Return list of folders/files
   ```

5. **Native Desktop Integration** (Advanced)
   - Electron wrapper for the React app
   - Native file dialogs via Electron IPC
   - Full file system access

---

#### 3.2 Recommended Approach

**Hybrid Solution**:

1. **Phase 3A**: Manual path entry (Week 3)
   - ✅ Simple to implement
   - Works immediately
   - No security concerns

2. **Phase 3B**: Backend file browser (Week 4)
   - Protected file system access
   - Better UX than manual entry
   - Secure with path whitelisting

3. **Phase 3C**: Consider Electron (Future)
   - Full native desktop experience
   - Complete file system access
   - Cross-platform support

---

### Phase 4: Testing & Validation
**Timeline**: Week 4  
**Priority**: HIGH

#### 4.1 Integration Testing

**Test Cases Required**:

```typescript
// tests/data-imports.test.ts

describe('ACC Import Flow', () => {
  it('should save ACC folder path', async () => {
    // Test saving path
  });

  it('should load saved ACC folder path', async () => {
    // Test loading path
  });

  it('should import ACC CSV data', async () => {
    // Test import process
  });

  it('should display import logs', async () => {
    // Test log retrieval
  });
});

describe('Revit Health Import Flow', () => {
  it('should load health files for project', async () => {
    // Test file list
  });

  it('should save control file selection', async () => {
    // Test control file save
  });

  it('should import health JSON data', async () => {
    // Test import
  });

  it('should display health summary', async () => {
    // Test summary display
  });
});
```

#### 4.2 Manual Testing Checklist

- [ ] ACC folder path saves correctly
- [ ] ACC folder path loads on page refresh
- [ ] ACC CSV import processes successfully
- [ ] ACC ZIP import processes successfully
- [ ] Import logs display correctly
- [ ] ACC issues display after import
- [ ] Revit health files load for project
- [ ] Control file selection persists
- [ ] Health JSON import works
- [ ] Health summary displays correctly
- [ ] Revizto extraction starts successfully
- [ ] Revizto extraction history displays

---

## Implementation Checklist

### Backend (Flask API)

- [ ] **ACC Endpoints**
  - [ ] GET `/api/projects/<id>/acc-folder`
  - [ ] POST `/api/projects/<id>/acc-folder`
  - [ ] POST `/api/projects/<id>/acc-import`
  - [ ] GET `/api/projects/<id>/acc-import-logs`
  - [ ] GET `/api/projects/<id>/acc-issues`
  - [ ] GET `/api/projects/<id>/acc-issues/stats`

- [ ] **Revizto Endpoints**
  - [ ] POST `/api/revizto/start-extraction`
  - [ ] GET `/api/revizto/extraction-runs`
  - [ ] GET `/api/projects/<id>/revizto-issues`
  - [ ] POST `/api/revizto/sync-issues`

- [ ] **Revit Health Endpoints**
  - [ ] GET `/api/projects/<id>/health-files`
  - [ ] GET `/api/projects/<id>/control-file`
  - [ ] POST `/api/projects/<id>/control-file`
  - [ ] POST `/api/projects/<id>/health-import`
  - [ ] GET `/api/projects/<id>/health-summary`

- [ ] **File Browser (Optional)**
  - [ ] POST `/api/file-browser/list`
  - [ ] GET `/api/file-browser/validate-path`

### Frontend (React Components)

- [ ] **Pages**
  - [ ] `DataImportsPage.tsx` - Main container with tabs

- [ ] **Components**
  - [ ] `ACCImportPanel.tsx`
  - [ ] `ACCIssuesPanel.tsx`
  - [ ] `ReviztoImportPanel.tsx`
  - [ ] `RevitHealthPanel.tsx`
  - [ ] `ImportHistoryTable.tsx` (shared)
  - [ ] `FolderPathInput.tsx` (shared)

- [ ] **Navigation**
  - [ ] Add "Data Imports" to main navigation menu
  - [ ] Add route in React Router

### Testing

- [ ] Unit tests for new API endpoints
- [ ] Integration tests for import flows
- [ ] E2E tests for complete workflows
- [ ] Manual testing with real data
- [ ] Performance testing with large files

### Documentation

- [ ] API endpoint documentation
- [ ] Component usage documentation
- [ ] User guide for data imports
- [ ] Troubleshooting guide

---

## Technical Considerations

### 1. File Upload Size Limits

ACC ZIP files can be large (100MB+). Configure:

```python
# backend/app.py
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
```

### 2. Long-Running Imports

ACC/Revit imports can take minutes. Consider:

- **Background Tasks**: Use Celery or similar
- **WebSocket Progress**: Real-time import progress
- **Polling**: Frontend polls for status updates

```python
# Example: Background task with status endpoint
@app.route('/api/import-status/<task_id>', methods=['GET'])
def get_import_status(task_id):
    # Return current status
    pass
```

### 3. Error Handling

Robust error handling for:
- Invalid file paths
- Missing files
- Database connection failures
- Import validation failures
- Partial imports

### 4. Security

- **Path Validation**: Prevent directory traversal attacks
- **File Type Validation**: Only allow expected file types
- **Access Control**: Ensure users can only access their projects
- **Rate Limiting**: Prevent import spam

---

## Migration Timeline

### Week 1: Backend API (5 days)
- Day 1-2: ACC endpoints
- Day 3: Revizto endpoints
- Day 4-5: Revit Health endpoints

### Week 2: Frontend Components (5 days)
- Day 1-2: ACCImportPanel
- Day 3: RevitHealthPanel
- Day 4: ReviztoImportPanel
- Day 5: Integration & styling

### Week 3: File System Integration (5 days)
- Day 1-2: Manual path entry refinement
- Day 3-4: Backend file browser service
- Day 5: Testing & bug fixes

### Week 4: Testing & Deployment (5 days)
- Day 1-2: Integration testing
- Day 3: Performance testing
- Day 4: User acceptance testing
- Day 5: Documentation & deployment

---

## Success Criteria

✅ **Functionality**:
- All four import types work in React frontend
- Feature parity with Tkinter implementation
- Data persists correctly in database

✅ **User Experience**:
- Intuitive folder selection
- Clear error messages
- Progress indicators for long operations
- Import history visible

✅ **Performance**:
- Large file imports complete successfully
- No browser crashes or freezes
- Responsive UI during imports

✅ **Reliability**:
- Comprehensive error handling
- Data validation before import
- Transaction rollback on failures

---

## Future Enhancements

1. **Real-time Progress**
   - WebSocket connection for live import status
   - File-by-file progress bars
   - Estimated time remaining

2. **Scheduled Imports**
   - Automated daily/weekly imports
   - Email notifications on completion
   - Failure alerts

3. **Cloud Storage Integration**
   - Import from OneDrive/SharePoint
   - Import from Dropbox
   - Direct ACC API integration

4. **Advanced Validation**
   - Pre-import data quality checks
   - Duplicate detection
   - Schema version validation

5. **Analytics Dashboard**
   - Import frequency tracking
   - Data volume metrics
   - Error rate monitoring

---

## Contact & Support

For questions or issues during implementation:
- Review Tkinter implementation: `ui/tab_data_imports.py`
- Check handler documentation: `handlers/acc_handler.py`, `handlers/rvt_health_importer.py`
- Database schema reference: `constants/schema.py`
- API patterns: `backend/app.py`

---

**Document Version**: 1.0  
**Last Updated**: October 13, 2025  
**Status**: Ready for Implementation
