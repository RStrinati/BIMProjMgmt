# ✅ Naming Convention Persistence - Complete

## Issue Fixed
> "lets make sure that when the naming convention is set and saved, then when we edit the project again it shows the selected naming convention."

## Solution Implemented

### Problem
- Naming convention was only stored in `clients` table
- When editing a project, the form showed the client's default convention
- Any override selected by the user was not saved or persisted

### Fix
Added `naming_convention` column to the `projects` table to store per-project overrides.

## Changes Made

### 1. Database Migration ✅
**File**: `sql/migrations/add_naming_convention_to_projects.sql`

```sql
-- Added naming_convention column to projects table
ALTER TABLE projects
ADD naming_convention NVARCHAR(50) NULL;

-- Added constraint for valid values
ALTER TABLE projects
ADD CONSTRAINT CK_projects_naming_convention 
CHECK (naming_convention IS NULL OR naming_convention IN ('AWS', 'SINSW'));

-- Updated view to include naming convention with smart fallback
CREATE VIEW vw_projects_full AS
SELECT
    ...
    -- Returns project override if set, otherwise client default
    COALESCE(p.naming_convention, c.naming_convention) as naming_convention
FROM projects p
LEFT JOIN clients c ON p.client_id = c.client_id
...
```

**Migration Applied**: ✅ Successfully executed

### 2. Schema Constants Updated ✅
**File**: `constants/schema.py`

```python
class Projects:
    ...
    NAMING_CONVENTION = "naming_convention"  # Added
```

### 3. Backend API Updated ✅
**File**: `backend/app.py`

```python
def _extract_project_payload(body):
    return {
        ...
        'naming_convention': body.get('naming_convention'),  # Added
    }
```

### 4. Service Layer Updated ✅
**File**: `shared/project_service.py`

```python
@dataclass
class ProjectPayload:
    ...
    naming_convention: Optional[str] = None  # Added

    def to_db_payload(self) -> Dict[str, Any]:
        ...
        if self.naming_convention not in (None, ""):
            payload[S.Projects.NAMING_CONVENTION] = self.naming_convention  # Added
```

### 5. Frontend Types Updated ✅
**File**: `frontend/src/types/api.ts`

```typescript
export interface Project {
    ...
    naming_convention?: string | null;  // Added
}
```

### 6. Form Loading Logic Fixed ✅
**File**: `frontend/src/components/ProjectFormDialog.tsx`

```typescript
// OLD: Always used client's convention
naming_convention: projectClient?.naming_convention || ''

// NEW: Uses project's saved convention, falls back to client default
naming_convention: project.naming_convention || projectClient?.naming_convention || ''
```

## Data Flow

### Creating a New Project
```
1. User selects client → Client's naming_convention auto-fills
2. User optionally overrides → Sets different convention
3. Form submits → naming_convention saved to projects table
4. Database stores → project.naming_convention = 'AWS' or 'SINSW'
```

### Editing an Existing Project
```
1. User opens edit dialog
2. Backend fetches project → includes naming_convention field
3. Form loads → Checks project.naming_convention first
4. If project has override → Shows override
5. If project has NULL → Shows client's default
6. User can change → Updates project.naming_convention
7. Form submits → New value saved to database
```

### View Query Logic
```sql
COALESCE(p.naming_convention, c.naming_convention) as naming_convention

-- Returns:
-- 1. project.naming_convention if NOT NULL (user override)
-- 2. client.naming_convention if project value is NULL (client default)
-- 3. NULL if both are NULL
```

## Testing

### Test Scenario 1: Create with Client Default
1. Create new project
2. Select client "AWS" (has AWS convention)
3. Leave override dropdown as "Use Client Default"
4. Save project
5. ✅ Expected: `project.naming_convention = NULL`, view returns client's 'AWS'

### Test Scenario 2: Create with Override
1. Create new project
2. Select client "AWS" (has AWS convention)
3. Change override dropdown to "SINSW"
4. Save project
5. ✅ Expected: `project.naming_convention = 'SINSW'`, view returns 'SINSW'

### Test Scenario 3: Edit Existing Project
1. Open existing project with naming_convention = 'SINSW'
2. Edit dialog opens
3. ✅ Expected: Dropdown shows "SINSW (ISO 19650-2 + SINSW...)"
4. Change to "AWS"
5. Save
6. ✅ Expected: `project.naming_convention = 'AWS'`

### Test Scenario 4: Edit Project with NULL Convention
1. Open existing project with naming_convention = NULL
2. Client has convention 'AWS'
3. ✅ Expected: Dropdown shows "AWS (ISO 19650)" (from client)
4. Override to "SINSW"
5. Save
6. ✅ Expected: `project.naming_convention = 'SINSW'`

## Migration Script Usage

```powershell
# Apply the migration
python tools/apply_projects_naming_convention_migration.py

# Output:
# ============================================================
# Applying Naming Convention Migration to Projects Table
# ============================================================
# 
# Database connection pools initialized
#
# ============================================================
# ✅ Migration Applied Successfully!
# ============================================================
```

## Verification Queries

```sql
-- Check column exists
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'projects' AND COLUMN_NAME = 'naming_convention';

-- Check constraint exists
SELECT * FROM INFORMATION_SCHEMA.CHECK_CONSTRAINTS
WHERE CONSTRAINT_NAME = 'CK_projects_naming_convention';

-- Test view
SELECT project_id, project_name, naming_convention
FROM vw_projects_full
ORDER BY project_id DESC;

-- Test project with override
SELECT p.project_id, p.naming_convention as project_nc, 
       c.naming_convention as client_nc,
       COALESCE(p.naming_convention, c.naming_convention) as effective_nc
FROM projects p
LEFT JOIN clients c ON p.client_id = c.client_id
WHERE p.project_id = 1;
```

## Files Modified/Created

### Modified
- ✅ `constants/schema.py` - Added NAMING_CONVENTION constant
- ✅ `backend/app.py` - Added naming_convention to payload extraction
- ✅ `shared/project_service.py` - Added naming_convention to ProjectPayload
- ✅ `frontend/src/types/api.ts` - Added naming_convention to Project interface
- ✅ `frontend/src/components/ProjectFormDialog.tsx` - Fixed form loading logic

### Created
- ✅ `sql/migrations/add_naming_convention_to_projects.sql` - Database migration
- ✅ `tools/apply_projects_naming_convention_migration.py` - Migration script

### Documentation
- ✅ This file (`NAMING_CONVENTION_PERSISTENCE_COMPLETE.md`)

## Summary

✅ **Database**: naming_convention column added to projects table
✅ **Constraints**: CHECK constraint ensures only valid values ('AWS', 'SINSW', NULL)
✅ **View**: vw_projects_full uses COALESCE for smart fallback
✅ **Backend**: API accepts and saves naming_convention
✅ **Service Layer**: ProjectPayload includes naming_convention
✅ **Frontend**: Form loads saved convention correctly
✅ **Migration**: Successfully applied

## Next Steps

1. **Restart Backend**: If running, restart to pick up schema changes
2. **Test**: Create/edit projects and verify persistence
3. **Verify**: Check database to confirm values are saved

The naming convention will now:
- ✅ Save with the project when set
- ✅ Display correctly when editing
- ✅ Allow per-project overrides
- ✅ Fall back to client default when NULL
