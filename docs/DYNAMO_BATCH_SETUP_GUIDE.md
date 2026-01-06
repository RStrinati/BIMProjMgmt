# Dynamo Batch Automation - Setup & Usage Guide

## 🎯 Overview

RevitBatchProcessor integration for running Dynamo scripts on multiple Revit files through your web UI. This enables headless batch execution with safe-open options and maintains your existing JSON → database pipeline.

## 📋 Implementation Checklist

### ✅ Completed Components

1. **Database Schema** - [sql/add_dynamo_batch_tables.sql](../sql/add_dynamo_batch_tables.sql)
   - `DynamoScripts` - Script library
   - `DynamoBatchJobs` - Job tracking
   - `DynamoBatchJobFiles` - File-level progress

2. **Schema Constants** - [constants/schema.py](../constants/schema.py)
   - `DynamoScripts` class
   - `DynamoBatchJobs` class
   - `DynamoBatchJobFiles` class

3. **Backend Service** - [services/dynamo_batch_service.py](../services/dynamo_batch_service.py)
   - Python wrapper for RevitBatchProcessor
   - Job creation and execution
   - Task file generation (JSON)
   - Status tracking

4. **API Endpoints** - [backend/app.py](../backend/app.py)
   - `GET /api/dynamo/scripts` - List available scripts
   - `GET /api/dynamo/jobs` - List jobs with filters
   - `GET /api/dynamo/jobs/<id>` - Job details
   - `POST /api/dynamo/jobs` - Create job
   - `POST /api/dynamo/jobs/<id>/execute` - Execute job
   - `GET /api/projects/<id>/revit-files` - Get project Revit files

5. **Frontend Components**
   - [frontend/src/api/dynamoBatch.ts](../frontend/src/api/dynamoBatch.ts) - TypeScript API client
   - [frontend/src/components/dataImports/DynamoBatchRunner.tsx](../frontend/src/components/dataImports/DynamoBatchRunner.tsx) - React UI
   - [frontend/src/components/dataImports/RevitHealthPanel.tsx](../frontend/src/components/dataImports/RevitHealthPanel.tsx) - Tab integration

## 🚀 Setup Instructions

### Step 1: Database Migration

Run the SQL migration to create required tables:

```powershell
# Connect to SQL Server
sqlcmd -S YOUR_SERVER -d ProjectManagement -i sql/add_dynamo_batch_tables.sql
```

Or execute manually in SSMS.

### Step 2: Install RevitBatchProcessor

