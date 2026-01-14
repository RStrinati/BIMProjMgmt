# Naming Convention Dropdown - Visual Guide

## Project Dialog Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Create New Project / Edit Project                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────┐  ┌─────────────────────────┐      │
│  │ Project Name            │  │ Project Number          │      │
│  │ [________________]      │  │ [________________]      │      │
│  └─────────────────────────┘  └─────────────────────────┘      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ Client                                ▼             │        │
│  │ [ABC Developers [AWS]               ]              │        │
│  │                                                     │        │
│  │ Options:                                            │        │
│  │   • ABC Developers [AWS]                           │        │
│  │   • XYZ Corp [SINSW]                               │        │
│  │   • Test Client (no convention)                    │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
│  ╔═════════════════════════════════════════════════════╗        │
│  ║ ℹ File Naming Convention: AWS                      ║  ← NEW │
│  ╚═════════════════════════════════════════════════════╝        │
│                                                                  │
│  ┌─────────────────────────┐  ┌─────────────────────────┐      │
│  │ Project Type         ▼  │  │ Naming Convention    ▼  │      │
│  │ [Residential        ]   │  │ [AWS (ISO 19650)    ] │ ← NEW │
│  └─────────────────────────┘  └─────────────────────────┘      │
│                                 Optional: Override              │
│                                 client's default                │
│                                                                  │
│  ┌─────────────────────────┐  ┌─────────────────────────┐      │
│  │ Status              ▼   │  │ Priority             ▼  │      │
│  │ [Active             ]   │  │ [Medium              ]  │      │
│  └─────────────────────────┘  └─────────────────────────┘      │
│                                                                  │
│  ... (rest of form fields) ...                                  │
│                                                                  │
│                         [Cancel]  [Save]                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Client Selector (Enhanced)
```
┌─────────────────────────────────────────┐
│ Client                              ▼   │
│ [ABC Developers [AWS]              ]    │
│                                         │
│ Dropdown Options:                       │
│   ABC Developers [AWS]         ← Shows convention code
│   XYZ Corp [SINSW]             ← Shows convention code  
│   Test Client                  ← No convention
└─────────────────────────────────────────┘
```

**Features**:
- Convention code shown in brackets `[AWS]`
- Auto-updates form when selection changes
- Triggers `handleClientChange()` function

---

### 2. Naming Convention Badge (Auto-Display)
```
╔═══════════════════════════════════════╗
║ ℹ File Naming Convention: AWS        ║
╚═══════════════════════════════════════╝
```

**Features**:
- Blue info chip (Material-UI)
- Only appears if selected client has a naming convention
- Updates automatically when client changes
- Size: `small`
- Color: `info` (blue)

**Conditional Rendering**:
```tsx
{selectedClient?.naming_convention && (
  <Chip label={`File Naming Convention: ${convention}`} />
)}
```

---

### 3. Naming Convention Override Dropdown ⭐
```
┌─────────────────────────────────────────┐
│ Naming Convention (Override)        ▼   │
│ [AWS (ISO 19650)                   ]    │
│                                         │
│ Optional: Override client's default     │
│                                         │
│ Dropdown Options:                       │
│   Use Client Default               ← Empty value
│   AWS (ISO 19650)                  ← Full name + standard
│   SINSW (ISO 19650-2 + SINSW...)   ← Full name + standard
└─────────────────────────────────────────┘
```

**Features**:
- Optional field (can be left as "Use Client Default")
- Auto-populates from client selection
- Can be manually changed to override
- Shows full convention name and standard
- Helper text explains purpose
- Disabled when loading conventions

**States**:
- **Default**: Shows "Use Client Default" (empty value)
- **Auto-populated**: Shows client's convention
- **Override**: User manually selects different convention

---

## User Interaction Flow

### Scenario 1: Client with Naming Convention
```
1. User selects "ABC Developers [AWS]"
        ↓
2. Badge appears: "File Naming Convention: AWS"
        ↓
3. Dropdown auto-fills: "AWS (ISO 19650)"
        ↓
4. User can optionally change dropdown to "SINSW"
        ↓
5. Save → Project saved with naming_convention = "SINSW"
```

### Scenario 2: Client without Naming Convention
```
1. User selects "Test Client"
        ↓
2. No badge appears
        ↓
3. Dropdown shows: "Use Client Default"
        ↓
4. User can optionally set a convention manually
        ↓
5. Save → Project saved with naming_convention = null or selected value
```

