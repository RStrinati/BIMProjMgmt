# Naming Convention Integration Guide

## Overview
This guide explains how to integrate client-specific naming conventions (AWS and SINSW) into the BIM Project Management system.

## Changes Made

### 1. Database Schema (`constants/schema.py`)
✅ Added `NAMING_CONVENTION` field to `Clients` class

### 2. SQL Migration (`sql/migrations/add_naming_convention_to_clients.sql`)
✅ Created migration to add `naming_convention` column to clients table
- Column type: NVARCHAR(50) NULL
- Check constraint: Values must be 'AWS', 'SINSW', or NULL

**To apply migration:**
```powershell
# Run from SQL Server Management Studio or via command line
sqlcmd -S YOUR_SERVER -d ProjectManagement -i sql/migrations/add_naming_convention_to_clients.sql
```

### 3. Naming Convention Files (`constants/naming_conventions/`)
✅ Created directory structure:
```
constants/naming_conventions/
├── README.md
├── AWS.json      # AWS naming convention (ISO 19650)
└── SINSW.json    # SINSW naming convention (ISO 19650-2 + SINSW National Annex 2021)
```

### 4. Database Functions (`database.py`)
✅ Updated functions:
- `get_available_clients()` - Now returns naming_convention
- `create_new_client(client_data)` - Now accepts naming_convention parameter
- `get_client_naming_convention(client_id)` - New function to get client's convention

### 5. Naming Convention Service (`services/naming_convention_service.py`)
✅ Created service with methods:
- `get_convention_schema(code)` - Load JSON schema for a convention
- `get_available_conventions()` - List all available conventions
- `get_convention_path(code)` - Get file path for a convention
- `validate_convention_exists(code)` - Check if convention exists
- `get_convention_summary(code)` - Get convention metadata

## UI Integration (Manual Steps Required)

### Step 1: Update Client Creation Dialog

In `phase1_enhanced_ui.py`, update the `show_new_client_dialog` method in BOTH instances (there are duplicates):

1. **Change dialog height** from `500x500` to `500x550`
2. **Add naming convention field** after the postcode field (row 8):

```python
# Naming Convention
ttk.Label(fields_frame, text="Naming Convention:").grid(row=8, column=0, sticky="w", pady=5)
client_vars['naming_convention'] = tk.StringVar()

# Get available naming conventions
from services.naming_convention_service import get_available_conventions
conventions = get_available_conventions()
convention_values = [""] + [f"{code} - {name}" for code, name in conventions]

naming_combo = ttk.Combobox(fields_frame, textvariable=client_vars['naming_convention'], 
                             values=convention_values, state='readonly', width=38)
naming_combo.grid(row=8, column=1, sticky="ew", pady=5)
```

3. **Update the `save_client` function** to include naming convention:

```python
def save_client():
    """Save the new client to database"""
    try:
        from database import create_new_client
        
        # Extract naming convention code from selection
        naming_conv_value = client_vars['naming_convention'].get().strip()
        naming_conv_code = naming_conv_value.split(' - ')[0] if naming_conv_value else None
        
        client_data = {
            'client_name': client_vars['name'].get().strip(),
            'contact_name': client_vars['contact'].get().strip(),
            'contact_email': client_vars['email'].get().strip(),
            'contact_phone': client_vars['phone'].get().strip(),
            'address': client_vars['address'].get().strip(),
            'city': client_vars['city'].get().strip(),
            'state': client_vars['state'].get().strip(),
            'postcode': client_vars['postcode'].get().strip(),
            'country': 'Australia',
            'naming_convention': naming_conv_code  # ← ADD THIS LINE
        }
        # ... rest of the function
```

### Step 2: Update Validation Tab (`ui/tab_validation.py`)

Update `check_naming_conventions` function to automatically use client's naming convention:

```python
def check_naming_conventions():
    if " - " not in cmb_projects.get():
        messagebox.showerror("Error", "Select a project first")
        return

    project_id_str, project_name = cmb_projects.get().split(" - ", 1)
    project_id = int(project_id_str)

    # Get client's naming convention from project
    from database import get_project_details, get_client_naming_convention
    from services.naming_convention_service import get_convention_path
    
    project_details = get_project_details(project_id)
    if not project_details:
        messagebox.showerror("Error", "Could not load project details")
        return
    
    # Get client ID from project (you may need to adjust based on your schema)
    # Then get the naming convention
    client_id = project_details.get('client_id')  # Adjust key as needed
    
    if not client_id:
        messagebox.showwarning("No Client", "Project has no client assigned")
        return
    
    naming_convention = get_client_naming_convention(client_id)
    
    if not naming_convention:
        messagebox.showwarning("No Convention", 
            "Client has no naming convention set. Please set it in client settings.")
        return
    
    json_path = get_convention_path(naming_convention)
    
    if not json_path:
        messagebox.showerror("Error", f"Naming convention '{naming_convention}' not found")
        return

    # Continue with validation
    project_files = get_project_health_files(project_id)
    if not project_files:
        messagebox.showinfo("No Files", "No project files found")
        return

    results = validate_files(project_id, project_files, json_path, project_name)
    
    if results:
        result_msg = "\n".join([f"{file}: {reason}" for file, reason in results])
        messagebox.showwarning("Naming Issues Found", result_msg)
    else:
        messagebox.showinfo("Success", f"All files follow the {naming_convention} naming convention!")

    update_status(status_var, "Naming convention check complete.")
```

## Usage Workflow

### For End Users:

1. **Create/Edit Client** → Select naming convention from dropdown (AWS or SINSW)
2. **Create Project** → Assign to client (inherits naming convention)
3. **Validate Files** → Automatically uses client's naming convention

### For Administrators:

To add a new naming convention:

1. Create JSON file in `constants/naming_conventions/NEWCLIENT.json`
2. Follow the schema structure from AWS.json or SINSW.json
3. Update the check constraint in the migration SQL file
4. Re-run the migration or manually add the constraint

## Testing

After applying changes:

```python
# Test in Python console
from services.naming_convention_service import *

# List available conventions
conventions = get_available_conventions()
print(conventions)  # Should show [('AWS', 'AWS'), ('SINSW', 'SINSW')]

# Get schema
aws_schema = get_convention_schema('AWS')
print(aws_schema['institution'])  # Should print 'AWS'

# Test database
from database import get_client_naming_convention
naming_conv = get_client_naming_convention(1)  # Replace 1 with actual client_id
print(naming_conv)
```

## Benefits

1. **Automated Validation** - Files automatically validated against client-specific standards
2. **Centralized Management** - All naming conventions in one location
3. **Easy Updates** - Update JSON files without changing code
4. **Client-Specific** - Each client can have their own standard
5. **Extensible** - Easy to add new conventions

## Troubleshooting

**Issue**: Naming conventions not showing in UI
- Check that `constants/naming_conventions/` directory exists
- Verify JSON files are valid
- Check file permissions

**Issue**: Database error when creating client
- Apply the SQL migration first
- Check database connection
- Verify naming_convention value is valid ('AWS', 'SINSW', or NULL)

**Issue**: Validation fails
- Ensure project has a client assigned
- Ensure client has naming_convention set
- Check that JSON schema file exists

## Next Steps

1. Apply SQL migration
2. Update UI code as described above
3. Test client creation with naming convention
4. Test file validation with auto-loaded convention
5. Update existing clients with appropriate naming conventions
