# Custom Attributes - Quick Reference

## 📊 Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│  AUTODESK CONSTRUCTION CLOUD (ACC)                                   │
│  Project Settings → Custom Attributes Configuration                  │
└────────────────────────┬─────────────────────────────────────────────┘
                         │ Import via ACC Handler
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  acc_data_schema DATABASE                                            │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │  issues_custom_attributes_mappings (DEFINITIONS)        │        │
│  │  ──────────────────────────────────────────────────     │        │
│  │  • id (PK)                                              │        │
│  │  • bim360_project_id ──────┐                            │        │
│  │  • title: "Priority"       │ Different per project      │        │
│  │  • data_type: "list"       │                            │        │
│  └────────┬───────────────────┴────────────────────────────┘        │
│           │ FK: attribute_mapping_id                                 │
│           │                                                          │
│  ┌────────▼──────────────────────────────────────────────┐          │
│  │  issues_custom_attribute_list_values (OPTIONS)        │          │
│  │  ─────────────────────────────────────────────────    │          │
│  │  • attribute_mappings_id (FK)                         │          │
│  │  • list_id: "1958133f-d8c4-..." (UUID)               │          │
│  │  • list_value: "Major"                                │          │
│  └────────┬──────────────────────────────────────────────┘          │
│           │ Match on list_id                                         │
│           │                                                          │
│  ┌────────▼──────────────────────────────────────────────┐          │
│  │  issues_custom_attributes (ACTUAL VALUES)             │          │
│  │  ────────────────────────────────────────────────     │          │
│  │  • issue_id (which issue)                             │          │
│  │  • attribute_mapping_id (which attribute)             │          │
│  │  • attribute_value: "1958133f-..." (UUID or direct)   │          │
│  └───────────────────────────────────────────────────────┘          │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ JOIN in view
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  vw_issues_expanded (MATERIALIZED VIEW)                              │
│  ────────────────────────────────────────────────────────────────    │
│  • issue_id, title, status, ...                                      │
│  • custom_attributes_json (full JSON array)                          │
│  • Priority (extracted column) ──┐                                   │
│  • Building_Level (extracted)    │ OPENJSON extracts                 │
│  • Clash_Level (extracted)       │ from JSON to columns              │
│  • Location (extracted)          │                                   │
│  • Phase (extracted)            ─┘                                   │
└──────────────────────────────────────────────────────────────────────┘
```

## 🗂️ Projects and Their Custom Attributes

| Project ID (truncated) | Attributes |
|------------------------|------------|
| **B6706F13** | Building Level, Clash Level, Location, Phase |
| **057C6BB8** | Building Level, Clash Level, Location, Phase |
| **648AFD41** | Building Level, Clash Level, **Location 01**, Phase |
| **A24AB8FE** (SINSW) | **Priority** ⭐ |

⭐ = Currently exposed in view

## 📋 All Attribute Values

### Priority (Project: A24AB8FE - Melrose Park HS)
- **Blocker** (8 issues)
- **Critical** (67 issues)
- **Major** (180 issues) ← Most common
- **Minor** (93 issues)
- **Trivial** (7 issues)

### Building Level (3 projects)
- In-ground
- Level 00
- Level 00 Mezz
- Roof Level

### Clash Level (3 projects)
- L1 - Critical
- L2 - Important
- L3 - Significant
- L4 - Minor

### Location / Location 01 (varies)
- Admin
- Fire Pump Building
- Gen Yard
- MV Room
- ROMP 01, 02, 03, 04
- Security Building
- Site

### Phase (3 projects)
- PHASE 01
- PHASE 02
- PHASE 03
- PHASE 04

## 🔧 How to Add a New Custom Attribute Column

### Pattern
```sql
(
    SELECT TOP 1 [value]
    FROM OPENJSON(ca.custom_attributes_json)
    WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
    WHERE [name] = 'AttributeNameHere'
) AS [Column_Name]
```

### Example: Add "Clash Level"
```sql
(
    SELECT TOP 1 [value]
    FROM OPENJSON(ca.custom_attributes_json)
    WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
    WHERE [name] = 'Clash Level'
) AS [Clash_Level]
```

### Where to Add
File: `sql/update_vw_issues_expanded_with_priority.sql`  
Location: Around line 251-257, after the `custom_attributes_json` column

## 🎯 Common Queries

### Get all issues with Priority
```sql
SELECT issue_id, title, Priority
FROM vw_issues_expanded
WHERE Priority IS NOT NULL
ORDER BY 
    CASE Priority
        WHEN 'Blocker' THEN 1
        WHEN 'Critical' THEN 2
        WHEN 'Major' THEN 3
        WHEN 'Minor' THEN 4
        WHEN 'Trivial' THEN 5
    END
```

### Count by custom attribute
```sql
SELECT 
    Priority,
    COUNT(*) AS issue_count
FROM vw_issues_expanded
WHERE Priority IS NOT NULL
GROUP BY Priority
ORDER BY issue_count DESC
```

### Get raw custom attributes JSON
```sql
SELECT 
    issue_id,
    title,
    custom_attributes_json
FROM vw_issues_expanded
WHERE custom_attributes_json IS NOT NULL
```

## ⚠️ Important Notes

1. **Naming Confusion**: The attribute is called "Priority", NOT "SINSW Priority". It just happens to only exist in the SINSW project.

2. **Different Names, Same Concept**: "Location" vs "Location 01" are the same type of attribute but named differently per project.

3. **NULL Values**: If a project doesn't have an attribute, the column will be NULL for those issues.

4. **Performance**: OPENJSON is reasonably fast, but if you query millions of rows frequently, consider a computed column or indexed view.

5. **Future Attributes**: When new custom attributes are added in ACC, you'll need to:
   - Re-import ACC data
   - Re-run analysis: `python tools\custom_attributes_implementation_guide.py`
   - Add new columns to the view

## 📞 Related Files

- **Main View**: `sql/update_vw_issues_expanded_with_priority.sql`
- **Schema Constants**: `constants/schema.py` (add new column constants here)
- **Analysis Tools**: 
  - `tools/analyze_custom_attributes.py`
  - `tools/analyze_attribute_relationships.py`
  - `tools/custom_attributes_implementation_guide.py`
- **Full Documentation**: `docs/CUSTOM_ATTRIBUTES_ANALYSIS.md`
