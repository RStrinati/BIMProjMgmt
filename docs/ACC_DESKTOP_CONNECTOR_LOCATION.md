# ACC Desktop Connector - Current Implementation Location

## 🎯 Key Finding: This Feature Lives in Project Setup Tab

### Current Implementation

**Tab Location**: **Project Setup Tab** (NOT Data Imports Tab)

**Why It's There**: The Desktop Connector folder path is part of the **project configuration** along with Model Folder Path and IFC Folder Path. It's configured once per project and then used repeatedly for file extraction.

---

## 📍 Exact File Locations

### Tkinter UI Files

1. **`ui/tab_project.py`** - Project Setup Tab Definition
   - Line 33: `def build_project_tab(tab, status_var)` - Main tab builder
   - Line 104: `frame_paths` - Linked Folder Paths frame
   - Line 107: Model Folder Path entry
   - Line 108: IFC Folder Path entry
   - Line 163: `extract_files()` function - Calls `insert_files_into_tblACCDocs()`

2. **`phase1_enhanced_ui.py`** - Enhanced UI Implementation (lines 1301-1650)
   - **Line 1301**: `configure_paths()` - Configure Desktop Connector folder path
   - **Line 1346**: `extract_acc_files()` - Trigger extraction with validation
   - **Line 1391**: `_perform_desktop_connector_extraction()` - Main extraction logic with progress dialog

### Database Functions (`database.py`)

**Folder Path Management**:
- **Line 683**: `save_acc_folder_path()` - Save Desktop Connector folder path to database
- **Line 703**: `get_acc_folder_path()` - Retrieve saved folder path
- **Line 1429**: `get_project_folders()` - Get all project folder paths (Model, IFC, Data)
- **Line 1443**: `update_project_folders()` - Update project folder paths

**File Extraction**:
- **Line 542**: `insert_files_into_tblACCDocs()` - Extract files from folder and insert to database

---

## 🔄 User Workflow (Current Tkinter)

### Step 1: Configure Path (One-time per project)
1. Navigate to **Project Setup** tab
2. Select active project from dropdown
3. Click **"Configure Paths"** button
4. Browse to Desktop Connector folder on PC
5. Path saved to database via `save_acc_folder_path()`

### Step 2: Extract Files (Repeatable)
1. Navigate to **Project Setup** tab
2. Select active project
3. Click **"Extract Files from Desktop Connector"** button
4. System validates:
   - Folder path exists in database
   - Folder exists on disk
5. Confirmation dialog warns: "This will override existing data"
6. Progress dialog shows:
   - Current file being processed
   - Progress bar (0-100%)
   - File count (e.g., "45/120 files")
7. Files extracted to `ProjectManagement.dbo.tblACCDocs`
8. Success message shows total files processed

### Step 3: View Results
- Files are now in `tblACCDocs` table
- Can be viewed in various reports/analytics
- Used for model tracking across project lifecycle

---

## 📊 Database Schema

### Target Table: `ProjectManagement.dbo.tblACCDocs`

**Columns**:
- `id` (INT, PRIMARY KEY, IDENTITY)
- `project_id` (INT, FOREIGN KEY → tblProjects)
- `file_name` (NVARCHAR(255)) - e.g., "Building_A.rvt"
- `file_path` (NVARCHAR(500)) - e.g., "C:/ACC/Project123/Building_A.rvt"
- `file_type` (NVARCHAR(50)) - e.g., "Revit", "CAD", "IFC", "PDF", "Document"
- `file_size_kb` (DECIMAL(18,2)) - File size in kilobytes
- `date_modified` (DATETIME2) - Last modified date from file system
- `created_at` (DATETIME2, DEFAULT GETDATE()) - Record creation timestamp

**File Types Detected**:
- **Revit**: .rvt, .rfa, .rte
- **CAD**: .dwg, .dxf
- **IFC**: .ifc, .ifczip
- **PDF**: .pdf
- **Document**: .doc, .docx, .txt
- **Spreadsheet**: .xls, .xlsx, .csv
- **Image**: .jpg, .jpeg, .png, .bmp, .tiff
- **Archive**: .zip, .rar, .7z
- **Other**: All other file types

---

## 🔍 Implementation Details

### Override Behavior
The extraction **overrides** existing records for the project:
```python
# Step 1: Delete existing records
cursor.execute(f"DELETE FROM {S.ACCDocs.TABLE} WHERE {S.ACCDocs.PROJECT_ID} = ?", (project_id,))

# Step 2: Insert new records
for file_info in files_found:
    cursor.execute(
        f"INSERT INTO {S.ACCDocs.TABLE} (...) VALUES (...)",
        (file_name, file_path, date_modified, file_type, file_size_kb, created_at, project_id)
    )
```

**Rationale**: 
- Ensures database matches current state of Desktop Connector folder
- Removes deleted files from database
- Updates modified dates and file sizes
- Clean slate for each extraction

### Progress Tracking
```python
# Progress calculation
file_progress = 40 + ((i + 1) / total_files) * 50
progress_var.set(file_progress)
progress_text.config(text=f"{file_progress:.0f}% - {i + 1}/{total_files} files")
```

**Progress Stages**:
- 0-20%: Scanning folder structure
- 20-30%: Connecting to database
- 30-40%: Clearing existing records
- 40-90%: Processing files (50% allocated)
- 90-100%: Finalizing and committing

---

