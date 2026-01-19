# Quality Register Add Row - Minimal Architecture (Tightened)

**Date**: January 19, 2026  
**Objective**: Inline-first draft row creation with minimum state complexity  
**Risk**: Low (no backend changes, cache-only state management)

---

## 1. State Management Architecture Decision

### ❌ REJECTED: Full Hybrid (Cache + Local State)
**Why rejected**: Introduces dual source of truth, requires constant sync between `draftById` state and cache.

### ✅ CHOSEN: Cache-Only with Inline Edit Markers

**Architecture**:
```typescript
// Single source of truth
queryClient.cache: ['quality-register-phase1d', projectId]
  └─ rows: QualityRegisterRow[]  // Includes drafts (id < 0) and saved rows (id > 0)

// Minimal edit state (already exists)
editingRowId: number | null  // Which row is being edited
```

**Draft Identification**: 
- Draft rows have `expected_model_id < 0` (negative temp IDs)
- No separate draft state needed
- Edit state is tracked by existing `editingRowId` + `draftById` (KEEPS existing pattern, not removed)
- **Field name**: Always use `row.expected_model_id` (not `row.id`)
- **Draft check**: `const isDraftRow = (rowId: number) => rowId < 0;`

**Justification for Keeping `draftById`**:
The existing code already uses `draftById` to track **in-progress edits** (not just drafts). This is necessary because:
1. **Controlled inputs**: React TextFields need controlled values, not null/undefined
2. **Partial edits**: User types partial text before committing
3. **Validation state**: Inline error messages per field
4. **Already exists**: Removing it would require rewriting the entire edit system

**Strict Boundaries**:
- **Cache**: Authoritative for row existence and saved field values
- **draftById**: Ephemeral edit buffer, cleared on save/cancel
- **Flow**: Cache row → Edit mode → draftById buffer → Save → Cache update → Clear buffer

**Render Rule** (enforced in all editable cells):
```typescript
const value = draftById[rowId]?.[field] ?? row[field] ?? '';
```

**Save Rule** (source of truth while editing):
```typescript
const payload = draftById[rowId]; // NOT merged with row data
```

**Critical: ID Remapping** (if temp row replaced while still editing):
```typescript
// After POST success, always exit edit mode to avoid remapping
setEditingRowId(null);
// If you ever keep editing after ID change, must remap:
// draftById[newId] = draftById[tempId];
// delete draftById[tempId];
// setEditingRowId(newId);
// ⚠️ We avoid this complexity by ALWAYS exiting edit mode on save.
```

This is **minimal hybrid**, not dual-source-of-truth. The draft row shell lives in cache; the edit buffer lives in local state temporarily.

---

## 2. API Call Strategy (Single-Call Preferred)

### Backend Contract Analysis

**CREATE Endpoint**: `POST /api/projects/<project_id>/quality/expected-models`

**Currently Accepts**:
```python
# backend/app.py:5735-5742
manager.add_expected_model(
    project_id=project_id,
    expected_model_key=data.get('expected_model_key', 'UNNAMED-MODEL'),
    display_name=data.get('display_name'),          # Optional
    discipline=data.get('discipline'),              # Optional
    company_id=data.get('company_id'),              # Optional (INT, not string)
    is_required=data.get('is_required', True)
)
```

**Phase 1D Register Fields** (sql/migrations/add_quality_register_fields.sql):
- `abv` NVARCHAR(10) - NOT in create endpoint
- `registered_model_name` NVARCHAR(255) - NOT in create endpoint (only `display_name`)
- `company` NVARCHAR(255) - NOT in create endpoint (only `company_id` INT)
- `description` NVARCHAR(MAX) - NOT in create endpoint
- `bim_contact` NVARCHAR(255) - NOT in create endpoint
- `notes` NVARCHAR(MAX) - NOT in create endpoint

**UPDATE Endpoint**: `PATCH /api/projects/<project_id>/quality/expected-models/<id>`

**Accepts All Fields** (backend/app.py:5927-5936):
```python
field_mapping = {
    'abv': 'abv',
    'registeredModelName': 'registered_model_name',
    'company': 'company',              # String, not ID
    'discipline': 'discipline',
    'description': 'description',
    'bimContact': 'bim_contact',
    'notes': 'notes',
    # ...
}
```

