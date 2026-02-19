# Master Users List Feature

**Status**: Active (February 2026)  
**Last Updated**: February 13, 2026

This feature provides a unified, filterable view of all users from ACC (Autodesk Construction Cloud) and Revizto, normalized by email and enriched with project-specific metadata.

---

## Overview

The **Master Users List** is a central hub for:
- Viewing all users across ACC and Revizto platforms
- Consolidating duplicate users (same email across sources) into a single record
- Managing user properties like BIM meeting attendance, watcher status, and assignee eligibility
- Filtering and customizing column layout for different roles and workflows
- Refreshing Revizto license member data on-demand

### Key Use Cases
1. **PM User Assignment** — Find and assign project users to tasks, deliverables, and reviews
2. **License Tracking** — Identify which users have valid Revizto licenses
3. **Attendance Management** — Track who's invited to / attending BIM meetings
4. **Quality Control** — Monitor user activity (last active timestamps) across platforms

---

## Architecture

### Data Model

#### `master_users` Table
Stores the **normalized user identity** (one record per email).

| Column | Type | Purpose |
|--------|------|---------|
| `master_user_id` | INT (PK) | Unique user identifier |
| `email_normalized` | NVARCHAR(255) (UQ) | Normalized email (lowercase) |
| `display_name` | NVARCHAR(255) | Combined display name |
| `company` | NVARCHAR(255) | Consolidated company name |
| `status` | NVARCHAR(64) | User status (active, inactive, archived) |
| `last_active_at` | DATETIME2 | Most recent platform activity |
| `created_at` | DATETIME2 | Record creation timestamp |
| `updated_at` | DATETIME2 | Last update timestamp |

#### `master_user_identities` Table
Stores **one record per source** (e.g., ACC user +  separate Revizto user for same email).

| Column | Type | Purpose |
|--------|------|---------|
| `master_user_id` | INT (FK) | Link to consolidated master record |
| `source_system` | NVARCHAR(32) | 'ACC', 'Revizto', or other |
| `source_user_id` | NVARCHAR(100) | Platform-native user ID |
| `email_normalized` | NVARCHAR(255) | Email from this source |
| `name` | NVARCHAR(255) | Name from this source |
| `company` | NVARCHAR(255) | Company from this source |
| `role` | NVARCHAR(255) | Role/position from this source |
| `status` | NVARCHAR(64) | User status in this source |
| `last_active_at` | DATETIME2 | Last activity in this source |
| `user_key` | NVARCHAR(160) | Composite key for tracking |

#### `master_user_flags` Table (Optional)
Stores **user-specific flags** set at the project or system level.

| Column | Type | Purpose |
|--------|------|---------|
| `master_user_id` | INT (FK) | User being flagged |
| `invited_to_bim_meetings` | BIT | User is invited to project BIM meetings |
| `is_watcher` | BIT | User watches issues/deliverables |
| `is_assignee` | BIT | User can be assigned tasks/items |
| `created_at` | DATETIME2 | When flag was set |
| `updated_at` | DATETIME2 | Last modification |

### Backend Services

#### `database.py` — Core Functions

- **`get_master_users()`** — Fetch paginated, filtered list of users with counts
  - Returns: List of `MasterUser` objects with all flags and identity consolidation
  - Supports: Filtering by source, company, role, status, license type; search by name/email

- **`update_master_user_flags(master_user_id, ...)`** — Update user properties
  - Sets: `invited_to_bim_meetings`, `is_watcher`, `is_assignee`
  - Enforces: Only project members can be set as assignees (future safety check)

- **`sync_master_users_from_sources()`** — Normalize users from ACC/Revizto sources
  - Process: Merges ACC + Revizto user records by normalized email
  - Creates: `master_users` record per unique email
  - Creates: `master_user_identities` records for each source
  - Runs: On-demand via `/revizto/license-members/sync` endpoint or scheduled batch

### Frontend Components

#### `MasterUsersPage.tsx` (734 lines)
Main page component with:
- **Filtering UI** — 8 filter categories (source, company, role, status, license, BIM meetings, watcher, assignee)
- **Sorted table** — Click column header to sort; multi-field sort supported
- **Column visibility** — User can pin/hide/reorder columns (persisted to localStorage)
- **Inline editing** — Update `invited_to_bim_meetings`, `is_watcher`, `is_assignee` directly in table
- **Sync button** — Trigger Revizto license member refresh on-demand