## 🚀 React Implementation Plan

### Where Should It Live in React?

**Option 1: In Project Setup View** (Recommended - Matches Current Design)
- Path: `src/views/ProjectSetup.tsx`
- Tab/Section: "Project Configuration" or "Folder Paths"
- **Pros**: 
  - Matches current Tkinter location
  - Logical grouping with other project configuration
  - One-time setup, repeated extraction pattern
- **Cons**: 
  - Less discoverable for data import workflows

**Option 2: In Data Imports View** (Alternative - Workflow-Based)
- Path: `src/views/DataImports.tsx`
- Tab/Section: "ACC Desktop Connector"
- **Pros**: 
  - Grouped with other import operations
  - More discoverable for import workflows
- **Cons**: 
  - Doesn't match current Tkinter organization
  - Configuration vs. import operation confusion

**Recommendation**: **Option 1 - Project Setup View**
- Maintains consistency with existing Tkinter app
- Users already know where to find it
- Clear separation: Configuration (Project Setup) vs. Import Operations (Data Imports)

### React Components Needed

```typescript
// src/components/project-setup/ACCConnectorPanel.tsx
interface ACCConnectorPanelProps {
  projectId: number;
  onExtractionComplete?: (fileCount: number) => void;
}

// Features:
// - Display current Desktop Connector folder path
// - "Configure Path" button (manual entry or backend browse)
// - "Extract Files" button with confirmation
// - Progress dialog showing:
//   - Current file being processed
//   - Progress bar
//   - File count
// - Success/error messaging
```

### API Endpoints Needed

```python
# backend/app.py

# Get configured path
GET /api/projects/<int:project_id>/acc-connector-folder
Response: {
  'project_id': 1,
  'folder_path': 'C:/ACC/Project123',
  'exists': true
}

# Save path
POST /api/projects/<int:project_id>/acc-connector-folder
Body: { 'folder_path': 'C:/ACC/Project123' }
Response: { 'success': true, 'project_id': 1, 'folder_path': '...' }

# Extract files (with progress)
POST /api/projects/<int:project_id>/acc-connector-extract
Response: {
  'success': true,
  'files_processed': 120,
  'files_inserted': 120,
  'files_failed': 0,
  'execution_time_seconds': 15.3
}

# Get extracted files
GET /api/projects/<int:project_id>/acc-connector-files?limit=100&offset=0
Response: {
  'files': [
    {
      'id': 1,
      'file_name': 'Building_A.rvt',
      'file_type': 'Revit',
      'file_size_kb': 45678.23,
      'date_modified': '2024-10-01T14:30:00',
      'created_at': '2024-10-13T10:15:00'
    },
    ...
  ],
  'total_count': 120,
  'page': 1,
  'page_size': 100
}
```

---

## 📋 Migration Checklist

### Backend Implementation
- [ ] Create `GET /api/projects/<id>/acc-connector-folder` endpoint
- [ ] Create `POST /api/projects/<id>/acc-connector-folder` endpoint
- [ ] Create `POST /api/projects/<id>/acc-connector-extract` endpoint
- [ ] Create `GET /api/projects/<id>/acc-connector-files` endpoint
- [ ] Add progress tracking for long-running extraction
- [ ] Add error handling for missing folders, permission errors
- [ ] Test with various file types and folder structures

### Frontend Implementation
- [ ] Create `ACCConnectorPanel.tsx` component
- [ ] Add to Project Setup view
- [ ] Implement path configuration UI
- [ ] Implement extraction trigger with confirmation
- [ ] Create progress dialog component
- [ ] Add file list display with filtering/sorting
- [ ] Add error handling and validation
- [ ] Test with different project configurations

### Testing
- [ ] Test path configuration (valid/invalid paths)
- [ ] Test extraction with 0 files
- [ ] Test extraction with 1000+ files (performance)
- [ ] Test override behavior (re-extraction)
- [ ] Test file type detection accuracy
- [ ] Test progress tracking accuracy
- [ ] Test concurrent extractions (if allowed)
- [ ] Test permission errors

---

## 💡 Key Insights

1. **Configuration vs. Operation**: The Desktop Connector feature has TWO distinct operations:
   - **Configure Path**: One-time setup per project (like setting Model Folder Path)
   - **Extract Files**: Repeatable operation to refresh database with current files

2. **Override Strategy**: Each extraction replaces ALL existing records for the project, ensuring database matches current folder state

3. **Progress Visibility**: Users need to see progress for large folder scans (100+ files)

4. **File Type Intelligence**: System categorizes files automatically (Revit, CAD, IFC, etc.)

5. **Integration Point**: Extracted files can be used in:
   - Model tracking reports
   - Version control workflows
   - File analytics dashboards
   - Project deliverable tracking

---

## 🔗 Related Documentation

- **Main Roadmap**: `REACT_DATA_IMPORTS_IMPLEMENTATION_ROADMAP.md` - Phase 1.1
- **Quick Reference**: `DATA_IMPORTS_QUICK_REF.md` - ACC Desktop Connector section
- **Index**: `DATA_IMPORTS_INDEX.md` - Feature 1
- **Schema Constants**: `constants/schema.py` - `S.ACCDocs.*`
- **Database Functions**: `database.py` - Lines 542, 683, 703, 1429, 1443

---

**Last Updated**: October 13, 2025  
**Status**: ✅ Documentation Complete - Ready for React Implementation
