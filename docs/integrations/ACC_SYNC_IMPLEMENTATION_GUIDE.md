# ACC Sync Implementation Guide - Full Potential

## Overview

This guide details what's currently implemented in the ACC (Autodesk Construction Cloud) sync feature and what you need to implement to reach its full potential for extracting model data, user information, and other project details.

## Current Implementation Status

### ✅ What's Working

1. **Authentication**
   - 3-legged OAuth with PKCE flow
   - Token management via `aps-auth-demo` service
   - User profile retrieval
   - Status: **FULLY IMPLEMENTED**

2. **Hubs Listing**
   - Endpoint: `GET /api/aps-sync/hubs`
   - Lists all hubs accessible to authenticated user
   - Fallback to app-level token if user token fails
   - Status: **FULLY IMPLEMENTED**

3. **Projects Listing**
   - Endpoint: `GET /api/aps-sync/hubs/{hubId}/projects`
   - Lists projects within a specific hub
   - Fallback to app-level token if user token fails
   - Status: **FULLY IMPLEMENTED**

4. **Frontend UI**
   - `ACCSyncPanel` component for authentication and navigation
   - Hub selection interface
   - Project listing interface
   - Status: **PARTIALLY IMPLEMENTED** (basic listing only)

### ❌ What's Missing (To Reach Full Potential)

1. **Project Details Extraction** - NOT IMPLEMENTED
   - Metadata, folders count, file count, users
   - Required for comprehensive project overview

2. **Folder & File Structure** - NOT IMPLEMENTED
   - Top folders listing
   - Folder contents navigation
   - Model file identification (RVT, IFC, DWG, NWD, etc.)
   - Required for model data extraction

3. **Project Issues** - NOT IMPLEMENTED
   - Issues listing with filters
   - Issue details with custom attributes
   - Required for BIM coordination workflows

4. **Project Users** - NOT IMPLEMENTED
   - Team members listing
   - Roles and permissions
   - Required for user information extraction

5. **Data Persistence** - NOT IMPLEMENTED
   - Saving extracted data to database
   - Linking ACC data to internal projects
   - Historical tracking of synced data

## Architecture Overview

```
┌─────────────────────┐
│   React Frontend    │
│  (ACCSyncPanel)     │
└──────────┬──────────┘
           │ HTTP/REST
           ▼
┌─────────────────────┐
│   Flask Backend     │
│   (app.py)          │
└──────────┬──────────┘
           │ HTTP Proxy
           ▼
┌─────────────────────┐
│  aps-auth-demo      │
│  (Node.js Service)  │
└──────────┬──────────┘
           │ HTTPS
           ▼
┌─────────────────────┐
│  Autodesk Platform  │
│  Services (APS)     │
└─────────────────────┘
```

## Implementation Roadmap

### Phase 1: Backend API Extensions (High Priority)

#### 1.1 Project Details Endpoint

**Purpose**: Get comprehensive project information including metadata and summary statistics.

**Backend Endpoint**: `GET /api/aps-sync/hubs/{hubId}/projects/{projectId}/details`

**APS Service Endpoints Used**:
- `GET /my-project-details/{hubId}/{projectId}` (already exists in aps-auth-demo)
- Returns: project metadata, folder count, file count, model folders

**Implementation**:
```python
@app.route('/api/aps-sync/hubs/<path:hub_id>/projects/<path:project_id>/details', methods=['GET'])
def get_aps_sync_project_details(hub_id, project_id):
    """Get detailed project information including folders and files summary."""
    status_code, payload = _call_aps_service(f"my-project-details/{hub_id}/{project_id}")
    
    if status_code >= 400:
        # Fallback to app token
        fallback_status, fallback_payload = _call_aps_service(f"project-details/{hub_id}/{project_id}")
        if fallback_status < 400:
            payload = {**fallback_payload, "fallback_used": True}
            status_code = fallback_status
    
    return jsonify(payload), status_code
```

#### 1.2 Folders & Files Endpoint