#### `UserColumnsPopover.tsx` (112 lines)
Popover UI for:
- Displaying all available columns with visibility toggle
- Pinning columns to left side
- Reordering columns via drag-and-drop (optional future enhancement)

#### `UserFieldRegistry.tsx` (227 lines)
Field definition catalog with:
- 16 user fields (name, email, company, role, source, license, last active, etc.)
- Format types: text, number, date, boolean
- Visibility defaults per view type
- Custom render functions (e.g., Chip for source system badge)

#### `useUserViewLayout.ts` (142 lines)
Custom hook for:
- Persisting column visibility/order to localStorage
- Loading/saving user layout preferences
- Computing visible fields list for render

---

## API Endpoints

### `GET /master-users`
Fetch filtered list of unified users.

**Query Parameters**:
```
?source=ACC,Revizto
?company=Acme Fine Construction
?role=Architect
?status=active
?license_type=Professional
?invited_to_bim_meetings=true
?is_watcher=true
?is_assignee=true
&search=john  # name or email substring
&sort=name    # field to sort by
&order=asc    # asc | desc
```

**Response**:
```json
[
  {
    "master_user_id": 123,
    "name": "John Architect",
    "email": "john@acme.example",
    "company": "Acme Fine Construction",
    "role": "Architect",
    "source_system": "ACC",
    "license_type": "Professional",
    "last_active": "2026-02-13T14:30:00Z",
    "last_active_source": "ACC",
    "invited_to_bim_meetings": true,
    "is_watcher": false,
    "is_assignee": true,
    "user_key": "john@acme.example:ACC"
  }
]
```

### `PATCH /master-users/{user_key}`
Update flags for a user.

**Parameters**:
- `{user_key}` — Email (URL encoded) — e.g., `john%40acme.example`

**Request Body**:
```json
{
  "invited_to_bim_meetings": true,
  "is_watcher": false,
  "is_assignee": true
}
```

**Response**: 204 No Content (or error)

### `POST /revizto/license-members/sync`
Sync Revizto license member list and merge with ACC users.

**Purpose**: 
- Fetch latest Revizto user list
- Normalize by email against existing ACC data
- Update `last_active_at` for Revizto users
- Create/update `master_user_identities` records

**Response**:
```json
{
  "status": "success",
  "synced_count": 42,
  "new_users": 5,
  "updated_users": 37,
  "message": "Revizto license members synced"
}
```

---

## User Fields (Complete List)

The following fields are available for display and filtering:

| Field | Format | Filterable | Sortable | Default Visible |
|-------|--------|-----------|----------|-----------------|
| **name** | text | No | Yes | Yes |
| **email** | text | No | Yes | Yes |
| **company** | text | Yes | Yes | Yes |
| **role** | text | Yes | Yes | Yes |
| **source_system** | text | Yes | Yes | Yes |
| **license_type** | text | Yes | Yes | Yes |
| **last_active** | date | No | Yes | Yes |
| **last_active_source** | text | No | Yes | No |
| **invited_to_bim_meetings** | boolean | Yes | Yes | No |
| **is_watcher** | boolean | Yes | Yes | No |
| **is_assignee** | boolean | Yes | Yes | No |
| **status** | text | Yes | Yes | No |
| **phone** | text | No | Yes | No |
| **department** | text | No | Yes | No |
| **title** | text | No | Yes | No |
| **archived** | boolean | No | Yes | No |

---

## Data Flow

1. **Initial Load** — Page calls `GET /master-users` with default filters
   - Backend queries `master_users` joined with `master_user_identities` and flags
   - Returns consolidated list (one row per email, with all source info embedded)

2. **User Applies Filter** — Filter state saved to localStorage
   - Page constructs query params and calls `GET /master-users?company=...&role=...`

3. **Inline Edit** — User toggles checkbox for `invited_to_bim_meetings`
   - Page calls `PATCH /master-users/john%40acme.example` with `{"invited_to_bim_meetings": true}`
   - Backend updates `master_user_flags` table
   - Table refreshes to show new state

4. **Sync Revizto** — User clicks "Refresh Revizto Users"
   - Page calls `POST /revizto/license-members/sync`
   - Backend fetches Revizto API, normalizes, upserts into `master_user_identities`
   - Returns sync summary (5 new, 37 updated)
   - Page re-fetches `GET /master-users` to show fresh data

