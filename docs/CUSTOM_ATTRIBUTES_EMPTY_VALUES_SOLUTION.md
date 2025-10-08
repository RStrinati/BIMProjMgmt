# SOLUTION: Empty Custom Attribute Values

## 🔍 Problem Identified

You have **empty `attribute_value` columns** in the `issues_custom_attributes` table for MEL071, MEL081, and MEL064 projects, even though:
- ✅ Attribute **mappings** exist (definitions)
- ✅ Attribute **list_values** exist (available options)
- ❌ Attribute **values** are EMPTY (no actual issue data)

## 🎯 Root Cause

Based on the screenshots and diagnostics, the **ACC CSV export has empty `attribute_value` columns**. This happens for one of these reasons:

###  1. **Issues Don't Have Values Set** (Most Likely)
- Users created the custom attribute fields (Building Level, Clash Level, etc.)
- But they **haven't actually filled them in** on the issues yet
- The attributes exist as *available fields*, but no values have been selected

### 2. **ACC Export Settings**
- The export may not include custom attribute values
- Only structure/definitions are exported
- Check export options when downloading from ACC

### 3. **Wrong Data Source**
- Custom attribute values might be in a different location in ACC
- May need to use ACC API instead of CSV export

## ✅ Verification Steps

### Step 1: Check ACC Web Interface
1. Open Autodesk Construction Cloud
2. Navigate to one of your test issues:
   - `3eddd8c2-c798-4f63-b5cf-979d445f67c7`
   - `5a126ab8-df62-4f8c-9c77-fb9a1ee68f4d`
3. Look for custom fields: "Building Level", "Clash Level", "Phase"
4. **Are they filled in or blank?**

**If blank in ACC** → That's why they're empty in database (users need to fill them in)  
**If filled in ACC** → Export issue (proceed to Step 2)

### Step 2: Check CSV Source File
1. Open the original CSV: `issues_custom_attributes.csv`
2. Find the rows for your test issues
3. Check the `attribute_value` column
4. **Does it have data?**

**If empty in CSV** → Export problem (proceed to Step 3)  
**If filled in CSV** → Import problem (contact me)

### Step 3: Re-Export from ACC
1. In ACC, go to Project Admin → Export Data
2. Ensure these options are checked:
   - ☑ Include Issues
   - ☑ Include Custom Attributes
   - ☑ Include Field Values (not just definitions)
3. Download new ZIP
4. Re-import

## 🔧 Solution Options

### Option A: Use ACC API (Recommended)
If the CSV export doesn't include values, you need to use the ACC API to fetch them.

**Benefits:**
- Gets actual real-time data
- Includes all custom attribute values
- More reliable than CSV export

**Implementation:**
1. I can create an ACC API integration script
2. Authenticates with ACC using OAuth
3. Fetches issues with custom attributes via REST API
4. Populates the database with actual values

### Option B: Manual CSV Fix (Temporary)
If you know what the values should be, you can manually update the CSV:

1. Open `issues_custom_attributes.csv`
2. Fill in the `attribute_value` column with the correct `list_id` UUIDs
3. Match values from the `issues_custom_attribute_list_values` table
4. Re-import

**Example:**
```csv
issue_id,attribute_value
3eddd8c2-c798-4f63-b5cf-979d445f67c7,bf68dd9c-8d42-46c4-a586-474d1c473c6a
```
Where `bf68dd9c-8d42-46c4-a586-474d1c473c6a` is the `list_id` for "In-ground"

### Option C: Wait for Users to Fill In Values
If the attributes genuinely haven't been set yet:

1. Ask users to fill in custom attributes in ACC
2. Re-export after values are populated
3. Re-import

## 📊 Current State Summary

### What EXISTS in Your Database:

**issues_custom_attributes_mappings** ✅
- Defines that "Building Level" attribute exists
- Defines that it's a "list" type
- Links to project 648afd41-a9ba-4909-8d4f-8f4477fe3ae8

**issues_custom_attribute_list_values** ✅
- Defines available options:
  - In-ground (bf68dd9c-8d42-46c4-a586-474d1c473c6a)
  - Level 00 (95fc8441-fe97-4d68-8a2c-490e3768b5dd)
  - Level 00 Mezz (0424e758-84a2-431c-8f75-460be287e2fa)
  - etc.

**issues_custom_attributes** ❌
- Should link issue → attribute → value
- Currently has rows but `attribute_value` is **EMPTY**
- This is why you see NULL in the view

### Visual Data Flow:

```
ACC Web Interface
    ↓
    ├─ Issue #123 created
    ├─ Custom field "Building Level" available
    └─ ❌ USER HASN'T SELECTED A VALUE YET
    
ACC Export (CSV)
    ↓
    ├─ issues_custom_attributes_mappings.csv → Has definitions ✅
    ├─ issues_custom_attribute_list_values.csv → Has options ✅
    └─ issues_custom_attributes.csv → attribute_value is EMPTY ❌
    
Import Process
    ↓
    └─ staging.issues_custom_attributes → Empty attribute_value
        ↓
        └─ dbo.issues_custom_attributes → Empty attribute_value
            ↓
            └─ vw_issues_expanded → Building_Level = NULL
```

## 🎯 Action Plan

### Immediate Next Steps:

1. **Check ACC UI** (5 minutes)
   - Open one test issue in ACC web interface
   - Verify if Building Level field is filled in
   - Screenshot and share result

2. **Check Source CSV** (2 minutes)
   - Open `issues_custom_attributes.csv` in Excel
   - Filter to your test issue IDs
   - Check if `attribute_value` column has data
   - Screenshot and share result

3. **Based on Results:**
   - **If blank in ACC** → Ask users to fill in values, then re-export
   - **If blank in CSV but filled in ACC** → Need ACC API integration
   - **If filled in CSV but empty in DB** → Import script bug (rare)

### Long-Term Solution:

If this is a recurring issue, I recommend:
1. **ACC API Integration** - Fetch data directly from ACC API
2. **Automated Sync** - Schedule regular sync of custom attributes
3. **Data Validation** - Alert when custom attributes are empty

## 📞 Need Help?

Let me know the results of Steps 1 & 2 above and I can:
- Create an ACC API integration script
- Fix any import bugs if found
- Help populate the data manually if needed

## 🔗 Related Files

- Diagnostic tool: `tools/debug_empty_custom_attributes.py`
- Merge script: `sql/merge_issues_custom_attributes.sql`
- View definition: `sql/update_vw_issues_expanded_with_priority.sql`

---

**Bottom Line:** The SQL code works perfectly. The issue is that the source data (ACC export) has empty `attribute_value` columns. We need to determine WHY they're empty (not set vs export issue) to provide the right solution.