**Purpose**: Navigate folder structure and identify model files.

**Backend Endpoint**: `GET /api/aps-sync/hubs/{hubId}/projects/{projectId}/folders`

**APS Service Endpoints Used**:
- `GET /my-project-files/{hubId}/{projectId}` (already exists in aps-auth-demo)
- Returns: folder structure, all files, model files filtered by extension

**Implementation**:
```python
@app.route('/api/aps-sync/hubs/<path:hub_id>/projects/<path:project_id>/folders', methods=['GET'])
def get_aps_sync_project_folders(hub_id, project_id):
    """Get project folder structure and model files."""
    status_code, payload = _call_aps_service(f"my-project-files/{hub_id}/{project_id}")
    
    if status_code >= 400:
        fallback_status, fallback_payload = _call_aps_service(f"project-files/{hub_id}/{project_id}")
        if fallback_status < 400:
            payload = {**fallback_payload, "fallback_used": True}
            status_code = fallback_status
    
    return jsonify(payload), status_code
```

#### 1.3 Issues Endpoint

**Purpose**: Extract project issues for coordination and tracking.

**Backend Endpoint**: `GET /api/aps-sync/hubs/{hubId}/projects/{projectId}/issues`

**Query Parameters**:
- `status`: Filter by issue status
- `priority`: Filter by priority
- `assigned_to`: Filter by assignee
- `page`: Pagination
- `limit`: Items per page

**APS Service Endpoints Used**:
- `GET /my-project-issues/{hubId}/{projectId}` (already exists in aps-auth-demo)

**Implementation**:
```python
@app.route('/api/aps-sync/hubs/<path:hub_id>/projects/<path:project_id>/issues', methods=['GET'])
def get_aps_sync_project_issues(hub_id, project_id):
    """Get project issues with filtering and pagination."""
    params = {
        'status': request.args.get('status'),
        'priority': request.args.get('priority'),
        'assigned_to': request.args.get('assigned_to'),
        'page': request.args.get('page', 1, type=int),
        'limit': request.args.get('limit', 50, type=int)
    }
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    status_code, payload = _call_aps_service(
        f"my-project-issues/{hub_id}/{project_id}",
        params=params
    )
    
    if status_code >= 400:
        fallback_status, fallback_payload = _call_aps_service(
            f"project-issues/{hub_id}/{project_id}",
            params=params
        )
        if fallback_status < 400:
            payload = {**fallback_payload, "fallback_used": True}
            status_code = fallback_status
    
    return jsonify(payload), status_code
```

#### 1.4 Users Endpoint

**Purpose**: Get project team members and their roles.

**Backend Endpoint**: `GET /api/aps-sync/hubs/{hubId}/projects/{projectId}/users`

**APS Service Endpoints Used**:
- `GET /my-project-users/{hubId}/{projectId}` (already exists in aps-auth-demo)

**Implementation**:
```python
@app.route('/api/aps-sync/hubs/<path:hub_id>/projects/<path:project_id>/users', methods=['GET'])
def get_aps_sync_project_users(hub_id, project_id):
    """Get project users and team members."""
    status_code, payload = _call_aps_service(f"my-project-users/{hub_id}/{project_id}")
    
    if status_code >= 400:
        fallback_status, fallback_payload = _call_aps_service(f"project-users/{hub_id}/{project_id}")
        if fallback_status < 400:
            payload = {**fallback_payload, "fallback_used": True}
            status_code = fallback_status
    
    return jsonify(payload), status_code
```

### Phase 2: Frontend TypeScript Types

**File**: `frontend/src/types/apsSync.ts`

Add the following type definitions:

