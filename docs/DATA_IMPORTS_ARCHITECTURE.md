# Data Imports Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REACT FRONTEND (Browser)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      DataImportsPage.tsx                              │  │
│  │                    (Main Container with Tabs)                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         │                          │                          │             │
│         ▼                          ▼                          ▼             │
│  ┌─────────────┐          ┌──────────────┐          ┌──────────────┐       │
│  │ACC Import   │          │Revizto       │          │Revit Health  │       │
│  │Panel        │          │Import Panel  │          │Panel         │       │
│  └─────────────┘          └──────────────┘          └──────────────┘       │
│         │                          │                          │             │
│         │  Folder Path Input       │  Start Extraction       │  JSON Folder │
│         │  Import Logs Display     │  History Display        │  Control File│
│         │                          │                          │             │
└─────────┼──────────────────────────┼──────────────────────────┼─────────────┘
          │                          │                          │
          │ HTTP/REST API            │                          │
          ▼                          ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLASK BACKEND (Python)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────┐    ┌────────────────────┐    ┌─────────────────┐   │
│  │ ACC API Endpoints  │    │ Revizto Endpoints  │    │ Health Endpoints│   │
│  ├────────────────────┤    ├────────────────────┤    ├─────────────────┤   │
│  │ GET /acc-folder    │    │ POST /start-extract│    │ GET /health-files│  │
│  │ POST /acc-folder   │    │ GET /extraction-runs│   │ POST /control-file│ │
│  │ POST /acc-import   │    │ GET /revizto-issues│    │ POST /health-import││
│  │ GET /import-logs   │    │ POST /sync-issues  │    │ GET /health-summary││
│  │ GET /acc-issues    │    │                    │    │                  │   │
│  └─────────┬──────────┘    └──────────┬─────────┘    └────────┬─────────┘   │
│            │                          │                        │             │
│            ▼                          ▼                        ▼             │
│  ┌────────────────────┐    ┌────────────────────┐    ┌─────────────────┐   │
│  │ acc_handler.py     │    │ Revizto Service    │    │rvt_health_      │   │
│  ├────────────────────┤    ├────────────────────┤    │ importer.py     │   │
│  │ import_acc_data()  │    │ Launch exporter    │    ├─────────────────┤   │
│  │ - Parse CSV/ZIP    │    │ Process extraction │    │import_health_   │   │
│  │ - Validate data    │    │ Track runs         │    │  data()         │   │
│  │ - Insert staging   │    │                    │    │ - Parse JSON    │   │
│  │ - Run merge SQL    │    │                    │    │ - Insert records│   │
│  └─────────┬──────────┘    └──────────┬─────────┘    └────────┬─────────┘   │
│            │                          │                        │             │
└────────────┼──────────────────────────┼────────────────────────┼─────────────┘
             │                          │                        │
             ▼                          ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SQL SERVER DATABASES                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────┐    ┌────────────────────┐    ┌─────────────────┐   │