### ❌ CANNOT Use Single-Call

**Proof**: CREATE endpoint does NOT accept `abv`, `registered_model_name`, `company` (string), `description`, `bim_contact`, `notes`.

**Consequence**: MUST use two-call pattern:
1. **POST** with minimal fields (`expected_model_key`, `display_name`)
2. **PATCH** with full register fields (`abv`, `registeredModelName`, `company`, `discipline`, `description`, `bimContact`, `notes`)

### Two-Call Pattern (Minimal)

**Key Generation Utility** (centralized, prevents overflow/collisions):
```typescript
// frontend/src/api/quality.ts or utils/keyGenerator.ts
export const generateModelKey = (abv?: string): string => {
  const prefix = (abv || 'MODEL').slice(0, 10).toUpperCase();
  const timestamp = Date.now().toString(36); // Base36 is shorter
  const random = Math.random().toString(36).slice(2, 6).toUpperCase();
  const key = `${prefix}-${timestamp}-${random}`;
  
  // Enforce NVARCHAR(50) constraint
  return key.slice(0, 50);
};
```

```typescript
// Step 1: Create skeleton row
const createResponse = await apiClient.post(
  `/projects/${projectId}/quality/expected-models`,
  {
    expected_model_key: generateModelKey(draft.abv),
    display_name: draft.registeredModelName || 'New Model'
  }
);
const newId = createResponse.data.expected_model_id;

// Step 2: ALWAYS update with full fields (for consistency)
// POST stores display_name, but table renders registered_model_name
// PATCH syncs registered_model_name with user input
await apiClient.patch(
  `/projects/${projectId}/quality/expected-models/${newId}`,
  {
    abv: draft.abv,
    registeredModelName: draft.registeredModelName, // Sync canonical field
    company: draft.company,
    discipline: draft.discipline,
    description: draft.description,
    bimContact: draft.bimContact,
    notes: draft.notes
  }
);
```

**Error Handling**: If PATCH fails after POST succeeds, row exists in database with incomplete data. This is **acceptable** because:
- User can edit the row again to complete it
- Better than losing the row entirely
- Shows warning: "Row created but some fields not saved. Please edit to retry."

---

## 3. Query Invalidation Rules (Strict)

### ❌ NEVER Invalidate During Edit

**Query Key**: `['quality-register-phase1d', projectId]`

**NEVER invalidate when**:
- User clicks "Add Row" (draft created locally)
- User types in edit fields (buffer update only)
- User saves row (optimistic cache update only)
- User cancels edit (local state clear only)
- Row is in edit mode (`editingRowId !== null`)

**Rationale**: Invalidation triggers refetch, which replaces optimistically-updated rows and causes flicker.

### ✅ Invalidate ONLY On External Changes

**Allowed conditions**:
1. **Side panel updates** (user edits in side panel, not inline table)
   ```typescript
   // After side panel save
   queryClient.invalidateQueries({ queryKey: ['quality-register-phase1d', projectId] });
   ```

2. **Data imports** (ACC, Revizto, health data)
   ```typescript
   // After import completes
   queryClient.invalidateQueries({ queryKey: ['quality-register-phase1d', projectId] });
   ```

3. **Initial page load / manual refresh**
   ```typescript
   // User clicks browser refresh or navigates back to tab
   // React Query automatically refetches
   ```

4. **Background refetch (with user awareness)**
   ```typescript
   // Only if user is NOT editing (editingRowId === null)
   // Use refetchQueries (not invalidateQueries) with guard
   if (editingRowId === null) {
     queryClient.refetchQueries({ 
       queryKey: ['quality-register-phase1d', projectId],
       type: 'active'  // Only refetch active queries
     });
   }
   ```

### Invalidation Guard (Enforcement)

**Safe invalidation wrapper** (use everywhere):
```typescript
// frontend/src/pages/QualityTab.tsx
const safeInvalidateQualityRegister = () => {
  // QUALITY_REGISTER_SAFE_INVALIDATE_ONLY
  if (editingRowId !== null) {
    console.warn('[QualityTab] Skipping invalidate: row is being edited', { editingRowId });
    return;
  }
  queryClient.invalidateQueries({ queryKey: ['quality-register-phase1d', projectId] });
};
```