```typescript
// Project Details Types
export interface ApsProjectDetails {
  success: boolean;
  authMethod?: string;
  projectInfo: {
    id: string;
    name: string;
    status: string;
    created: string;
    updated: string;
    totalTopLevelFolders: number;
    totalFiles: number;
    modelFolders: ApsModelFolder[];
  };
  folders: ApsFolder[];
  actions?: {
    users: string;
    issues: string;
    files: string;
  };
  fallback_used?: boolean;
}

export interface ApsFolder {
  id: string;
  name: string;
  created: string;
  modified: string;
}

export interface ApsModelFolder {
  name: string;
  fileCount: number;
  lastModified: string;
}

// Files Types
export interface ApsProjectFiles {
  success: boolean;
  authMethod?: string;
  projectId: string;
  totalFiles: number;
  lastUpdated: string | null;
  modelFiles: ApsModelFile[];
  allFiles: ApsFile[];
  folders: ApsFolderSummary[];
  fallback_used?: boolean;
}

export interface ApsFile {
  id: string;
  name: string;
  extension?: string;
  size?: number;
  created: string;
  modified: string;
  version?: number;
  folder: string;
}

export interface ApsModelFile extends ApsFile {
  // Model files are files with CAD/BIM extensions
}

export interface ApsFolderSummary {
  id: string;
  name: string;
  counts: {
    files: number;
    models: number;
  };
}

// Issues Types
export interface ApsProjectIssues {
  success: boolean;
  authMethod?: string;
  projectId: string;
  totalIssues: number;
  issues: ApsIssue[];
  page?: number;
  limit?: number;
  fallback_used?: boolean;
}

export interface ApsIssue {
  id: string;
  title: string;
  description?: string;
  status: string;
  priority?: string;
  type?: string;
  assigned_to?: string;
  owner?: string;
  created: string;
  due_date?: string;
  closed_date?: string;
  location?: string;
  custom_attributes?: Record<string, any>;
}

// Users Types
export interface ApsProjectUsers {
  success: boolean;
  authMethod?: string;
  projectId: string;
  userCount: number;
  users: ApsUser[];
  fallback_used?: boolean;
}

export interface ApsUser {
  id: string;
  name: string;
  email?: string;
  role?: string;
  status?: string;
  company?: string;
  lastSignIn?: string;
}
```

### Phase 3: Frontend API Client Extensions

**File**: `frontend/src/api/apsSync.ts`

Add the following methods:

```typescript
export const apsSyncApi = {
  // ... existing methods (getLoginUrl, getHubs, getProjects)

  /** Get detailed project information */
  getProjectDetails: async (hubId: string, projectId: string): Promise<ApsProjectDetails> => {
    const response = await apiClient.get<ApsProjectDetails>(
      `/aps-sync/hubs/${encodeURIComponent(hubId)}/projects/${encodeURIComponent(projectId)}/details`
    );
    return response.data;
  },

  /** Get project folders and model files */
  getProjectFolders: async (hubId: string, projectId: string): Promise<ApsProjectFiles> => {
    const response = await apiClient.get<ApsProjectFiles>(
      `/aps-sync/hubs/${encodeURIComponent(hubId)}/projects/${encodeURIComponent(projectId)}/folders`
    );
    return response.data;
  },

  /** Get project issues with optional filters */
  getProjectIssues: async (
    hubId: string,
    projectId: string,
    filters?: {
      status?: string;
      priority?: string;
      assigned_to?: string;
      page?: number;
      limit?: number;
    }
  ): Promise<ApsProjectIssues> => {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.priority) params.append('priority', filters.priority);
    if (filters?.assigned_to) params.append('assigned_to', filters.assigned_to);
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const response = await apiClient.get<ApsProjectIssues>(
      `/aps-sync/hubs/${encodeURIComponent(hubId)}/projects/${encodeURIComponent(projectId)}/issues?${params}`
    );
    return response.data;
  },

  /** Get project users and team members */
  getProjectUsers: async (hubId: string, projectId: string): Promise<ApsProjectUsers> => {
    const response = await apiClient.get<ApsProjectUsers>(
      `/aps-sync/hubs/${encodeURIComponent(hubId)}/projects/${encodeURIComponent(projectId)}/users`
    );
    return response.data;
  },
};
```

