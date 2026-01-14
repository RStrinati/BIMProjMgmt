# Naming Convention React Integration - Complete Guide

## ✅ Backend API Updates (COMPLETED)

### New Endpoints Created

#### 1. GET /api/naming-conventions
Returns all available naming conventions with metadata:

```json
[
  {
    "code": "AWS",
    "name": "AWS",
    "standard": "ISO 19650",
    "field_count": 7
  },
  {
    "code": "SINSW",
    "name": "SINSW",
    "standard": "ISO 19650-2 + SINSW National Annex 2021",
    "field_count": 7
  }
]
```

**File**: `backend/app.py` - Line ~343

#### 2. GET /api/clients
Returns all clients with naming convention info:

```json
[
  {
    "id": 1,
    "name": "ABC Developers",
    "contact_name": "John Doe",
    "contact_email": "john@abc.com",
    "naming_convention": null
  },
  {
    "id": 8,
    "name": "AWS",
    "contact_name": "Jane Smith",
    "contact_email": "jane@aws.com",
    "naming_convention": "AWS"
  }
]
```

**File**: `backend/app.py` - Line ~372

#### 3. Updated GET /api/reference/clients
Now redirects to `/api/clients` for backward compatibility.

**File**: `backend/app.py` - Line ~341

## ✅ Frontend Files Created (COMPLETED)

### 1. API Client (`frontend/src/api/clients.ts`)

```typescript
export interface NamingConvention {
  code: string;
  name: string;
  standard: string;
  field_count: number;
}

export interface Client {
  id: number;
  name: string;
  contact_name?: string;
  contact_email?: string;
  naming_convention?: string | null;
}

export const clientsApi = {
  getAll: () => Promise<Client[]>
  getById: (id) => Promise<Client>
  create: (client) => Promise<Client>
  update: (id, client) => Promise<Client>
  delete: (id) => Promise<void>
}

export const namingConventionsApi = {
  getAll: () => Promise<NamingConvention[]>
}
```

### 2. Custom Hook (`frontend/src/hooks/useNamingConventions.ts`)

```typescript
// Basic hook
export const useNamingConventions = () => {
  // Returns: { data, isLoading, error, ... }
}

// With formatted options
export const useNamingConventionOptions = () => {
  // Returns: { options, conventions, isLoading, error, ... }
  // options format: [{ value: 'AWS', label: 'AWS (ISO 19650)' }, ...]
}
```

### 3. Updated Type Definitions (`frontend/src/types/api.ts`)

```typescript
export interface Client {
  client_id: number;
  client_name: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  naming_convention?: string | null;  // ← NEW
  created_at?: string;
}
```

## 📋 How to Use in React Components

### Example 1: Show Client's Naming Convention in Project Form

```tsx
import { useQuery } from '@tantml:parameter>
import { Client } from '../api/clients';

function ProjectForm() {
  const [selectedClientId, setSelectedClientId] = useState(null);
  
  // Load all clients with naming conventions
  const { data: clients = [] } = useQuery<Client[]>({
    queryKey: ['clients'],
    queryFn: () => fetch('/api/clients').then(r => r.json()),
  });
  
  // Find selected client
  const selectedClient = clients.find(c => c.id === selectedClientId);
  
  return (
    <div>
      <Select value={selectedClientId} onChange={e => setSelectedClientId(e.target.value)}>
        {clients.map(client => (
          <option key={client.id} value={client.id}>
            {client.name}
            {client.naming_convention && ` [${client.naming_convention}]`}
          </option>
        ))}
      </Select>
      
      {selectedClient?.naming_convention && (
        <Chip 
          label={`Naming Convention: ${selectedClient.naming_convention}`}
          color="info"
        />
      )}
    </div>
  );
}
```

### Example 2: Client Creation/Edit Form with Naming Convention

```tsx
import { useNamingConventionOptions } from '../hooks/useNamingConventions';

function ClientForm() {
  const [formData, setFormData] = useState({
    name: '',
    contact_name: '',
    contact_email: '',
    naming_convention: ''
  });
  
  const { options, isLoading } = useNamingConventionOptions();
  
  return (
    <form>
      <TextField
        label="Client Name"
        value={formData.name}
        onChange={e => setFormData({...formData, name: e.target.value})}
      />
      
      <TextField
        label="Naming Convention"
        value={formData.naming_convention}
        onChange={e => setFormData({...formData, naming_convention: e.target.value})}
        select
      >
        <MenuItem value=""><em>None</em></MenuItem>
        {options.map(opt => (
          <MenuItem key={opt.value} value={opt.value}>
            {opt.label}
          </MenuItem>
        ))}
      </TextField>
    </form>
  );
}
```

