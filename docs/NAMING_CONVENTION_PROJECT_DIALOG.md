# Naming Convention Integration - Project Dialog

## Overview
The Project Form Dialog now displays and manages file naming conventions based on the selected client's settings.

## Features Implemented

### 1. Client Selector Enhancement
- **Location**: Project Form Dialog → Client dropdown
- **Functionality**: 
  - Shows naming convention code in brackets next to client name (e.g., "ABC Developers [AWS]")
  - Automatically populates project's naming convention when client is selected
  
```tsx
// Example client dropdown option display:
ABC Developers [AWS]
XYZ Corp [SINSW]
Test Client (no convention)
```

### 2. Naming Convention Badge Display
- **Location**: Appears below client selector when a client with naming convention is selected
- **Functionality**: 
  - Visual indicator (Chip component) showing active naming convention
  - Format: "File Naming Convention: AWS" or "File Naming Convention: SINSW"
  - Color: Info (blue)
  
### 3. Optional Naming Convention Override
- **Location**: Project Form Dialog → After Project Type field
- **Functionality**: 
  - Dropdown allowing manual selection of naming convention
  - Can override client's default convention
  - Options loaded from backend naming conventions
  - Helper text: "Optional: Override client's default naming convention"
  - Default option: "Use Client Default"

```tsx
// Dropdown options:
- Use Client Default
- AWS (ISO 19650)
- SINSW (ISO 19650-2 + SINSW National Annex 2021)
```

## User Workflow

### Creating a New Project
1. User opens "Create New Project" dialog
2. User selects a client from dropdown
3. If client has a naming convention:
   - Badge appears showing the convention
   - Convention is auto-populated in form data
4. User can optionally override the convention using the dropdown
5. On submit, project is saved with the naming convention

### Editing an Existing Project
1. User opens "Edit Project" dialog
2. Form loads with current project data
3. Client's naming convention is displayed
4. User can change client (updates convention automatically)
5. User can manually override convention if needed
6. On submit, updated convention is saved

## Technical Implementation

### Component Updates
**File**: `frontend/src/components/ProjectFormDialog.tsx`

#### Added Imports
```tsx
import { clientsApi } from '../api/clients';
import { useNamingConventionOptions } from '../hooks/useNamingConventions';
import type { Client } from '../api/clients';
import { Chip } from '@mui/material';
```

#### Form State Extension
```tsx
const [formData, setFormData] = useState({
  // ... existing fields
  naming_convention: '',  // NEW
});
```

#### Client Data Query Update
```tsx
// OLD: Direct fetch
const { data: clients = [] } = useQuery<ReferenceOption[]>({
  queryKey: ['reference', 'clients'],
  queryFn: () => fetch('/api/reference/clients').then(r => r.json()),
});

// NEW: Using clientsApi with naming convention support
const { data: clients = [] } = useQuery<Client[]>({
  queryKey: ['clients'],
  queryFn: clientsApi.getAll,
});
```

#### Naming Convention Options Hook
```tsx
const { options: namingConventionOptions, isLoading: namingConventionsLoading } = 
  useNamingConventionOptions();
```

#### Special Client Change Handler
```tsx
const handleClientChange = (event: React.ChangeEvent<HTMLInputElement>) => {
  const clientId = event.target.value;
  const selectedClient = clients.find(c => c.id === Number(clientId));
  
  setFormData((prev) => ({ 
    ...prev, 
    client_id: clientId,
    naming_convention: selectedClient?.naming_convention || ''
  }));
  setError(null);
};
```

### UI Components Added

#### 1. Enhanced Client Dropdown
```tsx
<MenuItem key={client.id} value={client.id}>
  {client.name}
  {client.naming_convention && (
    <span style={{ marginLeft: '8px', fontSize: '0.85em', color: '#666' }}>
      [{client.naming_convention}]
    </span>
  )}
</MenuItem>
```

#### 2. Naming Convention Badge
```tsx
{formData.client_id && (() => {
  const selectedClient = clients.find(c => c.id === Number(formData.client_id));
  return selectedClient?.naming_convention ? (
    <Grid item xs={12}>
      <Chip 
        label={`File Naming Convention: ${selectedClient.naming_convention}`}
        color="info"
        size="small"
        sx={{ mt: -1 }}
      />
    </Grid>
  ) : null;
})()}
```

#### 3. Naming Convention Override Dropdown
```tsx
<Grid item xs={12} sm={6}>
  <TextField
    label="Naming Convention (Override)"
    value={formData.naming_convention}
    onChange={handleChange('naming_convention')}
    fullWidth
    select
    disabled={isLoading || namingConventionsLoading}
    helperText="Optional: Override client's default naming convention"
  >
    <MenuItem value="">
      <em>Use Client Default</em>
    </MenuItem>
    {namingConventionOptions.map((option) => (
      <MenuItem key={option.value} value={option.value}>
        {option.label}
      </MenuItem>
    ))}
  </TextField>
</Grid>
```

## Data Flow

1. **Client Selection**:
   - User selects client → `handleClientChange` fired
   - Client lookup finds naming convention
   - Form state updated with `naming_convention`

2. **Badge Display**:
   - React re-renders after state update
   - Conditional rendering checks if client has naming convention
   - Chip component displays if convention exists

3. **Manual Override**:
   - User can change dropdown value
   - Updates `formData.naming_convention`
   - Overrides client's default

4. **Form Submission**:
   - `formData.naming_convention` included in payload
   - Sent to backend API
   - Saved with project record

## Testing Steps

### Test 1: Client with Naming Convention
1. Open project creation dialog
2. Select client "AWS" (has AWS convention)
3. ✅ Verify badge appears: "File Naming Convention: AWS"
4. ✅ Verify dropdown shows AWS selected
5. Submit and check database

### Test 2: Client without Naming Convention
1. Open project creation dialog
2. Select client without convention
3. ✅ Verify no badge appears
4. ✅ Verify dropdown shows "Use Client Default"
5. Submit and check database

### Test 3: Manual Override
1. Open project creation dialog
2. Select client "AWS" (has AWS convention)
3. Change override dropdown to "SINSW"
4. ✅ Verify badge still shows AWS (client's default)
5. ✅ Verify override dropdown shows SINSW
6. Submit and check database stores SINSW

### Test 4: Edit Existing Project
1. Open edit dialog for project
2. ✅ Verify client's naming convention displays correctly
3. Change client to different one
4. ✅ Verify naming convention updates automatically
5. Save and verify changes persist

## Future Enhancements

### Potential Improvements
1. **Validation Rules**: Prevent file uploads that don't match naming convention
2. **Auto-naming**: Generate file names based on selected convention
3. **Convention Preview**: Show example file name format
4. **Client Management**: Add naming convention selector when creating/editing clients
5. **Convention Details**: Show full schema when hovering over badge

### Related Features
- File upload validation against naming patterns
- Bulk file renaming tool using conventions
- Convention compliance reporting
- Custom naming convention creation UI

## References
- Backend API: `/api/naming-conventions`, `/api/clients`
- Service Layer: `services/naming_convention_service.py`
- Database: `clients.naming_convention` column
- Type Definitions: `frontend/src/types/api.ts`
- API Client: `frontend/src/api/clients.ts`
- Hook: `frontend/src/hooks/useNamingConventions.ts`