**Safe refetch wrapper** (for explicit refetch without marking stale):
```typescript
const safeRefetchQualityRegister = () => {
  if (editingRowId !== null) {
    console.warn('[QualityTab] Skipping refetch: row is being edited', { editingRowId });
    return;
  }
  queryClient.refetchQueries({ 
    queryKey: ['quality-register-phase1d', projectId],
    type: 'active'
  });
};
```

**Apply to**:
- Side panel save handler
- Import completion handler
- Bulk operations
- Any external trigger that needs to update the table

---

## 4. Required Fields for Validation

### Table Column Constraints

**From SQL schema** (ExpectedModels table):
- `expected_model_id` INT IDENTITY - Server-generated (PRIMARY KEY)
- `project_id` INT NOT NULL - Server-provided
- `expected_model_key` NVARCHAR(50) NOT NULL UNIQUE - **REQUIRED in DB**
- All Phase 1D fields (`abv`, `registered_model_name`, etc.) - **NULL allowed in DB**

### UX-Level Required Fields (Not DB Constraints)

**For draft commit, require**:
1. **`registered_model_name`** (mapped to `modelName` in UI)
   - Column: `registered_model_name` NVARCHAR(255) NULL
   - Why required: Every model must have a human-readable name
   - Validation: Must not be empty or whitespace-only

2. **`expected_model_key`** (generated from `abv` or fallback)
   - Column: `expected_model_key` NVARCHAR(50) NOT NULL
   - Why required: Database constraint (UNIQUE per project)
   - Generation strategy: `${abv || 'MODEL'}-${timestamp}`

**Optional fields** (no validation):
- `abv` - Model abbreviation (used to generate key if present)
- `company` - Company name
- `discipline` - Model discipline (Architecture, Structural, MEP, etc.)
- `description` - Long-form description
- `bim_contact` - Email or name of BIM coordinator
- `notes` - Freeform notes

### Validation Logic (Minimal)

```typescript
const validateDraft = (draft: EditableFields): { valid: boolean; errors: Record<string, string> } => {
  const errors: Record<string, string> = {};
  
  // Only one required field for UX
  if (!draft.registeredModelName?.trim()) {
    errors.registeredModelName = 'Model Name is required';
  }
  
  return {
    valid: Object.keys(errors).length === 0,
    errors
  };
};
```

**Rationale**: Minimal friction. User can add a row with just a name and fill in details later.

---

## 5. Two-Call Failure Handling

### Success Case (Both Calls Succeed)

```typescript
try {
  // Call 1: Create
  const { id } = await apiClient.post('/expected-models', { 
    expected_model_key: generateKey(draft),
    display_name: draft.registeredModelName 
  });
  
  // Call 2: Update (if any additional fields present)
  if (hasAdditionalFields(draft)) {
    await apiClient.patch(`/expected-models/${id}`, {
      abv: draft.abv,
      company: draft.company,
      // ... other fields
    });
  }
  
  // Success: Replace draft in cache
  replaceDraftWithSavedRow(tempId, id, draft);
  
} catch (error) {
  // Error handling below
}
```

### Failure Case 1: Create Fails

**Scenario**: POST returns 400/500 (e.g., duplicate key, validation error)

**Handling**:
```typescript
catch (error) {
  if (error.response?.status === 400 && error.response.data.error.includes('duplicate')) {
    // Show specific error
    showInlineError(tempId, 'Model key already exists. Try a different name.');
  } else {
    // Generic error
    showInlineError(tempId, `Failed to create: ${error.message}`);
  }
  
  // Keep draft in edit mode for retry
  // Do NOT remove from cache
  // Do NOT clear edit state
}
```

**User Action**: Edit `registeredModelName` or `abv`, click Save again.

### Failure Case 2: Create OK, Update Fails (Partial Success)

**Scenario**: POST succeeds (row created in DB), PATCH fails (network error, timeout, 500)

