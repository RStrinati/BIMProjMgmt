# ACC Sync Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    React Frontend                              │  │
│  │              http://localhost:5173                            │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │  ACCSyncPanel Component (TypeScript)                     │ │  │
│  │  │  ┌────────┬────────┬────────┬────────┐                   │ │  │
│  │  │  │Overview│ Files  │ Issues │ Users  │ ◄─ Tabs           │ │  │
│  │  │  └────────┴────────┴────────┴────────┘                   │ │  │
│  │  │  • Hub selection                                          │ │  │
│  │  │  • Project selection                                      │ │  │
│  │  │  • Real-time data display                                 │ │  │
│  │  │  • Material-UI tables                                     │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  │                            ▲                                   │  │
│  │                            │ REST API (JSON)                   │  │
│  │                            │ axios HTTP client                 │  │
│  │                            ▼                                   │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │  API Client (frontend/src/api/apsSync.ts)                │ │  │
│  │  │  • getHubs()                                              │ │  │
│  │  │  • getProjects(hubId)                                     │ │  │
│  │  │  • getProjectDetails(hubId, projectId)   NEW             │ │  │
│  │  │  • getProjectFolders(hubId, projectId)   NEW             │ │  │
│  │  │  • getProjectIssues(hubId, projectId)    NEW             │ │  │
│  │  │  • getProjectUsers(hubId, projectId)     NEW             │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP GET requests
                                    │ /api/aps-sync/*
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Flask Backend Server                          │
│                      http://localhost:5000                          │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Flask Routes (backend/app.py)                                │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │  Existing Endpoints:                                      │ │  │
│  │  │  • GET /api/aps-sync/login-url                            │ │  │
│  │  │  • GET /api/aps-sync/hubs                                 │ │  │
│  │  │  • GET /api/aps-sync/hubs/{hubId}/projects                │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │  NEW Endpoints (Added in this enhancement):               │ │  │
│  │  │  • GET /api/aps-sync/hubs/{hubId}/projects/{id}/details   │ │  │
│  │  │  • GET /api/aps-sync/hubs/{hubId}/projects/{id}/folders   │ │  │
│  │  │  • GET /api/aps-sync/hubs/{hubId}/projects/{id}/issues    │ │  │
│  │  │  • GET /api/aps-sync/hubs/{hubId}/projects/{id}/users     │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  │                            ▲                                   │  │
│  │                            │ _call_aps_service()               │  │
│  │                            │ Proxy helper function             │  │
│  │                            ▼                                   │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │  • Forwards requests to aps-auth-demo                     │ │  │
│  │  │  • Handles errors and fallbacks                           │ │  │
│  │  │  • Returns JSON responses                                 │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP requests
                                    │ Proxy to Node.js service
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   APS Auth Demo Service (Node.js)                    │
│                      http://localhost:3000                          │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Express Routes (services/aps-auth-demo/index.js)            │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │  Authentication:                                          │ │  │
│  │  │  • /login-pkce          - PKCE OAuth flow                 │ │  │
│  │  │  • /callback            - OAuth callback handler          │ │  │
│  │  │  • /login-2legged       - App-level token                 │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │  Data Endpoints:                                          │ │  │
│  │  │  • /my-hubs                    - User's hubs              │ │  │
│  │  │  • /my-projects/{hubId}        - User's projects          │ │  │
│  │  │  • /my-project-details/{h}/{p} - Project metadata         │ │  │
│  │  │  • /my-project-files/{h}/{p}   - Files & folders          │ │  │
│  │  │  • /my-project-issues/{h}/{p}  - Project issues           │ │  │
│  │  │  • /my-project-users/{h}/{p}   - Team members             │ │  │
│  │  │                                                            │ │  │
│  │  │  • /hubs                       - App-level fallback       │ │  │
│  │  │  • /projects/{hubId}           - App-level fallback       │ │  │
│  │  │  • /project-details/{h}/{p}    - App-level fallback       │ │  │
│  │  │  • /project-files/{h}/{p}      - App-level fallback       │ │  │
│  │  │  • /project-issues/{h}/{p}     - App-level fallback       │ │  │
│  │  │  • /project-users/{h}/{p}      - App-level fallback       │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  │                            ▲                                   │  │
│  │                            │ Token Management                  │  │
│  │                            ▼                                   │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │  Token Storage (in-memory):                               │ │  │
│  │  │  • user_access_token   - 3-legged OAuth token             │ │  │
│  │  │  • refresh_token        - For token renewal               │ │  │
│  │  │  • client_credentials_token - 2-legged app token          │ │  │
│  │  │  • access_token         - PKCE token                      │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS API calls
                                    │ Authorization: Bearer {token}
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 Autodesk Platform Services (Cloud)                   │
│                    https://developer.api.autodesk.com               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Authentication API (OAuth 2.0)                               │  │
│  │  • /authentication/v2/authorize  - User authorization         │  │
│  │  • /authentication/v2/token      - Token exchange             │  │
│  │  • /userprofile/v1/users/@me     - User profile               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Data Management API                                          │  │
│  │  • /project/v1/hubs               - List hubs                 │  │
│  │  • /project/v1/hubs/{id}/projects - List projects             │  │
│  │  • /project/v1/hubs/{h}/projects/{p}       - Project details  │  │
│  │  • /project/v1/hubs/{h}/projects/{p}/topFolders - Folders     │  │
│  │  • /project/v1/projects/{p}/folders/{f}/contents - Files      │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Construction Cloud API                                       │  │
│  │  • /construction/issues/v2/{p}/issues - List issues           │  │
│  │  • /project/v1/hubs/{h}/projects/{p}/users - List users       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  BIM 360 / ACC Project Data                                   │  │
│  │  • Projects, Hubs, Folders                                    │  │
│  │  • Model Files (RVT, IFC, DWG, NWD)                           │  │
│  │  • Issues with custom attributes                              │  │
│  │  • Team members and roles                                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

### User Authentication Flow

```
┌──────┐                ┌─────────┐              ┌──────────┐          ┌────────┐
│ User │                │ React   │              │ APS Auth │          │Autodesk│
│      │                │Frontend │              │  Demo    │          │  APS   │
└──┬───┘                └────┬────┘              └────┬─────┘          └───┬────┘
   │                         │                        │                    │
   │ 1. Click "Authenticate" │                        │                    │
   ├────────────────────────►│                        │                    │
   │                         │ 2. GET /login-url      │                    │
   │                         ├───────────────────────►│                    │
   │                         │                        │                    │
   │                         │ 3. Return login URL    │                    │
   │                         │◄───────────────────────┤                    │
   │                         │                        │                    │
   │ 4. Open popup window    │                        │                    │
   │◄────────────────────────┤                        │                    │
   │                         │                        │                    │
   │ 5. Navigate to /login-pkce                       │                    │
   ├─────────────────────────┼───────────────────────►│                    │
   │                         │                        │ 6. Redirect to APS │
   │                         │                        ├───────────────────►│
   │                         │                        │                    │
   │ 7. Autodesk login page  │                        │                    │
   │◄────────────────────────┼────────────────────────┼────────────────────┤
   │                         │                        │                    │
   │ 8. Enter credentials    │                        │                    │
   ├────────────────────────►│                        │                    │
   │                         │                        │                    │
   │                         │                        │ 9. Auth code       │
   │                         │                        │◄───────────────────┤
   │                         │                        │                    │
   │                         │                        │ 10. Exchange code  │
   │                         │                        ├───────────────────►│
   │                         │                        │                    │
   │                         │                        │ 11. Access token   │
   │                         │                        │◄───────────────────┤
   │                         │                        │                    │
   │ 12. Success page        │                        │                    │
   │◄────────────────────────┼────────────────────────┤                    │
   │                         │                        │                    │
   │ 13. Close popup         │                        │                    │
   ├────────────────────────►│                        │                    │
   │                         │                        │                    │
```

### Data Retrieval Flow (Example: Get Project Files)

```
┌──────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐    ┌────────┐
│ User │    │ React   │    │ Flask   │    │ APS Auth │    │Autodesk│
│      │    │Frontend │    │ Backend │    │  Demo    │    │  APS   │
└──┬───┘    └────┬────┘    └────┬────┘    └────┬─────┘    └───┬────┘
   │             │              │              │              │
   │ 1. Select   │              │              │              │
   │   project   │              │              │              │
   ├────────────►│              │              │              │
   │             │              │              │              │
   │             │ 2. GET /api/aps-sync/hubs/{h}/projects/{p}/folders
   │             ├─────────────►│              │              │
   │             │              │              │              │
   │             │              │ 3. Proxy request             │
   │             │              │              │              │
   │             │              │ 4. GET /my-project-files/{h}/{p}
   │             │              ├─────────────►│              │
   │             │              │              │              │
   │             │              │              │ 5. GET /project/v1/hubs/{h}/projects/{p}/topFolders
   │             │              │              ├─────────────►│
   │             │              │              │              │
   │             │              │              │ 6. Folders   │
   │             │              │              │◄─────────────┤
   │             │              │              │              │
   │             │              │              │ 7-N. GET /project/v1/projects/{p}/folders/{f}/contents
   │             │              │              ├─────────────►│
   │             │              │              │              │
   │             │              │              │ 8-N. Files   │
   │             │              │              │◄─────────────┤
   │             │              │              │              │
   │             │              │ 9. Aggregated file data      │
   │             │              │◄─────────────┤              │
   │             │              │              │              │
   │             │ 10. JSON response           │              │
   │             │◄─────────────┤              │              │
   │             │              │              │              │
   │ 11. Display │              │              │              │
   │    files    │              │              │              │
   │◄────────────┤              │              │              │
   │             │              │              │              │
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
├─────────────────────────────────────────────────────────────┤
│ • React 18.2+          - UI library                          │
│ • TypeScript 5.2+      - Type safety                         │
│ • Material-UI 5.14+    - Component library                   │
│ • React Router 6.20+   - Client-side routing                 │
│ • React Query 5.8+     - Server state management & caching   │
│ • Axios 1.6+           - HTTP client                         │
│ • Vite 5.0             - Build tool and dev server           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        Backend Layer                         │
├─────────────────────────────────────────────────────────────┤
│ • Python 3.12+         - Core language                       │
│ • Flask                - Web framework                       │
│ • Flask-CORS           - Cross-origin support                │
│ • pyodbc               - SQL Server connectivity             │
│ • requests             - HTTP client for proxying            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     Authentication Layer                     │
├─────────────────────────────────────────────────────────────┤
│ • Node.js 18+          - Runtime                             │
│ • Express.js           - Web framework                       │
│ • axios                - HTTP client                         │
│ • crypto               - PKCE code generation                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        Cloud Services                        │
├─────────────────────────────────────────────────────────────┤
│ • Autodesk Platform Services (APS)                           │
│   - OAuth 2.0 authentication                                 │
│   - Data Management API                                      │
│   - Construction Cloud API                                   │
│   - User Profile API                                         │
└─────────────────────────────────────────────────────────────┘
```

## Component Hierarchy

```
App
└── Router
    └── DataImportsPage
        └── ACCSyncPanel ⬅️ ENHANCED COMPONENT
            │
            ├── Authentication Section
            │   ├── Authenticate Button
            │   └── Load Hubs Button
            │
            ├── Hubs List
            │   └── Hub Items (selectable)
            │
            ├── Projects List
            │   └── Project Items (selectable)
            │
            └── Project Details Panel ⬅️ NEW
                │
                ├── Overview Tab ⬅️ NEW
                │   ├── Project Metadata
                │   └── Model Folders List
                │
                ├── Files Tab ⬅️ NEW
                │   ├── File Count Alert
                │   └── Model Files Table
                │       ├── Name Column
                │       ├── Type Column
                │       ├── Version Column
                │       ├── Folder Column
                │       └── Modified Column
                │
                ├── Issues Tab ⬅️ NEW
                │   ├── Issue Count Alert
                │   └── Issues Table
                │       ├── Title Column
                │       ├── Status Column (with chips)
                │       ├── Priority Column (with chips)
                │       ├── Assigned To Column
                │       └── Created Column
                │
                └── Users Tab ⬅️ NEW
                    ├── User Count Alert
                    └── Users Table
                        ├── Name Column
                        ├── Email Column
                        ├── Role Column (with chips)
                        ├── Company Column
                        └── Status Column (with chips)
```

## State Management

```
React Query Cache
├── ['aps-sync', 'login-url']
│   └── ApsLoginInfo (login URL and flow info)
│
├── ['aps-sync', 'hubs']
│   └── ApsHubsResponse (list of accessible hubs)
│
├── ['aps-sync', 'projects', hubId]
│   └── ApsProjectsResponse (projects for selected hub)
│
├── ['aps-sync', 'project-details', hubId, projectId] ⬅️ NEW
│   └── ApsProjectDetails (project metadata and stats)
│
├── ['aps-sync', 'project-files', hubId, projectId] ⬅️ NEW
│   └── ApsProjectFiles (folders and model files)
│
├── ['aps-sync', 'project-issues', hubId, projectId] ⬅️ NEW
│   └── ApsProjectIssues (issues list)
│
└── ['aps-sync', 'project-users', hubId, projectId] ⬅️ NEW
    └── ApsProjectUsers (team members)

Component State (useState)
├── selectedHubId: string | null
├── selectedProjectId: string | null ⬅️ NEW
├── selectedProject: ApsProject | null ⬅️ NEW
├── activeTab: number (0=Overview, 1=Files, 2=Issues, 3=Users) ⬅️ NEW
└── showProjectDetails: boolean ⬅️ NEW
```

## Error Handling Flow

```
API Request
    │
    ├─ Success (200)
    │   └─► Display data
    │
    ├─ Authentication Error (401)
    │   └─► Show "Please authenticate" message
    │       └─► Redirect to login
    │
    ├─ Permission Error (403)
    │   └─► Show "Insufficient permissions" message
    │       └─► Suggest requesting access
    │
    ├─ Not Found (404)
    │   └─► Show "Resource not found" message
    │       └─► Check if hub/project exists
    │
    ├─ Rate Limit (429)
    │   └─► Show "Too many requests" message
    │       └─► Automatic retry with backoff
    │
    ├─ Server Error (500+)
    │   └─► Show "Service unavailable" message
    │       └─► Provide retry button
    │
    └─ Network Error (no response)
        └─► Show "Network error" message
            └─► Check connectivity
```

## Security Architecture

```
┌────────────────────────────────────────────────┐
│             Security Layers                    │
├────────────────────────────────────────────────┤
│                                                │
│ 1. Authentication Layer                        │
│    • OAuth 2.0 with PKCE                       │
│    • Tokens stored server-side only            │
│    • No tokens in browser/localStorage         │
│    • Automatic token refresh                   │
│                                                │
│ 2. Authorization Layer                         │
│    • User-level permissions (3-legged)         │
│    • App-level fallback (2-legged)             │
│    • Scope-based access control                │
│                                                │
│ 3. Transport Security                          │
│    • HTTPS for all API calls                   │
│    • Secure callback URLs                      │
│    • CORS properly configured                  │
│                                                │
│ 4. Data Security                               │
│    • No sensitive data in logs                 │
│    • Credentials in .env only                  │
│    • .gitignore protects secrets               │
│                                                │
└────────────────────────────────────────────────┘
```

---

**Legend**:
- ⬅️ NEW - Added in this enhancement
- ► - Data flow direction
- ├─ - Tree branch
- └─ - Tree end

**Last Updated**: January 7, 2026
