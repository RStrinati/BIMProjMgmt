# Custom Attributes Analysis Summary

## Overview
You have **6 unique custom attributes** across **4 ACC projects** in your `acc_data_schema` database.

## The Confusion: "Priority" Attribute Naming

### What You Were Looking For
You mentioned the "SINSW schools priority attribute" and confusion about naming.

### What Actually Exists
- **Attribute Name**: `Priority` (exactly as-is, not "SINSW Priority")
- **Project**: This only exists in ONE project: `A24AB8FE-A092-44D0-AB9C-B4754F58C71F` (Melrose Park HS)
- **Values**: Blocker, Critical, Major, Minor, Trivial
- **Current Implementation**: Already exposed in `vw_issues_expanded` as the `[Priority]` column

The confusion likely arose because:
- The attribute is called simply "Priority" (not "SINSW Priority")
- It only exists in the SINSW schools project (Melrose Park HS)
- You may have associated the project name with the attribute name

## Database Structure

### Three Key Tables

#### 1. `issues_custom_attributes_mappings` (DEFINITIONS)
Defines what custom attributes exist per project.
- **Key columns**: `id`, `bim360_project_id`, `title`, `data_type`
- **Example**: Project A has attribute "Priority" of type "list"

#### 2. `issues_custom_attribute_list_values` (LOOKUP VALUES)
For list-type attributes, defines the available options.
- **Key columns**: `attribute_mappings_id`, `list_id`, `list_value`
- **Example**: Priority options are "Major", "Minor", "Critical", etc.

#### 3. `issues_custom_attributes` (ACTUAL VALUES)
Stores the actual value for each issue.
- **Key columns**: `issue_id`, `attribute_mapping_id`, `attribute_value`
- **For list types**: `attribute_value` contains a UUID that maps to `list_id` in the list_values table
- **For text/number types**: `attribute_value` contains the direct value

## All Custom Attributes by Project

### Project 1: B6706F13-8A3A-4C98-9382-1148051059E7
**Attributes:**
- **Building Level** (list): In-ground, Level 00, Level 00 Mezz, Roof Level
- **Clash Level** (list): L1 - Critical, L2 - Important, L3 - Significant, L4 - Minor
- **Location** (list): Admin, Fire Pump Building, Gen Yard, MV Room, ROMP 01-04, Security Building, Site
- **Phase** (list): PHASE 01, PHASE 02, PHASE 03, PHASE 04

### Project 2: 057C6BB8-CF6E-449C-8A07-33C1AF69CDFF
**Attributes:** (Same as Project 1)
- **Building Level** (list)
- **Clash Level** (list)
- **Location** (list)
- **Phase** (list)

### Project 3: 648AFD41-A9BA-4909-8D4F-8F4477FE3AE8
**Attributes:**
- **Building Level** (list)
- **Clash Level** (list)
- **Location 01** (list) ← Note: Different name than other projects!
- **Phase** (list)

### Project 4: A24AB8FE-A092-44D0-AB9C-B4754F58C71F (SINSW - Melrose Park HS)
**Attributes:**
- **Priority** (list): Blocker, Critical, Major, Minor, Trivial
  - **Usage**: 360 issues (180 Major, 93 Minor, 67 Critical, 8 Blocker, 7 Trivial)

## Current Implementation

The view `vw_issues_expanded` currently has **ONLY** the Priority column:

```sql
-- 🔹 Custom Attributes Expanded - Priority extracted from JSON
(
    SELECT TOP 1 [value]
    FROM OPENJSON(ca.custom_attributes_json)
    WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
    WHERE [name] = 'Priority'
) AS [Priority]
```

This works because:
1. The `custom_attributes_json` field contains all custom attributes as a JSON array
2. OPENJSON extracts the value where `name = 'Priority'`

## How to Add More Custom Attribute Columns

### SQL to Add All 6 Custom Attributes

Add this to the SELECT clause of `vw_issues_expanded` (after the existing Priority column):