**Handling**:
```typescript
try {
  const { id } = await apiClient.post('/expected-models', payload);
  
  try {
    await apiClient.patch(`/expected-models/${id}`, fullPayload);
    // Both succeeded
    replaceDraftWithSavedRow(tempId, id, draft);
    
  } catch (patchError) {
    // Create succeeded, update failed
    console.warn('Row created but update failed', { id, error: patchError });
    
    // Still replace draft with new ID (row exists in DB)
    // Map display_name to registered_model_name for consistent rendering
    replaceDraftWithSavedRow(tempId, id, { 
      expected_model_id: id,
      modelName: draft.registeredModelName || 'New Model',  // UI field
      // Map to DB field that table reads (registered_model_name or display_name)
      registeredModelName: draft.registeredModelName,
      abv: null,  // Not saved yet
      company: null,
      discipline: null,
      description: null,
      bimContact: null,
      notes: null,
      mappingStatus: 'UNMAPPED',
      validationOverall: 'UNKNOWN',
      freshnessStatus: 'UNKNOWN',
      needsSync: true  // Flag for partial success
    });
    
    // Show warning toast (not blocking)
    showWarningToast(
      'Row created but some fields not saved. Click the row to edit and retry.',
      { autoClose: 8000 }
    );
    
    // Exit edit mode (row is saved, just incomplete)
    setEditingRowId(null);
    
    // Clear draft buffer
    setDraftById(prev => {
      const { [tempId]: _, ...rest } = prev;
      return rest;
    });
  }
  
} catch (createError) {
  // Create failed: handle as Failure Case 1
}
```

**Rationale**: 
- Row exists in database with partial data
- Better to show incomplete row than lose it
- User can edit row again to complete missing fields
- Non-blocking warning (toast, not alert)

### Failure Case 3: Network Timeout (Unknown State)

**Scenario**: Request times out, unknown if server processed it

**Handling**:
```typescript
catch (error) {
  if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
    showInlineError(
      tempId, 
      'Request timed out. Check your connection and retry. (If you see a duplicate row after refresh, the save succeeded.)'
    );
    
    // Keep draft for retry
    // User can cancel if duplicate appears after refresh
  }
}
```

---

## 6. Test Plan Updates (Two-Call Coverage)

### New Test: Partial Failure (Create OK, Update Fail)

```typescript
test('partial failure: create succeeds but update fails', async ({ page }) => {
  // Mock API: POST succeeds, PATCH fails
  await page.route('**/quality/expected-models**', route => {  // Pattern catches /expected-models and /expected-models/{id}
    const method = route.request().method();
    const url = route.request().url();
    
    if (method === 'POST' && url.endsWith('/expected-models')) {
      route.fulfill({ 
        status: 201, 
        body: JSON.stringify({ expected_model_id: 999 }) 
      });
    } else if (method === 'PATCH' && /\/expected-models\/\d+$/.test(url)) {
      route.fulfill({ 
        status: 500, 
        body: JSON.stringify({ error: 'Database timeout' }) 
      });
    } else {
      route.continue();  // Let other requests pass through
    }
  });
  
  // Add draft
  await page.click('button:has-text("Add row")');
  const draftRow = page.locator('tbody tr').last();
  
  // Fill fields
  await draftRow.locator('td:nth-child(1) input').fill('PARTIAL');
  await draftRow.locator('td:nth-child(2) input').fill('Partial Model');
  await draftRow.locator('td:nth-child(3) input').fill('Acme Corp');
  
  // Save
  await draftRow.locator('button[title*="Save"]').click();
  await page.waitForTimeout(1000);
  
  // Verify row is saved (exits edit mode)
  await expect(draftRow.locator('input')).toHaveCount(0);
  
  // Verify warning toast appears
  await expect(page.locator('text=/not saved|incomplete/i')).toBeVisible();
  
  // Verify Model Name is saved (from POST)
  await expect(draftRow).toContainText('Partial Model');
  
  // Verify company NOT saved (PATCH failed)
  // (May show as empty or previous value)
});
```

### New Test: Retry After Partial Failure