│  │ acc_data_schema    │    │ ProjectManagement  │    │RevitHealthCheckDB│  │
│  ├────────────────────┤    ├────────────────────┤    ├─────────────────┤   │
│  │ staging.issues_*   │    │ ReviztoExtraction- │    │ tblRvtProjHealth│   │
│  │ dbo.vw_issues_*    │    │   Runs             │    │ tblRvtUser      │   │
│  │ staging.projects   │    │ tblReviztoProjects │    │ tblSysName      │   │
│  │ staging.users      │    │ tblReviztoIssues   │    │ vw_LatestRvtFiles│  │
│  │ + 20+ more tables  │    │ ACCImportFolders   │    │ tblControlModels│   │
│  │                    │    │ ACCImportLogs      │    │                  │   │
│  └────────────────────┘    └────────────────────┘    └─────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES & TOOLS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  ReviztoDataExporter.exe (C# .NET Application)                     │     │
│  ├────────────────────────────────────────────────────────────────────┤     │
│  │  - Connects to Revizto API                                         │     │
│  │  - Fetches projects, issues, licenses                              │     │
│  │  - Writes to SQL Server databases                                  │     │
│  │  - Logs extraction runs                                            │     │
│  │  - Location: services/revizto-dotnet/ReviztoDataExporter/          │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Autodesk Construction Cloud (ACC) Desktop Connector               │     │
│  ├────────────────────────────────────────────────────────────────────┤     │
│  │  - Syncs ACC data to local folder                                  │     │
│  │  - Exports as CSV files in ZIP archive                             │     │
│  │  - User manually configures export location                        │     │
│  │  - System imports from that location                               │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │  Revit Health Check Export (Dynamo/Plugin)                         │     │
│  ├────────────────────────────────────────────────────────────────────┤     │
│  │  - Runs inside Autodesk Revit                                      │     │
│  │  - Exports model health data as JSON                               │     │
│  │  - Includes warnings, views, families, etc.                        │     │
│  │  - Files combined into single JSON per model                       │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
                              DATA FLOW DIAGRAMS
═══════════════════════════════════════════════════════════════════════════════

1. ACC IMPORT FLOW
─────────────────────

   User Input              Backend Processing           Database Updates
   ──────────              ──────────────────           ────────────────

   Select Folder    ──►    Validate Path         ──►   Save to
   /ZIP File               Extract ZIP (if needed)      ACCImportFolders

        │                         │                            │
        ▼                         ▼                            ▼
                                                        
   Click Import    ──►    Parse CSV Files        ──►   Insert to
                          - issues_issues.csv           staging.issues_*
                          - projects.csv                staging.projects
                          - users.csv                   staging.users
                          - 20+ more tables             + 20 more
                                                        
        │                         │                            │
        ▼                         ▼                            ▼
                                                        
   View Results    ◄──    Run Merge Scripts      ◄──   Merge to dbo.*
                          - merge_issues.sql            vw_issues_expanded_pm
                          - merge_projects.sql          Created/updated
                          - etc.                        
                                                        
        │                         │                            │
        ▼                         ▼                            ▼
                                                        
   Check Logs      ◄──    Log Import Summary     ◄──   Insert to
                          - Tables processed            ACCImportLogs
                          - Rows imported               
                          - Errors/warnings             


2. REVIZTO EXTRACTION FLOW
──────────────────────────

   User Action            Backend Processing           Database Updates
   ───────────            ──────────────────           ────────────────

   Click "Start    ──►    Create extraction run  ──►   Insert to
   Extraction"            - Generate run_id             ReviztoExtraction-
                          - Record start time            Runs (status='running')

        │                         │                            │
        ▼                         ▼                            ▼
                                                        
   Launch         ──►    Execute                ──►   Update
   Exporter Tool         ReviztoDataExporter.exe       ReviztoExtraction-
                         - Connect to API               Runs (progress)
                         - Fetch projects
                         - Fetch issues                 
                         - Fetch licenses               

        │                         │                            │
        ▼                         ▼                            ▼
                                                        
   Monitor        ◄──    Process Data           ──►   Insert/Update
   Progress               - Parse responses             tblReviztoProjects
                          - Transform data              tblReviztoIssues
                          - Validate                    tblReviztoLicenses

        │                         │                            │
        ▼                         ▼                            ▼
                                                        
   View Results   ◄──    Complete run           ──►   Update
                         - Update statistics           ReviztoExtraction-
                         - Mark completed              Runs (status='completed')
                                                       - projects_extracted
                                                       - issues_extracted


3. REVIT HEALTH CHECK IMPORT FLOW
─────────────────────────────────

   User Input              Backend Processing           Database Updates
   ──────────              ──────────────────           ────────────────

   Select Control  ──►    Validate file exists   ──►   Update
   Model File             in health files list          tblControlModels

        │                         │                            │
        ▼                         ▼                            ▼
                                                        
   Select JSON     ──►    Validate folder path   ──►   (No update yet)
   Folder

        │                         │                            │
        ▼                         ▼                            ▼
                                                        
   Click Import    ──►    Process JSON files     ──►   Insert to
                          - Read combined_*.json        tblRvtProjHealth
                          - Extract metadata            - File info
                          - Parse nested data           - Warnings
                                                        - Views/families

        │                         │                            │
        ▼                         ▼                            ▼
                                                        
   View Health     ◄──    Query latest data      ◄──   Select from
   Summary                                              vw_LatestRvtFiles
                                                        - Group by project
                                                        - Latest export only

        │                         │                            │
        ▼                         ▼                            ▼
                                                        
   Analyze         ◄──    Generate reports       ◄──   Join tables
   Quality                - Warning trends              tblRvtProjHealth
                          - Model sizes                 tblControlModels
                          - View counts                 Projects


═══════════════════════════════════════════════════════════════════════════════
                           COMPONENT HIERARCHY
═══════════════════════════════════════════════════════════════════════════════

DataImportsPage
│
├─── Tabs (Material-UI)
│    ├─── "ACC Import" Tab
│    │    └─── ACCImportPanel
│    │         ├─── FolderPathInput
│    │         │    ├─── TextField (path entry)
│    │         │    └─── Button (browse - limited)
│    │         ├─── Button (Save Path)
│    │         ├─── Button (Import)
│    │         ├─── ImportHistoryTable
│    │         │    └─── Table (logs with dates)
│    │         └─── ACCIssuesPanel
│    │              ├─── IssueStatsCards
│    │              └─── IssuesTable
│    │
│    ├─── "Revizto" Tab
│    │    └─── ReviztoImportPanel
│    │         ├─── Button (Start Extraction)
│    │         ├─── Button (Refresh History)
│    │         ├─── ExtractionHistoryTable
│    │         │    └─── Table (run details)
│    │         ├─── ProjectChangesTable
│    │         │    └─── Table (modified projects)
│    │         └─── ReviztoIssuesPanel
│    │              └─── IssuesTable
│    │
│    └─── "Revit Health" Tab
│         └─── RevitHealthPanel
│              ├─── Select (Control Model)
│              ├─── Button (Save Control)
│              ├─── FolderPathInput (JSON folder)
│              ├─── Button (Import JSONs)
│              └─── HealthSummaryTable
│                   ├─── Table (file list)
│                   └─── Charts (warnings, sizes)
│
└─── StatusBar
     └─── Snackbar (success/error messages)


═══════════════════════════════════════════════════════════════════════════════
                             SECURITY CONSIDERATIONS
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔒 FILE PATH VALIDATION                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Path Traversal Prevention                                               │
│     ❌ DON'T: Accept any user path                                          │
│     ✅ DO: Validate against allowed root directories                        │
│                                                                              │
│     WHITELIST = [                                                           │
│         r"C:\Users\*\Documents\ACC\",                                       │
│         r"C:\iimbe\",                                                       │
│         r"D:\ProjectData\"                                                  │
│     ]                                                                        │
│                                                                              │
│  2. File Type Validation                                                    │
│     ❌ DON'T: Accept executable files                                       │
│     ✅ DO: Validate file extensions                                         │
│                                                                              │
│     ALLOWED_EXTENSIONS = {'.csv', '.zip', '.json'}                         │
│                                                                              │
│  3. Size Limits                                                             │
│     ❌ DON'T: Allow unlimited file sizes                                    │
│     ✅ DO: Set reasonable limits                                            │
│                                                                              │
│     MAX_ZIP_SIZE = 500 * 1024 * 1024  # 500MB                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔐 ACCESS CONTROL                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Project-Level Permissions                                               │
│     - Users can only import for projects they own/manage                   │
│     - Check user_id matches project assignment                             │
│                                                                              │
│  2. Rate Limiting                                                           │
│     - Prevent import spam/DoS                                               │
│     - Limit imports to 5 per hour per user                                 │
│                                                                              │
│  3. Audit Logging                                                           │
│     - Log all import attempts                                               │
│     - Track who imported what and when                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
                              PERFORMANCE OPTIMIZATION
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ ⚡ LARGE FILE HANDLING                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Problem: ACC ZIP files can be 100MB+, imports take 5-10 minutes           │
│                                                                              │
│  Solutions:                                                                 │
│                                                                              │
│  1. Background Task Processing                                              │
│     ┌─────────────────────────────────────────────────────────┐            │
│     │ Frontend              Backend               Worker      │            │
│     │   │                      │                     │        │            │
│     │   │ POST /import         │                     │        │            │
│     │   ├─────────────────────►│                     │        │            │
│     │   │                      │ Enqueue task        │        │            │
│     │   │                      ├────────────────────►│        │            │
│     │   │ {task_id: "123"}    │                     │        │            │
│     │   │◄─────────────────────┤                     │        │            │
│     │   │                      │                     │        │            │
│     │   │ GET /task/123/status │                     │        │            │
│     │   ├─────────────────────►│                     │        │            │
│     │   │ {status: "running"}  │                     │        │            │
│     │   │◄─────────────────────┤                     │        │            │
│     │   │                      │                     │        │            │
│     │   │ (poll every 2 sec)   │                  Process     │            │
│     │   │                      │                  CSV files   │            │
│     │   │                      │                     │        │            │
│     │   │ GET /task/123/status │                     │        │            │
│     │   ├─────────────────────►│                     │        │            │
│     │   │ {status: "complete"} │                     │        │            │
│     │   │◄─────────────────────┤                     │        │            │
│     └─────────────────────────────────────────────────────────┘            │
│                                                                              │
│  2. Streaming Uploads                                                       │
│     - Use chunked transfer encoding                                         │
│     - Process files as they upload                                          │
│                                                                              │
│  3. Database Bulk Operations                                                │
│     - Use cursor.executemany() with batches                                 │
│     - cursor.fast_executemany = True                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