### Phase 4: Frontend UI Enhancements

**File**: `frontend/src/components/dataImports/ACCSyncPanel.tsx`

Add the following features:

1. **Project Selection State**:
```typescript
const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
```

2. **Project Details Query**:
```typescript
const {
  data: projectDetails,
  isLoading: detailsLoading,
  refetch: refetchDetails,
} = useQuery({
  queryKey: ['aps-sync', 'project-details', selectedHubId, selectedProjectId],
  queryFn: () => apsSyncApi.getProjectDetails(selectedHubId || '', selectedProjectId || ''),
  enabled: !!selectedHubId && !!selectedProjectId,
  refetchOnWindowFocus: false,
});
```

3. **Folders/Files Query**:
```typescript
const {
  data: projectFiles,
  isLoading: filesLoading,
} = useQuery({
  queryKey: ['aps-sync', 'project-files', selectedHubId, selectedProjectId],
  queryFn: () => apsSyncApi.getProjectFolders(selectedHubId || '', selectedProjectId || ''),
  enabled: !!selectedHubId && !!selectedProjectId,
  refetchOnWindowFocus: false,
});
```

4. **Issues Query**:
```typescript
const {
  data: projectIssues,
  isLoading: issuesLoading,
} = useQuery({
  queryKey: ['aps-sync', 'project-issues', selectedHubId, selectedProjectId],
  queryFn: () => apsSyncApi.getProjectIssues(selectedHubId || '', selectedProjectId || ''),
  enabled: !!selectedHubId && !!selectedProjectId,
  refetchOnWindowFocus: false,
});
```

5. **Users Query**:
```typescript
const {
  data: projectUsers,
  isLoading: usersLoading,
} = useQuery({
  queryKey: ['aps-sync', 'project-users', selectedHubId, selectedProjectId],
  queryFn: () => apsSyncApi.getProjectUsers(selectedHubId || '', selectedProjectId || ''),
  enabled: !!selectedHubId && !!selectedProjectId,
  refetchOnWindowFocus: false,
});
```

6. **UI Sections**: Add tabs or accordions for:
   - Project Overview (metadata, folder count, file count)
   - Model Files (RVT, IFC, DWG, NWD files with versions)
   - Issues (filterable list with status, priority, assignee)
   - Team Members (users with roles and contact info)

### Phase 5: Data Persistence (Optional but Recommended)

#### 5.1 Database Schema Extensions

Add tables to store synced ACC data:

```sql
-- ACC Sync History
CREATE TABLE dbo.tblACCSyncHistory (
    SyncID INT IDENTITY(1,1) PRIMARY KEY,
    ProjectID INT FOREIGN KEY REFERENCES dbo.tblProject(ProjectID),
    HubID VARCHAR(100),
    ACCProjectID VARCHAR(100),
    SyncDate DATETIME2 DEFAULT GETDATE(),
    SyncType VARCHAR(50), -- 'Full', 'Issues', 'Users', 'Files'
    ItemsProcessed INT,
    Status VARCHAR(50), -- 'Success', 'Partial', 'Failed'
    ErrorMessage NVARCHAR(MAX),
    SyncedBy VARCHAR(100)
);

-- ACC Project Mapping
CREATE TABLE dbo.tblACCProjectMapping (
    MappingID INT IDENTITY(1,1) PRIMARY KEY,
    ProjectID INT FOREIGN KEY REFERENCES dbo.tblProject(ProjectID),
    HubID VARCHAR(100),
    ACCProjectID VARCHAR(100),
    ACCProjectName NVARCHAR(255),
    LastSync DATETIME2,
    UNIQUE(ProjectID, HubID, ACCProjectID)
);

-- ACC Model Files
CREATE TABLE dbo.tblACCModelFiles (
    FileID INT IDENTITY(1,1) PRIMARY KEY,
    ProjectID INT FOREIGN KEY REFERENCES dbo.tblProject(ProjectID),
    ACCFileID VARCHAR(100),
    FileName NVARCHAR(255),
    FileExtension VARCHAR(10),
    FilePath NVARCHAR(500),
    Version INT,
    FileSize BIGINT,
    LastModified DATETIME2,
    CreatedDate DATETIME2,
    LastSync DATETIME2 DEFAULT GETDATE()
);

-- ACC Users (separate from internal users)
CREATE TABLE dbo.tblACCUsers (
    ACCUserID INT IDENTITY(1,1) PRIMARY KEY,
    ProjectID INT FOREIGN KEY REFERENCES dbo.tblProject(ProjectID),
    ExternalUserID VARCHAR(100), -- APS user ID
    UserName NVARCHAR(255),
    Email NVARCHAR(255),
    Role NVARCHAR(100),
    Company NVARCHAR(255),
    Status VARCHAR(50),
    LastSync DATETIME2 DEFAULT GETDATE()
);
```