```typescript
test('user can retry update after partial failure', async ({ page }) => {
  // First save: POST ok, PATCH fails
  await page.route('**/quality/expected-models**', route => {
    const method = route.request().method();
    const url = route.request().url();
    
    if (method === 'POST' && url.endsWith('/expected-models')) {
      route.fulfill({ status: 201, body: JSON.stringify({ expected_model_id: 888 }) });
    } else if (method === 'PATCH' && url.endsWith('/888')) {
      // First PATCH fails
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Timeout' }) });
    } else {
      route.continue();
    }
  });
  
  await page.click('button:has-text("Add row")');
  const row = page.locator('tbody tr').last();
  await row.locator('td:nth-child(2) input').fill('Retry Test');
  await row.locator('td:nth-child(3) input').fill('Company A');
  await row.locator('button[title*="Save"]').click();
  await page.waitForTimeout(1000);
  
  // Warning appears
  await expect(page.locator('text=/not saved/i')).toBeVisible();
  
  // Remove route to allow successful retry
  await page.unroute('**/quality/expected-models');
  
  // Edit row again
  await row.locator('td:nth-child(3)').click(); // Enter edit mode
  await page.waitForTimeout(200);
  await row.locator('td:nth-child(3) input').fill('Company B');
  
  // Save again (now PATCH should succeed)
  await row.locator('button[title*="Save"]').click();
  await page.waitForTimeout(500);
  
  // Verify saved
  await expect(row).toContainText('Company B');
  await expect(page.locator('text=/not saved/i')).toHaveCount(0);
});
```

---

## 7. Concrete Guardrails (Add Before Coding)

### Guardrail 1: Centralized Key Generation

**File**: `frontend/src/utils/modelKeyGenerator.ts` (NEW)

```typescript
/**
 * Generate unique model key for ExpectedModels table.
 * Enforces NVARCHAR(50) constraint and prevents collisions.
 */
export const generateModelKey = (abv?: string): string => {
  const prefix = (abv || 'MODEL').slice(0, 10).toUpperCase();
  const timestamp = Date.now().toString(36); // Base36: shorter than decimal
  const random = Math.random().toString(36).slice(2, 6).toUpperCase();
  const key = `${prefix}-${timestamp}-${random}`;
  
  // Enforce NVARCHAR(50) constraint
  if (key.length > 50) {
    return key.slice(0, 50);
  }
  return key;
};

// Example outputs:
// "ARCH-l8k9m3n4-A3F9"  (when abv="ARCH")
// "MODEL-l8k9m3n4-B2K7"  (when abv is empty)
```

**Usage**: Import in `QualityTab.tsx` and use in POST payload.

---

### Guardrail 2: Replace Draft Helper

**File**: `frontend/src/pages/QualityTab.tsx`

```typescript
/**
 * Replace a temp draft row with server-returned row.
 * Updates cache and clears all temp-ID-keyed state.
 * 
 * CRITICAL: Always call this after successful POST, even on partial PATCH failure.
 */
const replaceTempRowId = (
  tempId: number, 
  newId: number, 
  rowData: Partial<QualityRegisterRow>
) => {
  // 1. Update cache: replace temp row with server row
  queryClient.setQueryData<QualityPhase1DRegisterResponse>(
    ['quality-register-phase1d', projectId],
    (old) => {
      if (!old) return old;
      return {
        ...old,
        rows: old.rows.map(row => 
          row.expected_model_id === tempId
            ? { ...row, expected_model_id: newId, ...rowData }
            : row
        )
      };
    }
  );
  
  // 2. Clear draft buffer (temp ID no longer exists)
  setDraftById(prev => {
    const { [tempId]: _, ...rest } = prev;
    return rest;
  });
  
  // 3. Exit edit mode (avoids remapping complexity)
  setEditingRowId(null);
  
  // 4. If selection state exists, update it
  if (selectedModelId === tempId) {
    setSelectedModelId(newId);
  }
};
```

---

### Guardrail 3: Safe Invalidation Wrappers

**File**: `frontend/src/pages/QualityTab.tsx`

```typescript
/**
 * Safe invalidate: Only invalidates if no row is being edited.
 * Use this for external changes (side panel, imports).
 * Tag: QUALITY_REGISTER_SAFE_INVALIDATE_ONLY
 */
const safeInvalidateQualityRegister = () => {
  if (editingRowId !== null) {
    console.warn(
      '[QualityTab] Skipping invalidate: row is being edited',
      { editingRowId, projectId }
    );
    return;
  }
  queryClient.invalidateQueries({ 
    queryKey: ['quality-register-phase1d', projectId] 
  });
};

/**
 * Safe refetch: Only refetches active queries if no row is being edited.
 * Use this for background updates or manual refresh triggers.
 */
const safeRefetchQualityRegister = () => {
  if (editingRowId !== null) {
    console.warn(
      '[QualityTab] Skipping refetch: row is being edited',
      { editingRowId, projectId }
    );
    return;
  }
  queryClient.refetchQueries({ 
    queryKey: ['quality-register-phase1d', projectId],
    type: 'active'
  });
};
```