### Scenario 3: Changing Client
```
1. User has selected "ABC Developers [AWS]"
2. Badge shows "AWS", dropdown shows "AWS (ISO 19650)"
        ↓
3. User changes to "XYZ Corp [SINSW]"
        ↓
4. Badge updates to "SINSW"
5. Dropdown updates to "SINSW (ISO 19650-2 + SINSW...)"
        ↓
6. Form state automatically synchronized
```

---

## Field Positioning

### Grid Layout (Material-UI)
```tsx
<Grid container spacing={2}>
  <Grid item xs={12} sm={6}>
    {/* Project Name */}
  </Grid>
  
  <Grid item xs={12} sm={6}>
    {/* Project Number */}
  </Grid>
  
  <Grid item xs={12} sm={6}>
    {/* Client Selector */}
  </Grid>
  
  {/* Badge (conditional, full width) */}
  <Grid item xs={12}>
    <Chip label="File Naming Convention: AWS" />
  </Grid>
  
  <Grid item xs={12} sm={6}>
    {/* Project Type */}
  </Grid>
  
  <Grid item xs={12} sm={6}>
    {/* Naming Convention Override Dropdown */}  ⭐ NEW
  </Grid>
  
  <Grid item xs={12} sm={6}>
    {/* Status */}
  </Grid>
  
  ... (more fields)
</Grid>
```

---

## Dropdown Options Detail

### Naming Convention Override Dropdown
```
┌───────────────────────────────────────────────────────┐
│ Naming Convention (Override)                      ▼   │
├───────────────────────────────────────────────────────┤
│ Value │ Label                                          │
├───────┼────────────────────────────────────────────────┤
│ ""    │ Use Client Default                   (italic) │
│ "AWS" │ AWS (ISO 19650)                                │
│ "SINSW"│ SINSW (ISO 19650-2 + SINSW National Annex...) │
└───────────────────────────────────────────────────────┘
```

---

## Color Coding

| Element | Color | Purpose |
|---------|-------|---------|
| Badge | Blue (`info`) | Shows active naming convention |
| Helper Text | Gray | Explains optional override |
| Convention Code | Gray (in dropdown) | Secondary text in client options |

---

## Responsive Behavior

### Desktop (sm and up)
```
[Project Name         ] [Project Number        ]
[Client                                        ]
  ℹ File Naming Convention: AWS
[Project Type         ] [Naming Convention    ]
[Status               ] [Priority             ]
```

### Mobile (xs)
```
[Project Name                          ]
[Project Number                        ]
[Client                                ]
  ℹ File Naming Convention: AWS
[Project Type                          ]
[Naming Convention (Override)          ]
[Status                                ]
[Priority                              ]
```

---

## Visual States

### Loading State
```
┌─────────────────────────────────────────┐
│ Naming Convention (Override)        ▼   │
│ [Loading...                        ]🔄  │ ← Disabled
└─────────────────────────────────────────┘
```

### Error State
```
┌─────────────────────────────────────────┐
│ Naming Convention (Override)        ▼   │
│ [Failed to load conventions        ]⚠️  │
└─────────────────────────────────────────┘
```

### Populated State
```
┌─────────────────────────────────────────┐
│ Naming Convention (Override)        ▼   │
│ [AWS (ISO 19650)                   ]✓   │
│                                         │
│ Optional: Override client's default     │
└─────────────────────────────────────────┘
```

---

## Key Points

✅ **Location**: After "Project Type" field
✅ **Width**: Half-width on desktop (6/12 grid)
✅ **Behavior**: Auto-populates, can be overridden
✅ **Validation**: Optional field
✅ **Label**: "Naming Convention (Override)"
✅ **Helper Text**: "Optional: Override client's default naming convention"

---

## Testing Checklist

- [ ] Badge appears when client with convention selected
- [ ] Badge disappears when client without convention selected
- [ ] Dropdown auto-populates from client
- [ ] Dropdown can be manually changed
- [ ] Client change updates badge and dropdown
- [ ] Form saves with correct naming_convention value
- [ ] "Use Client Default" option works correctly
- [ ] Loading state shows when conventions are fetching
- [ ] Mobile responsive layout works correctly

---

**Location in Code**: `frontend/src/components/ProjectFormDialog.tsx` (lines ~320-342)
