# Quick Start: Naming Conventions Integration

## 1. Apply Database Migration (Required)

```powershell
python tools/apply_naming_convention_migration.py
```

## 2. Test the Integration

```python
# Test in Python console
from services.naming_convention_service import get_available_conventions, get_convention_schema

# Should return [('AWS', 'AWS'), ('SINSW', 'SINSW')]
print(get_available_conventions())

# Load AWS schema
aws_schema = get_convention_schema('AWS')
print(aws_schema['institution'])  # 'AWS'
print(aws_schema['standard'])      # 'ISO 19650'
```

## 3. Update UI (Manual - see full guide)

### Location 1: `phase1_enhanced_ui.py` → `show_new_client_dialog()`

Add after postcode field (row 7):

```python
# Naming Convention
ttk.Label(fields_frame, text="Naming Convention:").grid(row=8, column=0, sticky="w", pady=5)
client_vars['naming_convention'] = tk.StringVar()

from services.naming_convention_service import get_available_conventions
conventions = get_available_conventions()
convention_values = [""] + [f"{code} - {name}" for code, name in conventions]

naming_combo = ttk.Combobox(fields_frame, textvariable=client_vars['naming_convention'], 
                             values=convention_values, state='readonly', width=38)
naming_combo.grid(row=8, column=1, sticky="ew", pady=5)
```

Update `save_client()`:

```python
# Extract naming convention code
naming_conv_value = client_vars['naming_convention'].get().strip()
naming_conv_code = naming_conv_value.split(' - ')[0] if naming_conv_value else None

client_data = {
    # ... existing fields ...
    'naming_convention': naming_conv_code  # ADD THIS
}
```

## 4. Usage

1. **Create Client** → Select naming convention (AWS/SINSW)
2. **Create Project** → Assign to client
3. **Validate Files** → System auto-loads client's convention

## Files Reference

| Purpose | Location |
|---------|----------|
| Full Documentation | `docs/NAMING_CONVENTION_INTEGRATION.md` |
| Summary | `NAMING_CONVENTION_SUMMARY.md` |
| Migration Script | `tools/apply_naming_convention_migration.py` |
| Service Code | `services/naming_convention_service.py` |
| Schema Files | `constants/naming_conventions/` |

## Adding New Conventions

1. Create `constants/naming_conventions/NEWCODE.json`
2. Follow AWS.json or SINSW.json structure
3. Update database constraint to include new code
4. Restart application

That's it! See full documentation for advanced usage.