**Usage**: Replace all `queryClient.invalidateQueries(...)` calls with `safeInvalidateQualityRegister()`.

---

### Guardrail 4: Partial Success Indicator

**UI Enhancement**: Add visual indicator for rows with `needsSync: true`

**File**: `frontend/src/components/quality/QualityRegisterTable.tsx`

```tsx
// In renderEditableCell or row render logic
{row.needsSync && (
  <Tooltip title="Some fields not saved. Edit row to retry.">
    <WarningIcon 
      fontSize="small" 
      color="warning" 
      sx={{ ml: 0.5, verticalAlign: 'middle' }} 
    />
  </Tooltip>
)}
```

**Clear flag on successful full save**:
```typescript
// In handleSaveRow after successful PATCH
queryClient.setQueryData<QualityPhase1DRegisterResponse>(
  ['quality-register-phase1d', projectId],
  (old) => {
    if (!old) return old;
    return {
      ...old,
      rows: old.rows.map(row =>
        row.expected_model_id === rowId
          ? { ...row, ...updatedFields, needsSync: false }
          : row
      )
    };
  }
);
```

---

### Guardrail 5: Draft Row Type (TypeScript)

**File**: `frontend/src/types/api.ts` or `frontend/src/pages/QualityTab.tsx`

```typescript
// Extend existing type with draft marker
export interface QualityPhase1DRow {
  expected_model_id: number;  // Negative for drafts, positive for saved
  abv: string | null;
  modelName: string | null;
  company: string | null;
  discipline: string | null;
  description: string | null;
  bimContact: string | null;
  folderPath: string | null;
  accPresent: boolean;
  accDate: string | null;
  reviztoPresent: boolean;
  reviztoDate: string | null;
  notes: string | null;
  notesUpdatedAt: string | null;
  mappingStatus: string;
  matchedObservedFile: string | null;
  validationOverall: string;
  freshnessStatus: string;
  needsSync?: boolean;  // True if POST ok but PATCH failed
}

// Helper
export const isDraftRow = (rowId: number): boolean => rowId < 0;
```

---

## 8. Revised Commit Checklist (Minimal)

### Commit 1: Add Draft Row Infrastructure + Guardrails
**Files**: 
- `frontend/src/pages/QualityTab.tsx`
- `frontend/src/utils/modelKeyGenerator.ts` (NEW)
- `frontend/src/types/api.ts` (extend type)

**Changes**:
- Add `nextTempId` state: `const [nextTempId, setNextTempId] = useState(-1);`
- Add helper: `const isDraftRow = (rowId: number) => rowId < 0;`
- Add `generateModelKey()` utility (Guardrail 1)
- Add `replaceTempRowId()` helper (Guardrail 2)
- Add `safeInvalidateQualityRegister()` wrapper (Guardrail 3)
- Add `safeRefetchQualityRegister()` wrapper (Guardrail 3)
- Extend `QualityPhase1DRow` type with `needsSync?: boolean` (Guardrail 5)

**Lines**: ~80 additions (includes guardrails)  
**Test**: Build succeeds, no runtime changes yet

---

### Commit 2: Replace Add Row Handler (No API Call)
**Files**: `frontend/src/pages/QualityTab.tsx`
**Changes**:
- Replace `handleAddRow` to create draft in cache (no API call)
- Remove `createModelMutation` declaration (no longer used)
- Update props: `isAddingRow={false}` (always false now)

**Lines**: ~60 lines changed (40 added, 20 removed)  
**Test**: Click "Add row" → Draft appears with yellow background

---

### Commit 3: Update Save Handler (Two-Call Pattern)
**Files**: `frontend/src/pages/QualityTab.tsx`
**Changes**:
- Rewrite `handleSaveRow` to detect drafts: `if (isDraftRow(rowId))`
- Add validation: `if (!draft.registeredModelName?.trim())`
- Use `generateModelKey(draft.abv)` for POST payload
- Add create + ALWAYS update sequence (no conditional PATCH)
- Add partial failure handling: POST ok, PATCH fail → call `replaceTempRowId()` with `needsSync: true`
- **ALWAYS exit edit mode** on save (success or partial success) to avoid ID remapping

