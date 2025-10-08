# SUMMARY: Custom Attributes Analysis & Implementation

## What You Asked For
You wanted to understand custom attributes across different projects and add columns like the "SINSW schools priority attribute" to your `issues_expanded` view.

## What We Found

### ✅ The "Confusion" Clarified
- **The attribute is called simply "Priority"** (not "SINSW Priority")
- It **only exists in ONE project**: Melrose Park HS (SINSW schools project)
- ACC Project ID: `A24AB8FE-A092-44D0-AB9C-B4754F58C71F`
- You likely associated the project name (SINSW) with the attribute name

### 📊 All Custom Attributes Found

| Attribute Name | Type | # Projects | Projects Using It | Values |
|----------------|------|------------|-------------------|---------|
| **Priority** | list | 1 | SINSW Melrose Park HS | Blocker, Critical, Major, Minor, Trivial |
| **Building Level** | list | 3 | Multiple | In-ground, Level 00, Level 00 Mezz, Roof Level |
| **Clash Level** | list | 3 | Multiple | L1-Critical, L2-Important, L3-Significant, L4-Minor |
| **Location** | list | 2 | Multiple | Admin, Fire Pump, Gen Yard, ROMP 01-04, etc. |
| **Location 01** | list | 1 | One project | Same values as Location |
| **Phase** | list | 3 | Multiple | PHASE 01, 02, 03, 04 |

### 🎯 Current Implementation
The view `vw_issues_expanded` **already has** the Priority column:
```sql
(
    SELECT TOP 1 [value]
    FROM OPENJSON(ca.custom_attributes_json)
    WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
    WHERE [name] = 'Priority'
) AS [Priority]
```

**Usage**: 360 issues in Melrose Park HS use Priority
- Major: 180 issues
- Minor: 93 issues  
- Critical: 67 issues
- Blocker: 8 issues
- Trivial: 7 issues

## 🔧 How to Add the Other 5 Custom Attributes

### Step 1: Edit the View
File: `sql/update_vw_issues_expanded_with_priority.sql`

### Step 2: Find the Priority Column
Around line 251-257, you'll find the existing Priority column extraction.

### Step 3: Replace with All 6 Attributes
Use the SQL code from: `sql/add_custom_attribute_columns.sql`

This will add:
- `[Building_Level]`
- `[Clash_Level]`
- `[Location]`
- `[Location_01]`
- `[Phase]`
- `[Priority]` (already exists, but included for completeness)

### Step 4: Execute
Run the full `ALTER VIEW` statement to update the view.

### Step 5: Test
```sql
SELECT TOP 10 
    issue_id, 
    title, 
    Priority, 
    Clash_Level, 
    Building_Level,
    Phase
FROM vw_issues_expanded
WHERE Priority IS NOT NULL OR Clash_Level IS NOT NULL
```

## 📁 Files Created

### Documentation
1. **`docs/CUSTOM_ATTRIBUTES_ANALYSIS.md`** - Complete detailed analysis
2. **`docs/CUSTOM_ATTRIBUTES_QUICK_REF.md`** - Quick reference guide with diagrams

### SQL Scripts
3. **`sql/add_custom_attribute_columns.sql`** - Ready-to-use SQL for updating the view

### Analysis Tools (in tools/)
4. **`analyze_custom_attributes.py`** - Basic analyzer (already existed)
5. **`analyze_attribute_relationships.py`** - Deep relationship analysis (new)
6. **`custom_attributes_implementation_guide.py`** - Full implementation guide (new)

## 🗂️ Database Structure Explained

### Three Tables Work Together:

```
issues_custom_attributes_mappings
  ↓ Defines what attributes exist per project
  ↓ (e.g., "Priority" attribute exists for Project A)
  
issues_custom_attribute_list_values  
  ↓ Defines available values for list-type attributes
  ↓ (e.g., Priority can be: Major, Minor, Critical, etc.)
  
issues_custom_attributes
  ↓ Stores actual values for each issue
  ↓ (e.g., Issue #123 has Priority = "Major")
  
vw_issues_expanded
  → Joins all together and exposes as columns
```

### The Join Logic:
1. `issues_custom_attributes.attribute_mapping_id` → `issues_custom_attributes_mappings.id`
2. `issues_custom_attributes.attribute_value` (UUID) → `issues_custom_attribute_list_values.list_id`
3. Result: Get human-readable value like "Major" instead of UUID

## 🚨 Key Insights

### Naming Inconsistencies
- **"Location" vs "Location 01"**: Same concept, different names across projects
- This is configured in ACC, not the database

### NULL Values Are Normal
- If a project doesn't define an attribute, the column will be NULL
- Example: Priority is NULL for all projects except Melrose Park HS

### Performance Considerations
- OPENJSON is fast enough for current dataset
- If you have millions of rows and performance issues, consider:
  - Computed columns with indexing
  - Separate pivoted custom_attributes table

## 🎬 Next Steps

### Immediate Actions
1. ✅ **Review** the analysis documents created
2. ⚠️ **Decide** which custom attributes you want to expose
3. 🔧 **Update** the view using `sql/add_custom_attribute_columns.sql`
4. ✅ **Test** with the provided queries
5. 📝 **Update** `constants/schema.py` with new column constants

### Future Maintenance
- When new custom attributes are added in ACC:
  1. Re-import ACC data
  2. Run: `python tools\custom_attributes_implementation_guide.py`
  3. Add new columns to the view following the same pattern

## 📞 Tools to Re-Run Analysis Anytime

```bash
# Full implementation guide with all details
python tools\custom_attributes_implementation_guide.py

# Deep relationship analysis
python tools\analyze_attribute_relationships.py

# Basic custom attributes overview
python tools\analyze_custom_attributes.py
```

## ❓ Questions Answered

**Q: Why is it called "Priority" and not "SINSW Priority"?**  
A: The attribute is named exactly "Priority" in ACC. It's only used in the SINSW project, which may have caused the confusion.

**Q: Can I rename attributes to be consistent across projects?**  
A: Attribute names are configured in Autodesk ACC project settings. You'd need to change them there, not in the database.

**Q: Do I need to add ALL 6 attributes?**  
A: No, add only what you need. Priority is already there. Add others as required.

**Q: What if the schema changes?**  
A: Re-run the analysis tools. They'll detect new attributes automatically.

## 🎉 Summary

- ✅ Found **6 unique custom attributes** across **4 projects**
- ✅ **Priority already exists** in your view (SINSW project only)
- ✅ Identified **naming confusion** ("Priority" not "SINSW Priority")
- ✅ Created **tools to analyze** attributes anytime
- ✅ Provided **ready-to-use SQL** to add all attributes
- ✅ Documented **complete structure** and relationships

**You're all set!** Review the docs and implement as needed.
