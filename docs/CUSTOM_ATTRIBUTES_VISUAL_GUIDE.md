# Custom Attributes Visual Guide

## 🎯 The Big Picture

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  4 ACC PROJECTS with 6 UNIQUE CUSTOM ATTRIBUTES                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌─────────────────────────────────────────────────────────────────┐
│  PROJECT 1: B6706F13 (Unknown)                                  │
├─────────────────────────────────────────────────────────────────┤
│  ✓ Building Level (4 values)                                    │
│  ✓ Clash Level (4 values)                                       │
│  ✓ Location (10 values)                                         │
│  ✓ Phase (4 values)                                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PROJECT 2: 057C6BB8 (Unknown)                                  │
├─────────────────────────────────────────────────────────────────┤
│  ✓ Building Level (4 values)                                    │
│  ✓ Clash Level (4 values)                                       │
│  ✓ Location (10 values)                                         │
│  ✓ Phase (4 values)                                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PROJECT 3: 648AFD41 (Unknown)                                  │
├─────────────────────────────────────────────────────────────────┤
│  ✓ Building Level (4 values)                                    │
│  ✓ Clash Level (4 values)                                       │
│  ✓ Location 01 (10 values) ← Different name!                    │
│  ✓ Phase (4 values)                                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PROJECT 4: A24AB8FE (SINSW - Melrose Park HS) ⭐              │
├─────────────────────────────────────────────────────────────────┤
│  ✓ Priority (5 values) ← THE ATTRIBUTE YOU ASKED ABOUT!         │
│    • Blocker (8 issues)                                         │
│    • Critical (67 issues)                                       │
│    • Major (180 issues) ← Most common                           │
│    • Minor (93 issues)                                          │
│    • Trivial (7 issues)                                         │
└─────────────────────────────────────────────────────────────────┘
```

## 🔍 How One Issue's Custom Attributes Flow Through the System

```
┌─────────────────────────────────────────────────────────────────┐
│  EXAMPLE: Issue "ARC v. STR - Beam clash" in Melrose Park HS   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  issues_custom_attributes_mappings                              │
│  (What attributes exist for this project?)                      │
├─────────────────────────────────────────────────────────────────┤
│  id: 83A41E34-74F3-4A39-83C6-E03CC3387947                       │
│  bim360_project_id: A24AB8FE-A092-44D0-AB9C-B4754F58C71F        │
│  title: "Priority"                                              │
│  data_type: "list"                                              │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  issues_custom_attribute_list_values                            │
│  (What are the possible values?)                                │
├─────────────────────────────────────────────────────────────────┤
│  attribute_mappings_id: 83A41E34-74F3-4A39-83C6-E03CC3387947    │
│  list_id: 1958133F-D8C4-4B46-9655-F957F5FB621C ← UUID           │
│  list_value: "Major" ← Human-readable                           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  issues_custom_attributes                                       │
│  (What is THIS issue's value?)                                  │
├─────────────────────────────────────────────────────────────────┤
│  issue_id: 75D29CA6-EC38-461E-86D8-FACC25AD48B9                 │
│  attribute_mapping_id: 83A41E34-74F3-4A39-83C6-E03CC3387947     │
│  attribute_value: "1958133F-D8C4-4B46-9655-F957F5FB621C"        │
│                    ↑ This UUID matches list_id above!           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  vw_issues_expanded                                             │
│  (Final view with joined data)                                  │
├─────────────────────────────────────────────────────────────────┤
│  issue_id: 75D29CA6-EC38-461E-86D8-FACC25AD48B9                 │
│  title: "ARC v. STR - Beam clash"                               │
│  Priority: "Major" ← Human-readable value exposed as column!    │
│  custom_attributes_json: [{"name":"Priority","value":"Major"}]  │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Attribute Distribution Across Projects

```
                    Projects Using This Attribute
                    ┌───┬───┬───┬───┐
Attribute           │ 1 │ 2 │ 3 │ 4 │  Values
────────────────────┼───┼───┼───┼───┼──────────────────────────
Building Level      │ ✓ │ ✓ │ ✓ │   │  In-ground, Level 00,
                    │   │   │   │   │  Level 00 Mezz, Roof
────────────────────┼───┼───┼───┼───┼──────────────────────────
Clash Level         │ ✓ │ ✓ │ ✓ │   │  L1-Critical, L2-Important
                    │   │   │   │   │  L3-Significant, L4-Minor
────────────────────┼───┼───┼───┼───┼──────────────────────────
Location            │ ✓ │ ✓ │   │   │  Admin, Fire Pump, Gen Yard
                    │   │   │   │   │  MV Room, ROMP 01-04, etc.
────────────────────┼───┼───┼───┼───┼──────────────────────────
Location 01         │   │   │ ✓ │   │  Same values as Location
                    │   │   │   │   │  (but different name)
────────────────────┼───┼───┼───┼───┼──────────────────────────
Phase               │ ✓ │ ✓ │ ✓ │   │  PHASE 01, 02, 03, 04
────────────────────┼───┼───┼───┼───┼──────────────────────────
Priority ⭐         │   │   │   │ ✓ │  Blocker, Critical, Major
                    │   │   │   │   │  Minor, Trivial
────────────────────┴───┴───┴───┴───┴──────────────────────────

⭐ = Already exposed in vw_issues_expanded
```

## 🎨 Priority Attribute Breakdown (SINSW Project Only)

```
Priority Distribution (360 total issues)

Blocker    ▓▓░░░░░░░░░░░░░░░░░░  8 issues (2%)
Critical   ▓▓▓▓▓▓▓▓▓░░░░░░░░░░░  67 issues (19%)
Major      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  180 issues (50%) ← Most common
Minor      ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░  93 issues (26%)
Trivial    ▓░░░░░░░░░░░░░░░░░░░  7 issues (2%)
```

## 🔄 Current vs. Proposed View Columns

### Current Implementation (vw_issues_expanded)
```
┌──────────────────────────────────────────────────────────────┐
│  Standard Columns                                            │
│  • issue_id, title, status, due_date, description, ...       │
├──────────────────────────────────────────────────────────────┤
│  Custom Attributes                                           │
│  • custom_attributes_json (full JSON)                        │
│  • Priority (extracted) ← Only ONE attribute exposed         │
└──────────────────────────────────────────────────────────────┘
```

### Proposed Implementation (with all attributes)
```
┌──────────────────────────────────────────────────────────────┐
│  Standard Columns                                            │
│  • issue_id, title, status, due_date, description, ...       │
├──────────────────────────────────────────────────────────────┤
│  Custom Attributes                                           │
│  • custom_attributes_json (full JSON)                        │
│  • Building_Level (extracted)    ← NEW                       │
│  • Clash_Level (extracted)       ← NEW                       │
│  • Location (extracted)          ← NEW                       │
│  • Location_01 (extracted)       ← NEW                       │
│  • Phase (extracted)             ← NEW                       │
│  • Priority (extracted)          ← EXISTING                  │
└──────────────────────────────────────────────────────────────┘
```

## 🛠️ Implementation Code Structure

### How OPENJSON Extraction Works

```sql
-- Pattern for each attribute
(
    SELECT TOP 1 [value]
    FROM OPENJSON(ca.custom_attributes_json)
    WITH ([name] NVARCHAR(100), [value] NVARCHAR(MAX))
    WHERE [name] = 'Priority'  ← Exact attribute name from ACC
) AS [Priority]                ← Column name in view
```

### What the JSON Looks like
```json
[
  {
    "name": "Priority",
    "value": "Major",
    "type": "list",
    "is_required": false,
    "created_at": "2025-09-09T04:07:00.143"
  }
]
```

### How OPENJSON Extracts It
```
OPENJSON parses the array
  → WITH clause defines structure
    → WHERE filters to specific attribute name
      → TOP 1 gets the first (only) match
        → Result: "Major" extracted to [Priority] column
```

## 🎯 Query Examples After Implementation

### Example 1: Get all high-priority clash issues
```sql
SELECT 
    issue_id,
    title,
    Priority,
    Clash_Level,
    project_name
FROM vw_issues_expanded
WHERE 
    Priority IN ('Blocker', 'Critical')
    AND Clash_Level IN ('L1 - Critical', 'L2 - Important')
ORDER BY 
    CASE Priority WHEN 'Blocker' THEN 1 WHEN 'Critical' THEN 2 END,
    created_at DESC
```

### Example 2: Issues by phase and location
```sql
SELECT 
    Phase,
    COALESCE(Location, Location_01) AS LocationValue,
    COUNT(*) AS issue_count
FROM vw_issues_expanded
WHERE Phase IS NOT NULL
GROUP BY Phase, COALESCE(Location, Location_01)
ORDER BY Phase, issue_count DESC
```

### Example 3: Dashboard metrics
```sql
SELECT 
    project_name,
    COUNT(*) AS total_issues,
    COUNT(Priority) AS has_priority,
    COUNT(Clash_Level) AS has_clash_level,
    COUNT(Phase) AS has_phase,
    SUM(CASE WHEN Priority IN ('Blocker','Critical') THEN 1 ELSE 0 END) AS critical_issues
FROM vw_issues_expanded
GROUP BY project_name
```

## 📋 Implementation Checklist

- [ ] 1. Review `docs/CUSTOM_ATTRIBUTES_ANALYSIS.md` (detailed guide)
- [ ] 2. Review `docs/CUSTOM_ATTRIBUTES_QUICK_REF.md` (quick reference)
- [ ] 3. Review `docs/CUSTOM_ATTRIBUTES_SUMMARY.md` (executive summary)
- [ ] 4. Review `docs/CUSTOM_ATTRIBUTES_VISUAL_GUIDE.md` (this file)
- [ ] 5. Open `sql/add_custom_attribute_columns.sql` (ready-to-use SQL)
- [ ] 6. Edit `sql/update_vw_issues_expanded_with_priority.sql`
- [ ] 7. Replace Priority section with all 6 attributes
- [ ] 8. Execute ALTER VIEW statement
- [ ] 9. Run test queries from `sql/add_custom_attribute_columns.sql`
- [ ] 10. Update `constants/schema.py` with new column constants
- [ ] 11. Update any UI code to display new columns
- [ ] 12. Update documentation/user guides as needed

## 🎓 Key Takeaways

1. **"Priority" is the exact attribute name** - not "SINSW Priority"
2. **It only exists in ONE project** - Melrose Park HS (SINSW)
3. **5 other attributes exist** across 3 other projects
4. **NULL values are normal** - attributes are project-specific
5. **OPENJSON extracts JSON to columns** - already working for Priority
6. **Same pattern for all attributes** - easy to add more

## 🚀 You're Ready!

Everything you need is documented. The SQL is ready. The tools are built.  
Just follow the checklist above and you'll have all custom attributes exposed!

---

**Questions?** Re-run the analysis tools anytime:
```bash
python tools\custom_attributes_implementation_guide.py
```