#### 5.2 Backend Sync Service

Create `services/acc_sync_service.py`:

```python
from database import get_db_connection
from config import Config
import logging

logger = logging.getLogger(__name__)

class ACCSyncService:
    """Service for syncing ACC data to local database."""
    
    @staticmethod
    def link_project(project_id: int, hub_id: str, acc_project_id: str, acc_project_name: str):
        """Link internal project to ACC project."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                MERGE INTO dbo.tblACCProjectMapping AS target
                USING (SELECT ? AS ProjectID, ? AS HubID, ? AS ACCProjectID, ? AS ACCProjectName) AS source
                ON target.ProjectID = source.ProjectID AND target.HubID = source.HubID AND target.ACCProjectID = source.ACCProjectID
                WHEN MATCHED THEN
                    UPDATE SET ACCProjectName = source.ACCProjectName, LastSync = GETDATE()
                WHEN NOT MATCHED THEN
                    INSERT (ProjectID, HubID, ACCProjectID, ACCProjectName, LastSync)
                    VALUES (source.ProjectID, source.HubID, source.ACCProjectID, source.ACCProjectName, GETDATE());
            """, project_id, hub_id, acc_project_id, acc_project_name)
            conn.commit()
            
    @staticmethod
    def sync_model_files(project_id: int, files_data: list):
        """Sync model files to database."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for file in files_data:
                cursor.execute("""
                    MERGE INTO dbo.tblACCModelFiles AS target
                    USING (SELECT ? AS ProjectID, ? AS ACCFileID) AS source
                    ON target.ProjectID = source.ProjectID AND target.ACCFileID = source.ACCFileID
                    WHEN MATCHED THEN
                        UPDATE SET 
                            FileName = ?,
                            FileExtension = ?,
                            Version = ?,
                            FileSize = ?,
                            LastModified = ?,
                            LastSync = GETDATE()
                    WHEN NOT MATCHED THEN
                        INSERT (ProjectID, ACCFileID, FileName, FileExtension, Version, FileSize, LastModified, CreatedDate, LastSync)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE());
                """, 
                project_id, file['id'],
                file['name'], file.get('extension'), file.get('version'), 
                file.get('size'), file.get('modified'),
                project_id, file['id'], file['name'], file.get('extension'), 
                file.get('version'), file.get('size'), file.get('modified'), file.get('created'))
            conn.commit()
            
    @staticmethod
    def sync_users(project_id: int, users_data: list):
        """Sync project users to database."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for user in users_data:
                cursor.execute("""
                    MERGE INTO dbo.tblACCUsers AS target
                    USING (SELECT ? AS ProjectID, ? AS ExternalUserID) AS source
                    ON target.ProjectID = source.ProjectID AND target.ExternalUserID = source.ExternalUserID
                    WHEN MATCHED THEN
                        UPDATE SET 
                            UserName = ?,
                            Email = ?,
                            Role = ?,
                            Company = ?,
                            Status = ?,
                            LastSync = GETDATE()
                    WHEN NOT MATCHED THEN
                        INSERT (ProjectID, ExternalUserID, UserName, Email, Role, Company, Status, LastSync)
                        VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE());
                """, 
                project_id, user['id'],
                user['name'], user.get('email'), user.get('role'), 
                user.get('company'), user.get('status'),
                project_id, user['id'], user['name'], user.get('email'), 
                user.get('role'), user.get('company'), user.get('status'))
            conn.commit()
            
    @staticmethod
    def log_sync(project_id: int, sync_type: str, items_processed: int, status: str, error_message: str = None, synced_by: str = None):
        """Log sync activity."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dbo.tblACCSyncHistory (ProjectID, SyncType, ItemsProcessed, Status, ErrorMessage, SyncedBy)
                VALUES (?, ?, ?, ?, ?, ?)
            """, project_id, sync_type, items_processed, status, error_message, synced_by)
            conn.commit()
```