---

## Common Workflows

### Assign a User to a Project Task

1. Open Master Users page
2. Filter by: `company=Acme`, `role=Architect`
3. Find user (e.g., "John Architect")
4. Check `is_assignee` flag
5. Now when creating a project task, John is available in the assignee dropdown

### Invite Users to BIM Meetings

1. Open Master Users page
2. Filter by: `source_system=ACC`
3. Select users to invite → check `invited_to_bim_meetings`
4. Review calendar/meeting logic to send invitations
5. System tracks who was invited vs. who attended

### Monitor Revizto License Usage

1. Open Master Users page
2. Filter by: `license_type=Professional` OR `license_type=Limited`
3. Sort by `last_active` to find inactive users
4. Consider revoking licenses for inactive users (manual process)

### Find Duplicate Users (Same Email, Different Sources)

1. Open Master Users page
2. Look for users with `source_system` showing both "ACC" and "Revizto"
   - These are already consolidated in `master_users` (same email)
   - Check if role/company differ between sources and needs manual reconciliation

---

## Testing

### Unit Tests
- **`test_master_users_sync()`** — Verify email normalization and identity mapping
- **`test_master_user_flag_updates()`** — Verify flag persistence
- **`test_master_users_filter()`** — Verify filter query generation

### UI Tests (Playwright)
- **Feature**: Master Users list renders all fields
- **Feature**: Filter selections persist across page reloads
- **Feature**: Column visibility toggles and persists
- **Feature**: Inline flag edits update backend
- **Feature**: Revizto sync button triggers refresh

### Manual QA
1. Verify all filters work in combination
2. Verify column reordering persists to localStorage
3. Verify flag updates reflect immediately in table
4. Verify Revizto sync completes and updates counts

---

## Schema Migrations

- **20260213_add_master_user_identities.sql** — Initial creation of `master_users` and `master_user_identities` tables
- **20260206_add_issue_link_anchors.sql** (related) — Added `master_user_identities` join support in issue linking

---

## Configuration

### Environment Variables
None currently required. Master Users feature uses existing database connection credentials.

### Feature Flags
None currently. Feature is always enabled if database tables exist.

---

## Performance Considerations

- **Index on `email_normalized`** — Enables fast lookups during sync and filter operations
- **Index on `last_active_at`** — Supports sorting by activity; helps identify inactive users
- **Lazy-load columns** — React Query paging and memoization reduce re-renders on filter change

---

## Future Enhancements

1. **Bulk Actions** — Select multiple users, apply flags in batch
2. **User Segmentation** — Save/restore named filter combos (e.g., "Active BIM Leads")
3. **Activity Timeline** — Show per-user activity log across ACC/Revizto
4. **Group Management** — Create user groups for project roles (e.g., "Design Review Team")
5. **Batch Email** — Send emails to filtered user set
6. **License Cost Tracking** — Calculate total Revizto license spend by company/role

---

## Support & Troubleshooting

**Q: Why isn't my user appearing in the list?**  
A: User must exist in ACC import or Revizto license member list. Run Revizto sync (`POST /revizto/license-members/sync`) to refresh.

**Q: How often is the list updated?**  
A: ACC data is refreshed on import (manual or scheduled). Revizto data is refreshed on-demand via the sync button or scheduled batch job (configurable).

**Q: Can I bulk-assign users to multiple projects?**  
A: Not yet. You can use filters to find users and update flags one-by-one. Bulk actions are tracked as a future enhancement.

**Q: What happens if the same user exists in ACC with different info than Revizto?**  
A: The `master_users` record uses the most recent update. All source variants are visible in `master_user_identities`, so you can see the differences and manually reconcile if needed.

---

## Related Documentation

- [Data Imports Architecture](DATA_IMPORTS_ARCHITECTURE.md) — Overall import pipeline for ACC/Revizto
- [User Assignment Implementation](../reference/USER_ASSIGNMENT_IMPLEMENTATION.md) — How users are assigned to tasks/items
- [Database Schema](../core/database_schema.md) — Full schema reference including master users tables

---

## Contact & Maintenance

- **Feature Owner**: BIM PM System Team
- **Last Maintenance**: February 13, 2026
- **Reporting Issues**: See [Troubleshooting Guide](../troubleshooting/README.md)