Download and install [RevitBatchProcessor](https://github.com/bvn-architecture/RevitBatchProcessor):

1. Clone/download the repository
2. Build or download the release
3. Install to one of these paths (or update `dynamo_batch_service.py`):
   - `C:\Program Files\RevitBatchProcessor\RevitBatchProcessor.exe`
   - `C:\Program Files (x86)\RevitBatchProcessor\RevitBatchProcessor.exe`
   - `C:\Tools\RevitBatchProcessor\RevitBatchProcessor.exe`

### Step 3: Register Your Dynamo Scripts

Update the sample scripts in [sql/add_dynamo_batch_tables.sql](../sql/add_dynamo_batch_tables.sql) (lines 78-82) with your actual script paths:

```sql
INSERT INTO [dbo].[DynamoScripts] ([script_name], [script_path], [description], [category], [output_folder])
VALUES 
    ('Model Health Check', 'C:\DynamoScripts\HealthCheck.dyn', 'Comprehensive Revit model health analysis with JSON export', 'Health Check', 'C:\Exports\DynamoHealth'),
    ('Family Size Analysis', 'C:\DynamoScripts\FamilySizeAnalysis.dyn', 'Analyzes family sizes and complexity metrics', 'Health Check', 'C:\Exports\DynamoHealth'),
    ('Naming Convention Check', 'C:\DynamoScripts\NamingCheck.dyn', 'Validates element naming against project standards', 'QA/QC', 'C:\Exports\DynamoHealth');
```

Or insert via Python:

```python
from database import connect_to_db
from constants import schema as S

conn = connect_to_db()
cursor = conn.cursor()

cursor.execute(f"""
    INSERT INTO {S.DynamoScripts.TABLE} 
    ({S.DynamoScripts.SCRIPT_NAME}, {S.DynamoScripts.SCRIPT_PATH}, {S.DynamoScripts.DESCRIPTION}, {S.DynamoScripts.CATEGORY}, {S.DynamoScripts.OUTPUT_FOLDER})
    VALUES (?, ?, ?, ?, ?)
""", ('My Health Check', 'C:\\Scripts\\MyHealthCheck.dyn', 'Custom health analysis', 'Health Check', 'C:\\Exports'))

conn.commit()
conn.close()
```

### Step 4: Configure Project Folders

Ensure projects have their `folder_path` set in the database (should already exist):

```sql
UPDATE Projects
SET folder_path = 'C:\Projects\MyProject\Models'
WHERE project_id = 1;
```

### Step 5: Start Backend & Frontend

```powershell
# Backend
cd backend
python app.py

# Frontend (new terminal)
cd frontend
npm run dev
```

## 📖 Usage Workflow

### In the Web UI

1. Navigate to **Data Imports** → **Revit Health Check** tab
2. Select the **"Run Health Scripts"** sub-tab
3. **Job Configuration**:
   - Enter a job name (e.g., "Weekly Health Check - Jan 2026")
   - Select a Dynamo script from the dropdown
   - Configure safe-open options:
     - ✅ Detach from Central (recommended)
     - ✅ Audit on Opening
     - ⬜ Close All Worksets (faster but limited data)
     - ⬜ Discard Worksets (creates local copy)
     - Timeout: 30 minutes

4. **File Selection**:
   - Files auto-populate from project folder path
   - Select individual files or "Select All"
   - View file size and modification dates

5. **Execute**:
   - Click "Run on X Files"
   - Job is created and queued immediately
   - Monitor progress in "Recent Jobs" table

### Job Status Tracking

The "Recent Jobs" table auto-refreshes every 5 seconds:

- **Status**: pending → queued → running → completed/failed
- **Progress**: File count and percentage
- **Success/Error Counts**: ✓ and ✗ indicators
- **Linear Progress Bar**: Visual progress

### Behind the Scenes

1. Job is created in database
2. Task JSON file is generated: `C:\Temp\DynamoBatchTasks\job_<id>_<uuid>.json`
3. RevitBatchProcessor reads the task file
4. Scripts execute on each Revit file
5. JSON outputs are written to configured output folder
6. Import your JSON files via "Import Health Data" tab (existing workflow)

## 🔧 Configuration Options

### Job Configuration (JSON)

Stored in `DynamoBatchJobs.configuration` column:

```json
{
  "detach_from_central": true,
  "audit_on_opening": true,
  "close_all_worksets": false,
  "discard_worksets": false,
  "timeout_minutes": 30
}
```

### RevitBatchProcessor Task File Format

Example generated task file:

```json
{
  "TaskScript": "C:\\Scripts\\HealthCheck.dyn",
  "RevitFileList": [
    "C:\\Projects\\Model1.rvt",
    "C:\\Projects\\Model2.rvt"
  ],
  "AuditOnOpening": true,
  "DetachFromCentral": true,
  "CloseAllWorksets": false,
  "DiscardWorksets": false,
  "TimeoutMinutes": 30,
  "LogFolder": "C:\\Exports\\DynamoHealth"
}
```

## 📊 Database Schema

### DynamoScripts

| Column | Type | Description |
|--------|------|-------------|
| script_id | INT | Primary key |
| script_name | NVARCHAR(255) | Display name |
| script_path | NVARCHAR(500) | Full path to .dyn file |
| description | NVARCHAR(MAX) | Optional description |
| category | NVARCHAR(100) | Health Check, QA/QC, Export, Analysis |
| output_folder | NVARCHAR(500) | Default JSON output location |
| is_active | BIT | Enabled/disabled flag |

### DynamoBatchJobs

| Column | Type | Description |
|--------|------|-------------|
| job_id | INT | Primary key |
| job_name | NVARCHAR(255) | User-provided job name |
| script_id | INT | FK to DynamoScripts |
| project_id | INT | FK to Projects |
| status | NVARCHAR(50) | pending, queued, running, completed, failed |
| total_files | INT | Number of files in job |
| processed_files | INT | Files completed |
| success_count | INT | Successfully processed |
| error_count | INT | Failed files |
| task_file_path | NVARCHAR(500) | Path to generated task JSON |
| output_folder | NVARCHAR(500) | Where JSON exports go |
| configuration | NVARCHAR(MAX) | JSON config string |

### DynamoBatchJobFiles

| Column | Type | Description |
|--------|------|-------------|
| job_file_id | INT | Primary key |
| job_id | INT | FK to DynamoBatchJobs |
| file_path | NVARCHAR(500) | Full path to Revit file |
| file_name | NVARCHAR(255) | File name |
| status | NVARCHAR(50) | pending, processing, completed, failed |
| output_file_path | NVARCHAR(500) | Generated JSON path |

## 🎨 UI Features

### Script Dropdown

- Shows all active scripts
- Grouped by category (Health Check, QA/QC, etc.)
- Displays description when selected

### File Table

- Sortable columns
- File size display (KB/MB/GB)
- Last modified date
- Checkbox selection
- "Select All" toggle

### Safe-Open Options

- **Detach from Central**: Opens workshared models without sync
- **Audit on Opening**: Fixes model corruption
- **Close All Worksets**: Faster opening, limited element access
- **Discard Worksets**: Creates local copy, removes worksharing
- **Timeout**: Max minutes per file (default 30)

### Job Monitoring

- Auto-refresh every 5 seconds
- Color-coded status chips
- Progress bars
- Success/error counters
- Timestamps

## 🔍 Troubleshooting

### "RevitBatchProcessor executable not found"

**Solution**: Install RBP and ensure it's in one of the default paths, or update `services/dynamo_batch_service.py`:

```python
self.rbp_path = r"C:\Your\Custom\Path\RevitBatchProcessor.exe"
```

### "No Revit files found"

**Solution**: Check project `folder_path` in database:

```sql
SELECT project_id, project_name, folder_path
FROM Projects
WHERE project_id = <YOUR_PROJECT_ID>;
```

### Scripts not appearing

**Solution**: Check `is_active` flag:

```sql
SELECT * FROM DynamoScripts WHERE is_active = 1;
```

### Job stuck in "queued" status

**Solution**: Currently, jobs must be manually executed via RevitBatchProcessor. Future enhancement: auto-execute via subprocess or scheduled tasks.

## 🚧 Future Enhancements

1. **Auto-Execution**: Subprocess integration to launch RBP directly
2. **Log Parsing**: Parse RBP output logs and update job status
3. **Scheduling**: Cron/Task Scheduler integration for recurring runs
4. **Email Notifications**: Alert on job completion/failure
5. **Custom Scripts Upload**: Web-based script management
6. **Revit Version Detection**: Auto-select correct Revit version

## 📝 Integration with Existing Pipeline

Your current workflow is **preserved**:

1. **Old Way**: Bird Tools → JSON files → Import via UI → Database
2. **New Way**: Web UI → RevitBatchProcessor → JSON files → Import via UI → Database

The "Import Health Data" tab (Tab 1) still works for importing JSON outputs.

## 🆘 Support

- RevitBatchProcessor Docs: https://github.com/bvn-architecture/RevitBatchProcessor
- Dynamo Forum: https://forum.dynamobim.com/
- Issue Tracking: Create GitHub issues in your repo

---

**Author**: GitHub Copilot Agent  
**Date**: January 6, 2026  
**Version**: 1.0