## Prerequisites & Configuration

### 1. APS Auth Demo Service Setup

The `services/aps-auth-demo` service must be running and properly configured:

**Required Environment Variables**:
```bash
CLIENT_ID=your_autodesk_client_id
CLIENT_SECRET=your_autodesk_client_secret
CALLBACK_URL=http://localhost:3000/callback
PORT=3000
```

**Start Service**:
```bash
cd services/aps-auth-demo
npm install
node index.js
```

### 2. Backend Configuration

**File**: `config.py`

Add these configuration variables:
```python
# APS Auth Service Configuration
APS_AUTH_SERVICE_URL = os.getenv('APS_AUTH_SERVICE_URL', 'http://localhost:3000')
APS_AUTH_LOGIN_PATH = os.getenv('APS_AUTH_LOGIN_PATH', '/login-pkce')
```

### 3. Frontend Configuration

**File**: `frontend/src/api/client.ts`

Ensure the API client points to the backend:
```typescript
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
  timeout: 30000,
});
```

## Usage Workflow

### Step-by-Step User Flow

1. **Authenticate**
   - User clicks "Authenticate" button
   - Opens Autodesk login in new window
   - User signs in with Autodesk credentials
   - Token is stored in aps-auth-demo service

2. **Select Hub**
   - User clicks "Load Hubs" button
   - System retrieves list of accessible hubs
   - User selects a hub from the list

3. **Select Project**
   - System automatically loads projects for selected hub
   - User selects a project from the list

4. **View Project Details** (NEW)
   - System loads project metadata
   - Displays folder count, file count, model folders
   - Shows project status and dates

5. **Explore Model Files** (NEW)
   - Navigate folder structure
   - Filter by file type (RVT, IFC, DWG, etc.)
   - View file versions and metadata

6. **Review Issues** (NEW)
   - List all project issues
   - Filter by status, priority, assignee
   - View issue details and custom attributes

7. **View Team Members** (NEW)
   - List all project users
   - See roles and contact information
   - Identify project stakeholders

8. **Link to Internal Project** (NEW - Optional)
   - Select existing internal project
   - Create mapping between ACC and internal project
   - Enable data sync to local database

## Common Model File Extensions

The system identifies these as "model files" for BIM workflows:

- `.rvt` - Revit models
- `.rfa` - Revit families
- `.ifc` - IFC models (open BIM standard)
- `.dwg` - AutoCAD drawings
- `.dwf` - Design Web Format
- `.nwd` - Navisworks models
- `.nwc` - Navisworks cache
- `.skp` - SketchUp
- `.3dm` - Rhino 3D
- `.dgn` - MicroStation

## API Response Examples

### Project Details Response
```json
{
  "success": true,
  "authMethod": "User Token (3-legged OAuth)",
  "projectInfo": {
    "id": "b.xxxxxxxxxxxx",
    "name": "Project Name",
    "status": "active",
    "created": "2023-01-15T10:30:00Z",
    "updated": "2024-01-05T14:20:00Z",
    "totalTopLevelFolders": 8,
    "totalFiles": 342,
    "modelFolders": [
      {
        "name": "Project Files",
        "fileCount": 156,
        "lastModified": "2024-01-05T14:20:00Z"
      }
    ]
  },
  "folders": [ ... ]
}
```

