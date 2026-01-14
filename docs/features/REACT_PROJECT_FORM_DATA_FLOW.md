# React Project Form - Data Flow Diagram

## Complete Data Flow: Create → Save → Display

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         REACT FRONTEND                                  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  ProjectFormDialog.tsx                                        │     │
│  │                                                               │     │
│  │  User Selects:                                                │     │
│  │  ┌────────────────────────────────────────────────────┐      │     │
│  │  │ Project Name:     "My Project"                     │      │     │
│  │  │ Project Number:   "PROJ-001"                       │      │     │
│  │  │ Project Type:     [Commercial ▼]  ← Dropdown       │      │     │
│  │  │ Status:           [Active ▼]      ← Dropdown       │      │     │
│  │  │ Priority:         [High ▼]        ← Dropdown       │      │     │
│  │  │ Start Date:       [2025-01-01]    ← Date Picker    │      │     │
│  │  │ End Date:         [2025-12-31]    ← Date Picker    │      │     │
│  │  └────────────────────────────────────────────────────┘      │     │
│  │                                                               │     │
│  │  On Submit → formData = {                                    │     │
│  │    project_name: "My Project",                               │     │
│  │    project_number: "PROJ-001",                               │     │
│  │    project_type: "Commercial",  ← Type NAME (string)         │     │
│  │    status: "Active",                                         │     │
│  │    priority: "High",                                         │     │
│  │    start_date: "2025-01-01",                                 │     │
│  │    end_date: "2025-12-31"                                    │     │
│  │  }                                                            │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                ↓                                       │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  api/projects.ts                                              │     │
│  │  projectsApi.create(formData)                                 │     │
│  └──────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
                                 ↓
                    POST /api/projects
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       FLASK BACKEND (Python)                            │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  backend/app.py                                               │     │
│  │  @app.route('/api/projects', methods=['POST'])                │     │
│  │                                                               │     │
│  │  payload = _extract_project_payload(request.json)            │     │
│  │    ↓                                                          │     │
│  │  create_project(payload)  ← calls shared service             │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                ↓                                       │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  shared/project_service.py                                    │     │
│  │                                                               │     │
│  │  _normalise_payload() {                                       │     │
│  │    // Convert project_type NAME → type_id                    │     │
│  │    if (payload.project_type == "Commercial") {               │     │
│  │      SELECT type_id FROM project_types                        │     │
│  │      WHERE type_name = "Commercial"                           │     │
│  │      // Returns: type_id = 7                                  │     │
│  │    }                                                          │     │
│  │  }                                                            │     │
│  │                                                               │     │
│  │  ProjectPayload.to_db_payload() returns:                     │     │
│  │  {                                                            │     │
│  │    project_name: "My Project",                               │     │
│  │    contract_number: "PROJ-001",                              │     │
│  │    type_id: 7,  ← Converted from "Commercial"               │     │
│  │    status: "Active",                                         │     │
│  │    priority: "High",                                         │     │
│  │    start_date: "2025-01-01",                                 │     │
│  │    end_date: "2025-12-31"                                    │     │
│  │  }                                                            │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                ↓                                       │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  database.py                                                  │     │
│  │  insert_project_full(db_payload)                             │     │
│  └──────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         SQL SERVER DATABASE                             │
│                                                                         │
│  INSERT INTO projects (                                                 │
│    project_name,                                                        │
│    contract_number,                                                     │
│    type_id,         ← Stores ID (7), not name                          │
│    status,                                                              │
│    priority,                                                            │
│    start_date,                                                          │
│    end_date                                                             │
│  ) VALUES (                                                             │
│    'My Project',                                                        │
│    'PROJ-001',                                                          │
│    7,               ← ID for "Commercial"                               │
│    'Active',                                                            │
│    'High',                                                              │
│    '2025-01-01',                                                        │
│    '2025-12-31'                                                         │
│  )                                                                      │
│                                                                         │
│  ✓ Project ID = 123 created                                            │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════

## Retrieve & Display Flow

┌─────────────────────────────────────────────────────────────────────────┐
│                         REACT FRONTEND                                  │
│                                                                         │
│  User navigates to /projects/123                                        │
│                                ↓                                       │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  ProjectDetailPage.tsx                                        │     │
│  │  useQuery(['project', 123])                                   │     │
│  │    ↓                                                          │     │
│  │  projectsApi.getById(123)                                     │     │
│  └──────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
                                 ↓
                    GET /api/project/123
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       FLASK BACKEND (Python)                            │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  backend/app.py                                               │     │
│  │  @app.route('/api/project/<int:project_id>', methods=['GET']) │     │
│  │                                                               │     │
│  │  projects = get_projects_full()                               │     │
│  │  return project where project_id == 123                       │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                ↓                                       │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  database.py                                                  │     │
│  │  get_projects_full()                                          │     │
│  │    ↓                                                          │     │
│  │  SELECT * FROM vw_projects_full                               │     │
│  └──────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         SQL SERVER DATABASE                             │
│                                                                         │
│  VIEW: vw_projects_full                                                 │
│                                                                         │
│  SELECT                                                                 │
│    p.project_id,              ← 123                                     │
│    p.project_name,            ← "My Project"                            │
│    p.contract_number,         ← "PROJ-001"                              │
│    p.type_id,                 ← 7                                       │
│    pt.type_name as project_type,  ← "Commercial" (via JOIN)            │
│    p.status,                  ← "Active"                                │
│    p.priority,                ← "High"                                  │
│    p.start_date,              ← "2025-01-01"                            │
│    p.end_date                 ← "2025-12-31"                            │
│  FROM projects p                                                        │
│  LEFT JOIN project_types pt ON p.type_id = pt.type_id                  │
│  WHERE p.project_id = 123                                               │
│                                                                         │
│  ✓ Returns project data with type NAME, not ID                         │
└─────────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       FLASK BACKEND (Python)                            │
│                                                                         │
│  Returns JSON:                                                          │
│  {                                                                      │
│    project_id: 123,                                                     │
│    project_name: "My Project",                                          │
│    project_number: "PROJ-001",                                          │
│    project_type: "Commercial",  ← Human-readable name                   │
│    status: "Active",                                                    │
│    priority: "High",                                                    │
│    start_date: "2025-01-01",                                            │
│    end_date: "2025-12-31"                                               │
│  }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         REACT FRONTEND                                  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  ProjectDetailPage.tsx                                        │     │
│  │                                                               │     │
│  │  Displays:                                                    │     │
│  │  ┌────────────────────────────────────────────────────┐      │     │
│  │  │  My Project                           [Active]     │      │     │
│  │  │  Project #PROJ-001                                 │      │     │
│  │  │                                                    │      │     │
│  │  │  Client:         N/A                               │      │     │
│  │  │  Project Type:   Commercial  ← ✓ DISPLAYS NAME    │      │     │
│  │  │  Start Date:     01/01/2025  ← ✓ FORMATTED         │      │     │
│  │  │  End Date:       12/31/2025  ← ✓ FORMATTED         │      │     │
│  │  │  Priority:       High        ← ✓ DISPLAYED         │      │     │
│  │  └────────────────────────────────────────────────────┘      │     │
│  │                                                               │     │
│  │  ✅ All fields display correctly                             │     │
│  └──────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════

## Key Points

✓ **Form → Database**: Type NAME converted to type ID
✓ **Database → Display**: Type ID converted back to type NAME via JOIN
✓ **Round Trip**: User never sees IDs, only human-readable names
✓ **Database Integrity**: Stores normalized ID, maintains referential integrity
✓ **API Consistency**: Both GET and POST handle conversions automatically

═══════════════════════════════════════════════════════════════════════════