### Example 3: Display Naming Convention Badge in Client List

```tsx
import { Chip } from '@mui/material';

function ClientListItem({ client }) {
  return (
    <div>
      <h3>{client.name}</h3>
      <p>{client.contact_email}</p>
      
      {client.naming_convention && (
        <Chip 
          label={client.naming_convention}
          size="small"
          color="primary"
          variant="outlined"
        />
      )}
    </div>
  );
}
```

## 🧪 Testing the Integration

### Test Backend Endpoints

```bash
# Test naming conventions endpoint
curl http://localhost:5000/api/naming-conventions

# Test clients endpoint
curl http://localhost:5000/api/clients
```

Expected responses:
- `/api/naming-conventions`: Array of 2 conventions (AWS & SINSW)
- `/api/clients`: Array of clients with `naming_convention` field

### Test Frontend Components

1. **Start the backend**:
   ```bash
   cd backend
   python app.py
   ```

2. **Start the frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open browser** to http://localhost:5173

4. **Test the hook** in browser console:
   ```javascript
   fetch('/api/naming-conventions').then(r => r.json()).then(console.log)
   fetch('/api/clients').then(r => r.json()).then(console.log)
   ```

## 📝 Next Steps to Complete Integration

### 1. Create Client Management Page (Optional)

Create `frontend/src/pages/ClientsPage.tsx`:

```tsx
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Client } from '../api/clients';
import { useNamingConventionOptions } from '../hooks/useNamingConventions';

export const ClientsPage = () => {
  const { data: clients, isLoading } = useQuery<Client[]>({
    queryKey: ['clients'],
    queryFn: () => fetch('/api/clients').then(r => r.json()),
  });
  
  const { options: namingConventions } = useNamingConventionOptions();
  
  if (isLoading) return <div>Loading...</div>;
  
  return (
    <div>
      <h1>Clients</h1>
      {clients?.map(client => (
        <div key={client.id}>
          <h3>{client.name}</h3>
          {client.naming_convention && (
            <span>Convention: {client.naming_convention}</span>
          )}
        </div>
      ))}
    </div>
  );
};
```

### 2. Update ProjectFormDialog

Modify `frontend/src/components/ProjectFormDialog.tsx`:

1. Import the new Client type and hook:
   ```typescript
   import { Client } from '../api/clients';
   import { useQuery } from '@tanstack/react-query';
   ```

2. Update the clients query:
   ```typescript
   const { data: clients = [] } = useQuery<Client[]>({
     queryKey: ['clients'],
     queryFn: () => fetch('/api/clients').then(r => r.json()),
   });
   ```

3. Add naming convention display below the client selector:
   ```tsx
   <Grid item xs={12} sm={6}>
     <TextField label="Client" /* ... existing props */>
       {/* ... existing options */}
     </TextField>
     
     {/* Show naming convention for selected client */}
     {formData.client_id && (() => {
       const client = clients.find(c => c.id === Number(formData.client_id));
       return client?.naming_convention ? (
         <Chip 
           label={`Naming Convention: ${client.naming_convention}`}
           size="small"
           color="info"
           sx={{ mt: 1 }}
         />
       ) : null;
     })()}
   </Grid>
   ```

## 🎯 Benefits

1. **Automatic Validation** - Frontend knows which naming convention applies to each project
2. **User Guidance** - Shows users which standard their files must follow
3. **Data Integrity** - Naming convention stored with client, inherited by projects
4. **Easy to Extend** - Add new conventions by creating JSON files

## 📚 File Reference

| File | Purpose | Status |
|------|---------|--------|
| `backend/app.py` | API endpoints | ✅ Updated |
| `frontend/src/api/clients.ts` | Client & naming convention API | ✅ Created |
| `frontend/src/hooks/useNamingConventions.ts` | React hook | ✅ Created |
| `frontend/src/types/api.ts` | TypeScript types | ✅ Updated |
| `frontend/src/components/ProjectFormDialog.tsx` | Project form | 📝 Ready to update |
| `frontend/src/pages/ClientsPage.tsx` | Client management | 📝 Optional |

## 🚀 Quick Start

1. **Backend is ready** - All endpoints are live
2. **Frontend files are ready** - All utilities and hooks created
3. **Update UI components** - Follow examples above to add dropdowns and displays
4. **Test** - Use browser console to verify API responses

The integration is 90% complete! Just add the UI components where you need them.
