# Quality Model Register - Add Row Flow Analysis

**Date**: January 19, 2026  
**Feature**: Quality Model Register Table (Phase 1D)  
**Objective**: Simplify add-row operation to support inline editing without forcing side panel

---

## (A) Current Flow Map

### 1. UI Action (User clicks "Add row")

**Location**: [frontend/src/components/quality/QualityRegisterTable.tsx](frontend/src/components/quality/QualityRegisterTable.tsx#L378-L384)

```tsx
<Button
  startIcon={<AddIcon />}
  onClick={onAddRow}
  disabled={isAddingRow || editingRowId !== null}
  size="small"
>
  Add row
</Button>
```

**Flow**: Button click → `onAddRow` prop → Parent handler

---

### 2. Parent Handler (QualityTab)

**Location**: [frontend/src/pages/QualityTab.tsx](frontend/src/pages/QualityTab.tsx#L223-L225)

```tsx
const handleAddRow = () => {
  createModelMutation.mutate();
};
```

**Data ownership**: Triggers mutation, no parameters, no pre-generation of temp row

---

### 3. Create Model Mutation

**Location**: [frontend/src/pages/QualityTab.tsx](frontend/src/pages/QualityTab.tsx#L32-L82)

```tsx
const createModelMutation = useMutation({
  mutationFn: () => qualityApi.createEmptyModel(projectId),
  onSuccess: (data) => {
    // 1. Optimistically add row to React Query cache
    queryClient.setQueryData<QualityPhase1DRegisterResponse>(
      ['quality-register-phase1d', projectId],
      (old) => {
        if (!old) return old;
        return {
          ...old,
          rows: [
            ...old.rows,
            {
              expected_model_id: data.id,
              abv: null,
              modelName: null,
              company: null,
              discipline: null,
              description: null,
              bimContact: null,
              folderPath: null,
              accPresent: false,
              accDate: null,
              reviztoPresent: false,
              reviztoDate: null,
              notes: null,
              notesUpdatedAt: null,
              mappingStatus: 'UNMAPPED',
              matchedObservedFile: null,
              validationOverall: 'UNKNOWN',
              freshnessStatus: 'UNKNOWN'
            }
          ]
        };
      }
    );
    
    // 2. Enter edit mode
    setEditingRowId(data.id);
    
    // 3. Initialize draft state
    setDraftById((prev) => ({
      ...prev,
      [data.id]: {
        abv: '',
        registeredModelName: '',
        company: '',
        discipline: '',
        description: '',
        bimContact: '',
        notes: ''
      }
    }));
    
    // 4. Background invalidate (triggers refetch)
    queryClient.invalidateQueries({ 
      queryKey: ['quality-register-phase1d', projectId] 
    });
  }
});
```

**Data ownership**:
- Mutation state: `isPending`, `isError`, `error`
- Server response: `{ id: number }`
- React Query cache: Full row data (optimistically added)
- Local state: `editingRowId`, `draftById[id]`

---

### 4. API Call

**Location**: [frontend/src/api/quality.ts](frontend/src/api/quality.ts#L237-L251)

```tsx
createEmptyModel: async (projectId: number): Promise<{ id: number }> => {
  // Generate a timestamp-based key for Phase 1D
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const key = `NEW-MODEL-${timestamp}`;
  
  const response = await apiClient.post<{ expected_model_id: number }>(
    `/projects/${projectId}/quality/expected-models`,
    {
      expected_model_key: key,
      display_name: `New Model ${new Date().toLocaleString()}`
    }
  );
  return { id: response.data.expected_model_id };
}
```

**Data ownership**:
- Client-side key generation: `NEW-MODEL-2026-01-19T14-30-22` (timestamp-based)
- Client-side display name: `New Model 1/19/2026, 2:30:22 PM`
- Server creates row and returns `{ expected_model_id: number }`

---

### 5. Backend Endpoint

**Location**: [backend/app.py](backend/app.py#L5725-L5750)

```python
@app.route('/api/projects/<int:project_id>/quality/expected-models', methods=['POST'])
def create_expected_model_endpoint(project_id):
    """Create a new expected model"""
    try:
        from services.expected_model_alias_service import get_expected_model_alias_manager
        
        data = request.get_json() or {}
        manager = get_expected_model_alias_manager()
        
        model_id = manager.add_expected_model(
            project_id=project_id,
            expected_model_key=data.get('expected_model_key', 'UNNAMED-MODEL'),
            display_name=data.get('display_name'),
            discipline=data.get('discipline'),
            company_id=data.get('company_id'),
            is_required=data.get('is_required', True)
        )
        
        if model_id:
            return jsonify({'expected_model_id': model_id}), 201
        else:
            return jsonify({'error': 'Failed to create expected model'}), 500
    
    except Exception as e:
        logging.exception(f"Error creating expected model for project {project_id}")
        return jsonify({'error': str(e)}), 500
```

**Data ownership**:
- Database INSERT into `ExpectedModels` table
- Returns new `expected_model_id`
- No validation of duplicate keys (relies on unique constraint)

---

### 6. Selection & Side Panel Logic

**Location**: [frontend/src/pages/QualityTab.tsx](frontend/src/pages/QualityTab.tsx#L163-L182)

```tsx
const handleRowClick = (row: any) => {
  // Don't open side panel if editing
  if (editingRowId === row.expected_model_id) {
    return;
  }
  
  // Prompt if switching rows while editing
  if (editingRowId !== null) {
    const shouldDiscard = window.confirm('Discard unsaved changes?');
    if (!shouldDiscard) {
      return;
    }
    // Discard draft
    setEditingRowId(null);
    setDraftById((prev) => {
      const { [editingRowId]: _, ...rest } = prev;
      return rest;
    });
  }
  
  setSelectedModelId(row.expected_model_id);
  setSidePanelOpen(true);
};
```

**Behavior**:
- Side panel does NOT open automatically on row creation
- Side panel opens only on explicit row click (when not editing)
- Selection state: `selectedModelId`, `sidePanelOpen` (both local state in QualityTab)

**Note**: No integration with `useWorkspaceSelection` hook (URL query params `?sel=model:123` are NOT used)

---

### 7. Edit Mode & Inline Editing

**Location**: [frontend/src/components/quality/QualityRegisterTable.tsx](frontend/src/components/quality/QualityRegisterTable.tsx#L188-L224)

```tsx
const renderEditableCell = (row: QualityRegisterRow, field: keyof EditableFields, displayValue: string | null) => {
  const isEditing = editingRowId === row.expected_model_id;
  const draft = draftById[row.expected_model_id] || {};
  const value = draft[field] !== undefined ? draft[field] : displayValue;

  if (isEditing) {
    return (
      <TextField
        size="small"
        fullWidth
        value={value || ''}
        onChange={(e) => onDraftChange(row.expected_model_id, field, e.target.value)}
        onKeyDown={(e) => handleKeyDown(e, row.expected_model_id, field, editableFields)}
        inputRef={field === 'abv' ? firstCellRef : undefined}
        inputProps={{
          'data-row': row.expected_model_id,
          'data-field': field
        }}
        multiline={field === 'description' || field === 'notes'}
        rows={field === 'description' ? 2 : field === 'notes' ? 1 : 1}
      />
    );
  }

  return value || '—';
};
```

**Data ownership**:
- Draft state: `draftById[rowId]` (local state in QualityTab)
- Changes: `onDraftChange` → updates draft
- Keyboard navigation: Enter/Shift+Enter to move between fields, Esc to cancel

---

### 8. Save Operation

**Location**: [frontend/src/pages/QualityTab.tsx](frontend/src/pages/QualityTab.tsx#L200-L214)

```tsx
const handleSaveRow = async (rowId: number, draft: EditableFields) => {
  // Trim whitespace
  const trimmedDraft: EditableFields = {};
  if (draft.abv !== undefined) trimmedDraft.abv = draft.abv.trim();
  if (draft.registeredModelName !== undefined) trimmedDraft.registeredModelName = draft.registeredModelName.trim();
  if (draft.company !== undefined) trimmedDraft.company = draft.company.trim();
  if (draft.discipline !== undefined) trimmedDraft.discipline = draft.discipline.trim();
  if (draft.description !== undefined) trimmedDraft.description = draft.description.trim();
  if (draft.bimContact !== undefined) trimmedDraft.bimContact = draft.bimContact.trim();
  if (draft.notes !== undefined) trimmedDraft.notes = draft.notes.trim();

  await updateModelMutation.mutateAsync({ rowId, draft: trimmedDraft });
};
```

**Mutation**: [frontend/src/pages/QualityTab.tsx](frontend/src/pages/QualityTab.tsx#L86-L123)

```tsx
const updateModelMutation = useMutation({
  mutationFn: ({ rowId, draft }: { rowId: number; draft: EditableFields }) =>
    qualityApi.updateExpectedModel(projectId, rowId, draft),
  onSuccess: (_, variables) => {
    // 1. Exit edit mode
    setEditingRowId(null);
    setDraftById((prev) => {
      const { [variables.rowId]: _, ...rest } = prev;
      return rest;
    });
    
    // 2. Update cache in-place
    queryClient.setQueryData<QualityPhase1DRegisterResponse>(
      ['quality-register-phase1d', projectId],
      (old) => {
        if (!old) return old;
        return {
          ...old,
          rows: old.rows.map((row) =>
            row.expected_model_id === variables.rowId
              ? {
                  ...row,
                  abv: variables.draft.abv ?? row.abv,
                  modelName: variables.draft.registeredModelName ?? row.modelName,
                  company: variables.draft.company ?? row.company,
                  discipline: variables.draft.discipline ?? row.discipline,
                  description: variables.draft.description ?? row.description,
                  bimContact: variables.draft.bimContact ?? row.bimContact,
                  notes: variables.draft.notes ?? row.notes
                }
              : row
          )
        };
      }
    );
    
    // 3. Background invalidate
    queryClient.invalidateQueries({ 
      queryKey: ['quality-register-phase1d', projectId] 
    });
  }
});
```

---

## Call Graph Summary

```
User clicks "Add row"
  ↓
[QualityRegisterTable] onAddRow prop
  ↓
[QualityTab] handleAddRow()
  ↓
[QualityTab] createModelMutation.mutate()
  ↓
[API] qualityApi.createEmptyModel(projectId)
  │   ├─ Generates key: NEW-MODEL-{timestamp}
  │   └─ Generates display_name: New Model {date}
  ↓
[Backend] POST /api/projects/{id}/quality/expected-models
  │   └─ manager.add_expected_model(...)
  ↓
[Database] INSERT into ExpectedModels
  ↓
[Response] { expected_model_id: 123 }
  ↓
[QualityTab] createModelMutation.onSuccess(data)
  │   ├─ queryClient.setQueryData(...) → adds row to cache
  │   ├─ setEditingRowId(data.id) → enters edit mode
  │   ├─ setDraftById({ [id]: {...} }) → initializes draft
  │   └─ queryClient.invalidateQueries(...) → refetch in background
  ↓
[QualityRegisterTable] Re-render with new row
  │   └─ Row shows in edit mode with inline TextField inputs
  ↓
User edits fields inline
  ↓
User clicks Save icon
  ↓
[QualityTab] handleSaveRow(rowId, draft)
  ↓
[QualityTab] updateModelMutation.mutateAsync(...)
  ↓
[API] qualityApi.updateExpectedModel(projectId, rowId, draft)
  ↓
[Backend] PATCH /api/projects/{id}/quality/expected-models/{rowId}
  ↓
[Database] UPDATE ExpectedModels SET abv=?, ...
  ↓
[QualityTab] updateModelMutation.onSuccess()
  │   ├─ setEditingRowId(null) → exits edit mode
  │   ├─ setDraftById cleanup
  │   ├─ queryClient.setQueryData(...) → updates cache row
  │   └─ queryClient.invalidateQueries(...) → refetch in background
  ↓
[QualityRegisterTable] Re-render with updated row (read-only)
```

---

## (B) Overlapping/Conflicting Logic

### 1. **Double Invalidation Pattern**

**Location**: [frontend/src/pages/QualityTab.tsx](frontend/src/pages/QualityTab.tsx#L36-L83)

**Issue**:
```tsx
// createModelMutation.onSuccess:
queryClient.setQueryData(...);  // Optimistic update
queryClient.invalidateQueries({ queryKey: ['quality-register-phase1d', projectId] });  // Immediate refetch
```

**Symptom**: 
- Optimistic row is rendered
- Background refetch triggers almost immediately
- Two renders occur in quick succession
- User sees flicker if server response differs from optimistic data

**Conflict**: Optimistic update is pointless if immediately invalidated

**Recommendation**: Remove `invalidateQueries` or make it conditional (only on error recovery)

---

### 2. **Key Generation in Client vs Server**

**Location**: 
- Client: [frontend/src/api/quality.ts](frontend/src/api/quality.ts#L240-L242)
- Server: [backend/app.py](backend/app.py#L5737)

**Issue**:
```typescript
// Client generates key
const key = `NEW-MODEL-${timestamp}`;

// Server has fallback
expected_model_key=data.get('expected_model_key', 'UNNAMED-MODEL')
```

**Symptom**:
- All new rows have keys like `NEW-MODEL-2026-01-19T14-30-22`
- Keys are not human-readable or project-specific
- Keys are generated BEFORE user edits any fields
- If user wants to set a specific key, they must edit after creation

**Conflict**: Key generation happens too early; user has no control

**Recommendation**: Use temp key `-1`, `-2`, etc., then require user to set real key during inline edit, or auto-generate from `abv` + `discipline` on first save

---

### 3. **Duplicate Source of Truth**

**Locations**:
- React Query cache: `['quality-register-phase1d', projectId]`
- Local state: `draftById[rowId]`
- React Query cache again: invalidated after mutation

**Issue**:
```tsx
// Data flow:
Server → RQ cache → draftById → User edit → updateMutation → RQ cache update → invalidate → Server → RQ cache
```

**Symptom**:
- Draft state and cache can diverge if user doesn't save
- Invalidation after save causes refetch, potentially overwriting optimistic updates with server data
- If server data differs (e.g., auto-generated fields), user sees data change after save

**Conflict**: Three-way sync between server, cache, and draft

**Recommendation**: Single source of truth (draft rows OR cache); reconcile only on successful save

---

### 4. **Auto-Edit Mode After Creation**

**Location**: [frontend/src/pages/QualityTab.tsx](frontend/src/pages/QualityTab.tsx#L64-L79)

**Issue**:
```tsx
// createModelMutation.onSuccess:
setEditingRowId(data.id);  // Auto-enter edit mode
setDraftById((prev) => ({
  ...prev,
  [data.id]: {
    abv: '',
    registeredModelName: '',
    company: '',
    discipline: '',
    description: '',
    bimContact: '',
    notes: ''
  }
}));
```

**Symptom**:
- User clicks "Add row"
- Row appears immediately in edit mode
- User MUST interact (save or cancel) before clicking another row
- If user clicks away, they get "Discard unsaved changes?" prompt

**Benefit**: This is actually GOOD behavior (aligned with goal)

**No conflict**: This is the desired flow; we want this

---

### 5. **Side Panel Not Auto-Opening**

**Location**: [frontend/src/pages/QualityTab.tsx](frontend/src/pages/QualityTab.tsx#L163-L182)

**Issue**: Side panel does NOT open after creation

**Symptom**: None (this is good!)

**Alignment**: This is ALIGNED with the goal (no side panel on creation)

**No conflict**: Keep this behavior

---

### 6. **No URL Selection Sync**

**Observation**: `QualityTab` does NOT use `useWorkspaceSelection` hook

**Issue**: Unlike other tabs (Services, Issues, Updates), Quality tab uses local state for selection

**Symptom**:
- URL does not update with `?sel=model:123`
- Deep linking to a specific model is not supported
- Browser back/forward does not navigate between models

**Conflict**: Inconsistent with other workspace tabs

**Recommendation**: Add `useWorkspaceSelection` integration if deep linking is desired; otherwise, this is fine for Phase 1D

---

### 7. **Edit Mode Blocking**

**Location**: [frontend/src/components/quality/QualityRegisterTable.tsx](frontend/src/components/quality/QualityRegisterTable.tsx#L381)

**Issue**:
```tsx
<Button
  onClick={onAddRow}
  disabled={isAddingRow || editingRowId !== null}
>
  Add row
</Button>
```

**Symptom**:
- User cannot add a second row while first row is in edit mode
- User must save or cancel before adding another row

**Conflict**: Limits rapid multi-row entry

**Recommendation**: Support multiple draft rows simultaneously (see design proposal)

---

## (C) Proposed Simplified Design

### Core Principles

1. **Single Source of Truth**: React Query cache is authoritative
2. **Draft Rows**: Local draft state with temp IDs (`-1`, `-2`, etc.)
3. **Commit on Save**: API call only when user explicitly saves
4. **No Auto-Invalidate**: Only invalidate on external changes (imports, side panel edits)
5. **Multi-Draft Support**: Allow multiple rows in draft state

---

### Architecture

```
[React Query Cache]
  ├─ Persisted rows (id > 0)
  └─ Draft rows (id < 0, client-only)

[Local State]
  ├─ editingRowId: number | null
  ├─ draftById: Record<number, EditableFields>
  └─ nextTempId: number (starts at -1, decrements)

[API Calls]
  ├─ Create: POST with user-edited fields (not auto-generated)
  └─ Update: PATCH with changed fields only
```

---

### Draft Row Lifecycle

```
1. User clicks "Add row"
   ↓
   Generate temp ID: -1, -2, -3, ...
   ↓
   Add draft row to cache with temp ID
   ↓
   Enter edit mode for temp row

2. User edits inline
   ↓
   Update draftById[tempId] with changes

3. User clicks Save
   ↓
   Validate required fields (e.g., abv, modelName)
   ↓
   POST to API with draft fields
   ↓
   Server returns { expected_model_id: 123 }
   ↓
   Replace temp row with real row in cache
   ↓
   Exit edit mode

4. User clicks Cancel
   ↓
   Remove temp row from cache
   ↓
   Clear draftById[tempId]
   ↓
   Exit edit mode
```

---

### Key Generation Strategy

**Option A**: User-provided (recommended)
- Require `abv` field during inline edit
- Auto-generate key from `abv` + timestamp on save
- Example: `ABV-2026-01-19-1430` or `ABV-001`

**Option B**: Server-generated
- Server generates key based on business logic (e.g., project code + sequence)
- Client sends minimal data, server returns full row

**Option C**: Hybrid
- Client generates temp key (e.g., `DRAFT-001`)
- Server replaces with real key on persist
- UI shows temp key until save

---

### Side Panel Behavior

**Trigger**: User explicitly clicks "View Details" or "Map/Aliases" button

**NOT triggered by**:
- Creating a new row
- Selecting a row for edit
- Saving a row

**Recommendation**: Add explicit "Details" button in Actions column for read-only rows

---

## (D) Implementation Plan

### Step 1: Introduce Draft Row State

**File**: [frontend/src/pages/QualityTab.tsx](frontend/src/pages/QualityTab.tsx)

**Changes**:
```tsx
// Add temp ID counter
const [nextTempId, setNextTempId] = useState(-1);

// Remove createModelMutation (replace with draft logic)
const handleAddRow = () => {
  const tempId = nextTempId;
  setNextTempId((prev) => prev - 1);
  
  // Add draft row to cache
  queryClient.setQueryData<QualityPhase1DRegisterResponse>(
    ['quality-register-phase1d', projectId],
    (old) => {
      if (!old) return { rows: [] };
      return {
        ...old,
        rows: [
          ...old.rows,
          {
            expected_model_id: tempId,
            abv: null,
            modelName: null,
            company: null,
            discipline: null,
            description: null,
            bimContact: null,
            folderPath: null,
            accPresent: false,
            accDate: null,
            reviztoPresent: false,
            reviztoDate: null,
            notes: null,
            notesUpdatedAt: null,
            mappingStatus: 'UNMAPPED',
            matchedObservedFile: null,
            validationOverall: 'UNKNOWN',
            freshnessStatus: 'UNKNOWN'
          }
        ]
      };
    }
  );
  
  // Enter edit mode
  setEditingRowId(tempId);
  setDraftById((prev) => ({
    ...prev,
    [tempId]: {
      abv: '',
      registeredModelName: '',
      company: '',
      discipline: '',
      description: '',
      bimContact: '',
      notes: ''
    }
  }));
};
```

**Risk**: None (additive change)

---

### Step 2: Update Save Logic to Handle Temp Rows

**File**: [frontend/src/pages/QualityTab.tsx](frontend/src/pages/QualityTab.tsx)

**Changes**:
```tsx
const handleSaveRow = async (rowId: number, draft: EditableFields) => {
  const trimmedDraft: EditableFields = {
    abv: draft.abv?.trim(),
    registeredModelName: draft.registeredModelName?.trim(),
    company: draft.company?.trim(),
    discipline: draft.discipline?.trim(),
    description: draft.description?.trim(),
    bimContact: draft.bimContact?.trim(),
    notes: draft.notes?.trim()
  };
  
  // Check if this is a draft row (temp ID)
  if (rowId < 0) {
    // CREATE operation
    try {
      // Validate required fields
      if (!trimmedDraft.abv || !trimmedDraft.registeredModelName) {
        alert('ABV and Model Name are required');
        return;
      }
      
      // Generate key from abv + timestamp
      const timestamp = Date.now();
      const key = `${trimmedDraft.abv}-${timestamp}`;
      
      // Call create API
      const result = await qualityApi.createExpectedModel(projectId, {
        expected_model_key: key,
        display_name: trimmedDraft.registeredModelName,
        discipline: trimmedDraft.discipline,
        // ... other fields
      });
      
      // Replace temp row with real row in cache
      queryClient.setQueryData<QualityPhase1DRegisterResponse>(
        ['quality-register-phase1d', projectId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            rows: old.rows.map((row) =>
              row.expected_model_id === rowId
                ? {
                    ...row,
                    expected_model_id: result.expected_model_id,
                    abv: trimmedDraft.abv,
                    modelName: trimmedDraft.registeredModelName,
                    company: trimmedDraft.company,
                    discipline: trimmedDraft.discipline,
                    description: trimmedDraft.description,
                    bimContact: trimmedDraft.bimContact,
                    notes: trimmedDraft.notes
                  }
                : row
            )
          };
        }
      );
      
      // Exit edit mode
      setEditingRowId(null);
      setDraftById((prev) => {
        const { [rowId]: _, ...rest } = prev;
        return rest;
      });
      
      // Optional: Refetch to get server-generated fields
      // queryClient.invalidateQueries({ queryKey: ['quality-register-phase1d', projectId] });
      
    } catch (error) {
      console.error('Failed to create model:', error);
      alert('Failed to save. Please try again.');
    }
  } else {
    // UPDATE operation (existing logic)
    await updateModelMutation.mutateAsync({ rowId, draft: trimmedDraft });
  }
};
```

**Risk**: Medium (changes save behavior; needs testing)

---

### Step 3: Update Cancel Logic to Handle Temp Rows

**File**: [frontend/src/pages/QualityTab.tsx](frontend/src/pages/QualityTab.tsx)

**Changes**:
```tsx
const handleCancelEdit = (rowId: number) => {
  // Check if this is a draft row (temp ID)
  if (rowId < 0) {
    // Remove draft row from cache
    queryClient.setQueryData<QualityPhase1DRegisterResponse>(
      ['quality-register-phase1d', projectId],
      (old) => {
        if (!old) return old;
        return {
          ...old,
          rows: old.rows.filter((row) => row.expected_model_id !== rowId)
        };
      }
    );
  }
  
  // Clear draft and exit edit mode
  setEditingRowId(null);
  setDraftById((prev) => {
    const { [rowId]: _, ...rest } = prev;
    return rest;
  });
};
```

**Risk**: Low (additive logic)

---

### Step 4: Remove Auto-Invalidation

**File**: [frontend/src/pages/QualityTab.tsx](frontend/src/pages/QualityTab.tsx)

**Changes**:
```tsx
// In updateModelMutation.onSuccess:
// REMOVE this line:
// queryClient.invalidateQueries({ queryKey: ['quality-register-phase1d', projectId] });

// Only invalidate on side panel changes or external imports
```

**Risk**: Low (removes unnecessary refetch)

---

### Step 5: Enable Multi-Draft Support

**File**: [frontend/src/components/quality/QualityRegisterTable.tsx](frontend/src/components/quality/QualityRegisterTable.tsx)

**Changes**:
```tsx
<Button
  startIcon={<AddIcon />}
  onClick={onAddRow}
  disabled={isAddingRow}  // Remove editingRowId !== null check
  size="small"
>
  Add row
</Button>
```

**Consideration**: Do we want to allow multiple draft rows simultaneously?

**Pros**:
- Faster data entry (add 5 rows, then edit all)
- Less clicking back and forth

**Cons**:
- More complex state management
- Risk of losing unsaved drafts if user navigates away

**Recommendation**: Start with single draft (current behavior), add multi-draft later if requested

**Risk**: Low (remove constraint)

---

### Step 6: Add Inline Validation Feedback

**File**: [frontend/src/components/quality/QualityRegisterTable.tsx](frontend/src/components/quality/QualityRegisterTable.tsx)

**Changes**:
```tsx
const renderEditableCell = (row, field, displayValue) => {
  const isEditing = editingRowId === row.expected_model_id;
  const draft = draftById[row.expected_model_id] || {};
  const value = draft[field] !== undefined ? draft[field] : displayValue;
  
  // Check if field is required and empty (for temp rows)
  const isRequired = row.expected_model_id < 0 && (field === 'abv' || field === 'registeredModelName');
  const isEmpty = !value || value.trim() === '';
  const showError = isRequired && isEmpty;

  if (isEditing) {
    return (
      <TextField
        size="small"
        fullWidth
        value={value || ''}
        onChange={(e) => onDraftChange(row.expected_model_id, field, e.target.value)}
        error={showError}
        helperText={showError ? 'Required' : ''}
        // ... other props
      />
    );
  }

  return value || '—';
};
```

**Risk**: Low (improves UX)

---

### Step 7: Update Delete Logic to Handle Temp Rows

**File**: [frontend/src/pages/QualityTab.tsx](frontend/src/pages/QualityTab.tsx)

**Changes**:
```tsx
const handleDeleteRow = async (rowId: number) => {
  // Check if this is a draft row (temp ID)
  if (rowId < 0) {
    // Just remove from cache (no API call)
    queryClient.setQueryData<QualityPhase1DRegisterResponse>(
      ['quality-register-phase1d', projectId],
      (old) => {
        if (!old) return old;
        return {
          ...old,
          rows: old.rows.filter((row) => row.expected_model_id !== rowId)
        };
      }
    );
    
    // Clear draft
    setDraftById((prev) => {
      const { [rowId]: _, ...rest } = prev;
      return rest;
    });
    
    return;
  }
  
  // Existing delete logic for persisted rows
  await deleteModelMutation.mutateAsync(rowId);
};
```

**Risk**: Low (additive logic)

---

### Step 8: Update API createExpectedModel to Accept Full Fields

**File**: [frontend/src/api/quality.ts](frontend/src/api/quality.ts)

**Changes**:
```tsx
createExpectedModel: async (
  projectId: number,
  payload: {
    expected_model_key: string;
    display_name?: string;
    discipline?: string;
    company?: string;
    description?: string;
    bim_contact?: string;
    notes?: string;
  }
): Promise<{ expected_model_id: number }> => {
  const response = await apiClient.post<{ expected_model_id: number }>(
    `/projects/${projectId}/quality/expected-models`,
    payload
  );
  return response.data;
}
```

**Risk**: Low (additive API change; backend already supports these fields)

---

### Step 9: Update Backend to Accept Additional Fields

**File**: [backend/app.py](backend/app.py)

**Changes**: Backend endpoint already accepts `discipline`, `company_id`, etc. No changes needed.

**Action**: Verify that backend service method `add_expected_model` accepts all fields.

**Risk**: None (backend already supports this)

---

### Step 10: Add Draft Row Indicator in UI

**File**: [frontend/src/components/quality/QualityRegisterTable.tsx](frontend/src/components/quality/QualityRegisterTable.tsx)

**Changes**:
```tsx
<TableRow
  key={row.expected_model_id}
  hover={!isEditing}
  onClick={(e) => handleCellClick(row, e)}
  selected={selectedRowId === row.expected_model_id || isEditing}
  sx={{ 
    cursor: isEditing ? 'default' : 'pointer',
    backgroundColor: isEditing 
      ? 'action.selected' 
      : row.expected_model_id < 0 
        ? 'warning.light'  // Draft row highlight
        : undefined
  }}
>
```

**Risk**: Low (visual enhancement)

---

### Step 11: Handle Rapid Multi-Row Adds

**File**: [frontend/src/pages/QualityTab.tsx](frontend/src/pages/QualityTab.tsx)

**Consideration**: If allowing multi-draft, ensure temp IDs don't collide

**Current logic**: `setNextTempId((prev) => prev - 1)` ensures unique IDs

**Risk**: None (already handled)

---

## Implementation Checklist (Ordered)

- [ ] **Step 1**: Add `nextTempId` state and draft row logic to `handleAddRow`
- [ ] **Step 2**: Update `handleSaveRow` to detect temp rows and call CREATE vs UPDATE
- [ ] **Step 3**: Update `handleCancelEdit` to remove draft rows from cache
- [ ] **Step 4**: Remove `invalidateQueries` from `updateModelMutation.onSuccess`
- [ ] **Step 5**: (Optional) Enable multi-draft by removing `editingRowId !== null` check
- [ ] **Step 6**: Add inline validation feedback for required fields
- [ ] **Step 7**: Update `handleDeleteRow` to handle temp rows without API call
- [ ] **Step 8**: Expand `createExpectedModel` API signature to accept all editable fields
- [ ] **Step 9**: Verify backend supports all fields (no code changes needed)
- [ ] **Step 10**: Add visual indicator for draft rows (light background)
- [ ] **Step 11**: (Already handled) Ensure temp ID uniqueness

---

## Edge Cases & Risk Notes

### 1. User Navigates Away with Unsaved Draft

**Risk**: Draft row lost

**Mitigation**:
- Add `beforeunload` event listener to warn user
- OR: Store drafts in `localStorage` and restore on mount
- OR: Auto-save drafts to server as "pending" status

**Recommendation**: Start with warning dialog; add auto-save later if needed

---

### 2. Create API Fails (Network Error, Validation Error)

**Risk**: Draft row remains in cache with temp ID; user clicks save again → duplicate API call

**Mitigation**:
```tsx
try {
  const result = await qualityApi.createExpectedModel(...);
  // Success: replace temp row
} catch (error) {
  // Show error inline
  alert(`Failed to save: ${error.message}`);
  // Keep draft row in edit mode
  // User can fix fields and try again
}
```

**Recommendation**: Show inline error, do not remove draft row

---

### 3. Duplicate Model Key

**Risk**: Server rejects create due to unique constraint violation

**Mitigation**:
- Backend returns 409 Conflict with error message
- Frontend shows error: "Model key already exists. Please choose a different ABV."
- User edits `abv` field and tries again

**Recommendation**: Clear error messaging; suggest auto-appending sequence number

---

### 4. Rapid Multi-Row Adds with Slow Network

**Risk**: Multiple temp rows accumulate; user loses track of which are saved

**Mitigation**:
- Show save spinner icon in Actions column while saving
- Disable save button after click until response
- Show checkmark icon after successful save

**Recommendation**: Add visual feedback for save-in-progress state

---

### 5. Pagination/Sorting with Draft Rows

**Risk**: Draft rows (temp ID < 0) may sort incorrectly or disappear on pagination

**Mitigation**:
- Draft rows always appear at TOP of table (regardless of sort)
- OR: Draft rows have special "Draft" status and sort last
- Disable pagination while drafts exist

**Recommendation**: Pin draft rows to top; show "Save or cancel drafts to enable sorting"

---

### 6. Optimistic Update Conflicts with Server Data

**Risk**: User saves draft; server returns different data (e.g., auto-generated `created_at`)

**Mitigation**:
- Only update fields that were user-edited
- Preserve server-generated fields in cache
- Optional: Refetch after save to get all server fields

**Recommendation**: Do NOT invalidate immediately; refetch on interval or user refresh

---

### 7. User Deletes Draft Row by Mistake

**Risk**: No undo; data lost

**Mitigation**:
- Show confirmation dialog: "Delete unsaved draft?"
- OR: Move to "Recently deleted" area with restore option
- OR: Store deleted drafts in `localStorage` for 24h

**Recommendation**: Add confirmation dialog for draft deletes only

---

## Acceptance Criteria

### After Clicking "Add row"

✅ A new row appears immediately at the **bottom** of the table (or top if sorted descending)

✅ Row has temp ID (negative number, e.g., `-1`, `-2`)

✅ Row is in **"draft" state** (light yellow background or badge indicator)

✅ Row enters **edit mode** automatically (all editable cells show TextFields)

✅ First cell (ABV) is **auto-focused**

✅ User can type inline in all editable cells

✅ **No side panel opens** automatically

✅ User can press Enter to move between fields, Esc to cancel

---

### During Inline Editing

✅ Draft state is preserved in `draftById[tempId]`

✅ Required fields (ABV, Model Name) show validation error if empty

✅ User can cancel (delete draft row) or save (persist to server)

✅ User can add multiple draft rows if multi-draft enabled (optional)

✅ Clicking another row prompts "Discard unsaved changes?"

---

### On Save

✅ **One clear create call** occurs: `POST /api/projects/{id}/quality/expected-models`

✅ Request includes all user-edited fields (not auto-generated key)

✅ Temp row is **replaced** with real row (server-returned ID)

✅ No duplicate rows appear

✅ Row exits edit mode and becomes read-only

✅ **No automatic refetch/invalidation** (cache is source of truth)

---

### On Cancel

✅ Draft row is **removed** from table

✅ No API call occurs

✅ Draft state is cleared

---

### On Error

✅ Error message shows inline (alert or Snackbar)

✅ Draft row remains in edit mode

✅ User can fix fields and retry save

✅ No duplicate API calls on retry

---

### Side Panel Behavior

✅ Side panel does NOT open on row creation

✅ Side panel opens only when user clicks row (after save)

✅ Side panel shows mapping/alias tools (not basic edit fields)

---

### Performance

✅ Minimal rerenders (only affected row updates)

✅ No conflicting state updates (single source of truth)

✅ No flicker or UI jank

✅ Fast interaction (no network delay for draft row creation)

---

## Summary

**Current flow**: 
- User clicks "Add row" → API call → optimistic cache update → auto-edit mode → background refetch → potential flicker

**Proposed flow**: 
- User clicks "Add row" → local draft row with temp ID → inline edit → save → API call → replace temp row with real row → done

**Key improvements**:
1. No API call until save (faster, no network delay)
2. No auto-invalidation (no unnecessary refetches)
3. Clear draft row lifecycle (temp ID → real ID on save)
4. Better error handling (retry without losing data)
5. Multi-draft support (optional, allows rapid entry)

**Migration effort**: 
- ~200 lines of code changes
- 1-2 days development + testing
- Low risk (additive changes, no breaking changes)

**Next steps**:
1. Review proposal with team
2. Implement Steps 1-7 as POC
3. Test edge cases (network error, duplicate key, cancel, delete)
4. Add Step 10 (draft row indicator) for visual feedback
5. Deploy to dev environment for user testing