**Lines**: ~150 lines changed  
**Test**: Save draft → Two API calls → Row persists with server ID, no longer in edit mode

---

### Commit 4: Update Cancel/Delete for Drafts
**Files**: `frontend/src/pages/QualityTab.tsx`
**Changes**:
- Update `handleCancelEdit`: Remove draft from cache if `isDraft(rowId)`
- Update `handleDeleteRow`: Skip API call if `isDraft(rowId)`

**Lines**: ~30 lines changed  
**Test**: Cancel draft → Row disappears; Delete draft → No API call

---

### Commit 5: Remove Auto-Invalidation
**Files**: `frontend/src/pages/QualityTab.tsx`
**Changes**:
- Remove `queryClient.invalidateQueries(...)` from `updateModelMutation.onSuccess`
- Add comment: `// Removed invalidation to prevent flicker during edit`

**Lines**: ~3 lines removed, 1 comment added  
**Test**: Save row → No flicker, row remains stable

---

### Commit 6: Add Draft Visual Indicators + Sync Warning
**Files**: `frontend/src/components/quality/QualityRegisterTable.tsx`
**Changes**:
- Update `<TableRow>` sx to check `row.expected_model_id < 0`
- Add yellow background + left border for drafts
- Add warning icon for `row.needsSync === true` (Guardrail 4)
- Add tooltip: "Some fields not saved. Edit row to retry."

**Lines**: ~20 lines changed  
**Test**: Draft has yellow background; Partial-save row has warning icon

---

### Commit 7: Add Inline Validation
**Files**: `frontend/src/components/quality/QualityRegisterTable.tsx`
**Changes**:
- Update `renderEditableCell` to show validation errors
- Add `error` and `helperText` props to TextField
- Check `draft.validationErrors?.[field]`

**Lines**: ~15 lines changed  
**Test**: Save empty draft → Red border, "Model Name is required"

---

### Commit 8: Update API Client (Accept Payload)
**Files**: `frontend/src/api/quality.ts`
**Changes**:
- Update `createEmptyModel` signature to accept payload object
- Remove auto-generation of key/name (caller controls)

**Lines**: ~10 lines changed  
**Test**: TypeScript build succeeds

---

### Commit 9: Add Playwright Tests
**Files**: `frontend/tests/e2e/quality-register-add-row.spec.ts` (NEW)
**Changes**:
- Add 10 test cases (8 from original + 2 for partial failure)
- Include two-call failure scenarios

**Lines**: ~350 lines (new file)  
**Test**: `npm run test:e2e` → All tests pass

---

### Commit 10: Update Existing Test Assertions
**Files**: `frontend/tests/e2e/quality-register-phase1d.spec.ts`
**Changes**:
- Update assertions for draft styling
- Remove expectations for loading state on add

**Lines**: ~5 lines changed  
**Test**: Existing tests pass

---

### Commit 11: Documentation
**Files**: `docs/features/quality-register-add-row-minimal-architecture.md` (this doc)
**Changes**:
- Add architecture decisions
- Document validation rules
- Document two-call error handling

**Lines**: N/A (docs)  
**Test**: Review with team

---

## 8. Deployment Checklist (Simplified)

### Pre-Deployment
- [ ] All 11 commits merged to `master`
- [ ] All Playwright tests passing
- [ ] Manual smoke test (add/save/cancel/delete drafts)
- [ ] Code review approved
- [ ] No console errors in dev build

### Deployment
- [ ] Deploy to dev → Test 30 minutes
- [ ] Deploy to staging → QA team sign-off
- [ ] Deploy to production → Monitor for 24 hours

### Rollback Trigger
- [ ] If error rate > 2% on create endpoint
- [ ] If user reports data loss
- [ ] If flicker returns (cache invalidation bug)

**Rollback**: `git revert HEAD~11..HEAD` + hotfix deploy

---

## 9. Risk Summary

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| POST fails after multiple retries | Low | Medium | Show clear error, keep draft for retry |
| POST succeeds, PATCH fails | Medium | Low | Row saved with partial data, show warning |
| User loses draft on refresh | High (by design) | Low | Accept as tradeoff; future: localStorage |
| Flicker returns from side panel | Low | Low | Guard invalidate calls with `editingRowId` check |
| Two-call latency noticeable | Low | Low | Acceptable for UX simplicity |