```sql
-- 🔹 Custom Attributes Expanded (All Attributes)
(
    SELECT TOP 1 [value]
    FROM OPENJSON(ca.custom_attributes_json)
    WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
    WHERE [name] = 'Building Level'
) AS [Building_Level],

(
    SELECT TOP 1 [value]
    FROM OPENJSON(ca.custom_attributes_json)
    WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
    WHERE [name] = 'Clash Level'
) AS [Clash_Level],

(
    SELECT TOP 1 [value]
    FROM OPENJSON(ca.custom_attributes_json)
    WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
    WHERE [name] = 'Location'
) AS [Location],

(
    SELECT TOP 1 [value]
    FROM OPENJSON(ca.custom_attributes_json)
    WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
    WHERE [name] = 'Location 01'
) AS [Location_01],

(
    SELECT TOP 1 [value]
    FROM OPENJSON(ca.custom_attributes_json)
    WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
    WHERE [name] = 'Phase'
) AS [Phase],

(
    SELECT TOP 1 [value]
    FROM OPENJSON(ca.custom_attributes_json)
    WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
    WHERE [name] = 'Priority'
) AS [Priority]
```

### Implementation Steps

1. **Edit the view**: `sql\update_vw_issues_expanded_with_priority.sql`
2. **Find the Priority column** (around line 251-257)
3. **Replace** the single Priority column with all 6 columns above
4. **Execute** the ALTER VIEW statement
5. **Test**: `SELECT TOP 10 * FROM vw_issues_expanded WHERE [Clash_Level] IS NOT NULL`

## Key Insights

### Naming Inconsistencies
- Most projects use "Location" but one uses "Location 01"
- Consider standardizing if possible in Autodesk ACC settings

### Attribute Distribution
- **Priority**: Only in 1 project (Melrose Park HS) - 360 issues using it
- **Building Level, Clash Level, Phase**: In 3 projects each
- **Location**: In 2 projects
- **Location 01**: In 1 project (different naming)

### Data Relationships
```
issues_custom_attributes (issue values)
    ├─→ attribute_mapping_id ─→ issues_custom_attributes_mappings (definitions)
    │                               └─→ title = "Priority"
    │                               └─→ data_type = "list"
    │
    └─→ attribute_value (UUID) ─→ issues_custom_attribute_list_values
                                    └─→ list_id (UUID match)
                                    └─→ list_value = "Major"
```

## Testing Queries

### Check if new columns work
```sql
SELECT 
    issue_id,
    title,
    project_name,
    Priority,
    Building_Level,
    Clash_Level,
    Location,
    Phase
FROM dbo.vw_issues_expanded
WHERE Priority IS NOT NULL 
   OR Building_Level IS NOT NULL
   OR Clash_Level IS NOT NULL
ORDER BY created_at DESC
```

### Count usage per attribute
```sql
SELECT 
    COUNT(CASE WHEN Priority IS NOT NULL THEN 1 END) AS Priority_Count,
    COUNT(CASE WHEN Building_Level IS NOT NULL THEN 1 END) AS Building_Level_Count,
    COUNT(CASE WHEN Clash_Level IS NOT NULL THEN 1 END) AS Clash_Level_Count,
    COUNT(CASE WHEN Location IS NOT NULL THEN 1 END) AS Location_Count,
    COUNT(CASE WHEN Phase IS NOT NULL THEN 1 END) AS Phase_Count
FROM dbo.vw_issues_expanded
```

## Tools Created

Three analysis tools were created in the `tools/` directory:

1. **`analyze_custom_attributes.py`** - Basic custom attributes analyzer
2. **`analyze_attribute_relationships.py`** - Deep dive into table relationships
3. **`custom_attributes_implementation_guide.py`** - Complete implementation guide (THIS REPORT)

Run any of these for updated analysis:
```bash
python tools\custom_attributes_implementation_guide.py
```

## Next Steps

1. **Decide which attributes to expose** - Do you want all 6, or just specific ones?
2. **Update the view** - Add the columns using the SQL above
3. **Update constants** - Add new column constants to `constants/schema.py`
4. **Update UI** - If needed, expose new columns in the Tkinter UI or analytics
5. **Document** - Update any API documentation or user guides

## Questions?

- **Q: Why is Priority only in one project?**  
  A: Each ACC project can define its own custom attributes. Only Melrose Park HS has configured "Priority".

- **Q: Can I rename attributes to be consistent?**  
  A: Attribute names are configured in Autodesk ACC. You'd need to change them there, not in the database.

- **Q: What if new attributes are added in ACC?**  
  A: They'll appear in `custom_attributes_json`. You'll need to re-run the analysis and add new columns.

- **Q: Should I use columns or JSON queries?**  
  A: Columns (OPENJSON) are better for filtering/sorting. JSON is better for flexibility. Current approach is good.