### Model Files Response
```json
{
  "success": true,
  "projectId": "b.xxxxxxxxxxxx",
  "totalFiles": 342,
  "modelFiles": [
    {
      "id": "urn:adsk.wipprod:fs.file:xxx",
      "name": "Architectural Model.rvt",
      "extension": "rvt",
      "size": 52428800,
      "version": 12,
      "modified": "2024-01-05T14:20:00Z",
      "folder": "Project Files"
    }
  ]
}
```

### Issues Response
```json
{
  "success": true,
  "projectId": "b.xxxxxxxxxxxx",
  "totalIssues": 87,
  "issues": [
    {
      "id": "issue-xxx",
      "title": "Clash between MEP and Structure",
      "status": "open",
      "priority": "high",
      "assigned_to": "john.doe@example.com",
      "created": "2024-01-03T09:15:00Z",
      "custom_attributes": {
        "discipline": "MEP",
        "location": "Level 2 - Grid C4"
      }
    }
  ]
}
```

### Users Response
```json
{
  "success": true,
  "projectId": "b.xxxxxxxxxxxx",
  "userCount": 24,
  "users": [
    {
      "id": "user-xxx",
      "name": "John Doe",
      "email": "john.doe@example.com",
      "role": "Project Admin",
      "company": "ABC Architecture",
      "status": "active"
    }
  ]
}
```

## Error Handling

### Authentication Errors
- **No token**: User must authenticate first
- **Expired token**: Redirect to login
- **Insufficient permissions**: Show error with required permissions

### API Errors
- **403 Forbidden**: User doesn't have access to resource
- **404 Not Found**: Hub/Project doesn't exist or not accessible
- **429 Rate Limit**: Too many requests, implement retry with backoff
- **500 Server Error**: APS service issue, show error message

### Fallback Strategy
The system automatically falls back to app-level (2-legged) tokens when user tokens fail. This provides limited data but ensures some functionality remains available.

## Security Considerations

1. **Token Storage**: Tokens are stored server-side in aps-auth-demo service
2. **CORS**: Properly configured for frontend-backend communication
3. **HTTPS**: Use HTTPS in production for all API calls
4. **Scopes**: Request only necessary OAuth scopes:
   - `data:read` - Read project data
   - `data:write` - Modify project data (if needed)
   - `account:read` - Read user profile
   - `viewables:read` - View models (if needed)

## Testing Strategy

1. **Unit Tests**: Test individual API endpoints
2. **Integration Tests**: Test full sync workflow
3. **Manual Testing**: Verify UI interactions
4. **Performance Tests**: Test with large projects (1000+ files)

## Troubleshooting

### Issue: "No hubs returned"
**Solution**: Verify authentication, check if user has access to any hubs

### Issue: "Failed to fetch projects"
**Solution**: Verify hub ID is correct, check user permissions

### Issue: "Issues API returns 404"
**Solution**: Issues module may not be enabled in ACC project

### Issue: "Users API returns 403"
**Solution**: User may not have admin rights to view project users

## Next Steps

1. ✅ Read this guide thoroughly
2. ⬜ Implement Phase 1 backend endpoints
3. ⬜ Add Phase 2 TypeScript types
4. ⬜ Implement Phase 3 API client methods
5. ⬜ Enhance Phase 4 UI components
6. ⬜ (Optional) Implement Phase 5 data persistence
7. ⬜ Test with real ACC projects
8. ⬜ Document any issues or improvements

## Additional Resources

- [Autodesk Platform Services Documentation](https://aps.autodesk.com/en/docs/)
- [ACC API Reference](https://aps.autodesk.com/en/docs/acc/v1/overview/)
- [Data Management API](https://aps.autodesk.com/en/docs/data/v2/overview/)
- [OAuth Authentication](https://aps.autodesk.com/en/docs/oauth/v2/overview/)