**Acceptance**: All risks are acceptable for Phase 1D. Future enhancements can address if needed.

---

## 10. Success Metrics

**Measure after 1 week**:
- Draft creation rate (clicks on "Add row")
- Draft commit rate (% of drafts saved vs canceled)
- Average time from draft create to save
- Error rate on create endpoint (target: <1%)
- User complaints about data loss (target: 0)

**Expected improvements**:
- Faster perceived speed (no API wait for draft)
- Fewer user complaints about flicker
- Higher draft commit rate (easier workflow)

---

## 11. Pre-Coding Checklist (Do This First)

**Critical verifications before writing code:**

### ✅ 1. Confirm Row Shape Field Name
**Question**: Is "Model Name" column reading `registered_model_name` or `display_name`?

**Action**: Check `frontend/src/components/quality/QualityRegisterTable.tsx` and `backend/app.py` GET endpoint.

**Expected**: Table renders `row.modelName` which maps to DB column `registered_model_name`.

**Impact**: If table reads `display_name` but we only update `registered_model_name` via PATCH, we'll have blank cells after partial failure.

---

### ✅ 2. Confirm React Query Version
**Question**: Which React Query version is in use? Does it support `refetchQueries({ type: 'active' })`?

**Action**: Check `frontend/package.json` → `@tanstack/react-query` version.

**Expected**: v4.x or v5.x (both support `type: 'active'`).

**Impact**: If using v3, use `{ active: true }` instead of `{ type: 'active' }`.

---

### ✅ 3. Decide: Always Exit Edit Mode After Save
**Question**: Should we keep the row in edit mode after POST+PATCH success?

**Decision**: **NO. Always exit edit mode** to avoid ID remapping complexity.

**Rationale**: Temp ID -1 becomes server ID 999; keeping edit mode requires remapping `editingRowId` and `draftById`. Exiting is simpler and aligns with "save commits the change" UX.

---

### ✅ 4. Decide: Always Call PATCH After POST
**Question**: Should PATCH be conditional (only if additional fields present) or always called?

**Decision**: **Always call PATCH** for consistency.

**Rationale**: Simplifies logic, ensures `registered_model_name` is synced even if user only enters Model Name. Predictable behavior is better than optimization.

---

### ✅ 5. Update Test Route Matchers
**Question**: Do Playwright route patterns catch both `/expected-models` (POST) and `/expected-models/{id}` (PATCH)?

**Action**: Use `**/quality/expected-models**` (double asterisk) to match both.

**Example**:
```typescript
await page.route('**/quality/expected-models**', route => {
  const method = route.request().method();
  const url = route.request().url();
  if (method === 'POST' && url.endsWith('/expected-models')) { /* ... */ }
  else if (method === 'PATCH' && /\/expected-models\/\d+$/.test(url)) { /* ... */ }
  else { route.continue(); }
});
```

---

## 12. Tightened Acceptance Criteria

**Wording aligned with implementation decisions:**

1. ✅ "Multiple rapid adds create multiple draft rows (identified by `expected_model_id < 0`); only one row is edited at a time (`editingRowId`)."

2. ✅ "Save on a draft performs POST then PATCH (always, not conditional); if PATCH fails, row is saved with `needsSync: true` flag and warning icon."

3. ✅ "Save always exits edit mode (no ID remapping needed); user can edit again to complete missing fields."

4. ✅ "Invalidation only occurs on external changes (side panel, imports) and is guarded by `editingRowId === null` check."

5. ✅ "Draft rows have yellow background + orange left border; partial-save rows have warning icon with tooltip."

6. ✅ "Model Name (`registered_model_name`) is the only UX-required field; all others optional."

7. ✅ "Model key (`expected_model_key`) is auto-generated via `generateModelKey()` with collision prevention and 50-char limit."

---

**End of Minimal Architecture**  
**Total Commits**: 11 (down from 13)  
**Total Lines Changed**: ~750 (includes guardrails + error handling)  
**Backend Changes**: 0 (no API modifications needed)  
**State Complexity**: Minimal (cache + existing edit state, no new patterns)  
**Pre-Coding Items**: 5 critical verifications (all answered above)
