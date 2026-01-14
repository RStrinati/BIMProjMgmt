# Custom Attributes - Documentation Index

## 📚 Quick Navigation

### Start Here
👉 **[SUMMARY](CUSTOM_ATTRIBUTES_SUMMARY.md)** - Start here for the executive summary

### Detailed Guides
1. **[ANALYSIS](CUSTOM_ATTRIBUTES_ANALYSIS.md)** - Complete detailed analysis with all findings
2. **[QUICK REFERENCE](CUSTOM_ATTRIBUTES_QUICK_REF.md)** - Quick lookup guide with queries
3. **[VISUAL GUIDE](CUSTOM_ATTRIBUTES_VISUAL_GUIDE.md)** - Diagrams and visual explanations

### Implementation
📄 **[SQL Script](../sql/add_custom_attribute_columns.sql)** - Ready-to-use SQL to update your view

### Tools
Located in `tools/` directory:
- `analyze_custom_attributes.py` - Basic analyzer
- `analyze_attribute_relationships.py` - Deep relationship analysis  
- `custom_attributes_implementation_guide.py` - Full guide generator

---

## 🎯 Your Question Answered

**You asked:** "I need to identify different custom attributes per project and add a column to my issues_expanded view like the SINSW schools priority attribute. I think there is confusion as they are not named the same"

**Answer:** 
- ✅ The attribute is called **"Priority"** (exactly, not "SINSW Priority")
- ✅ It **only exists** in the SINSW Melrose Park HS project
- ✅ The **Priority column already exists** in your view!
- ✅ We found **5 additional custom attributes** you can add
- ✅ The "confusion" was associating the project name with the attribute name

---

## 📋 What We Found

### 6 Unique Custom Attributes

| Attribute | Projects | Currently in View? | Action Needed |
|-----------|----------|-------------------|---------------|
| **Priority** | 1 (SINSW only) | ✅ Yes | None - already there |
| Building Level | 3 | ❌ No | Add if needed |
| Clash Level | 3 | ❌ No | Add if needed |
| Location | 2 | ❌ No | Add if needed |
| Location 01 | 1 | ❌ No | Add if needed |
| Phase | 3 | ❌ No | Add if needed |

### Database Structure

Three tables work together:
1. **`issues_custom_attributes_mappings`** - Defines attributes per project
2. **`issues_custom_attribute_list_values`** - Defines values for list-type attributes
3. **`issues_custom_attributes`** - Stores actual values per issue

---

## 🚀 Quick Start Guide

### 1️⃣ Understand the Current State
Read: [SUMMARY.md](CUSTOM_ATTRIBUTES_SUMMARY.md)

### 2️⃣ See How It Works
Read: [VISUAL_GUIDE.md](CUSTOM_ATTRIBUTES_VISUAL_GUIDE.md)

### 3️⃣ Implement (If Needed)
1. Open: `sql/add_custom_attribute_columns.sql`
2. Copy the SQL section for attributes you want
3. Edit: `sql/update_vw_issues_expanded_with_priority.sql`
4. Replace the Priority section with all 6 attributes
5. Execute the ALTER VIEW statement
6. Test with provided queries

### 4️⃣ Reference Material
Bookmark: [QUICK_REF.md](CUSTOM_ATTRIBUTES_QUICK_REF.md)

---

## 📊 Documents Overview

### CUSTOM_ATTRIBUTES_SUMMARY.md
**Best for:** Quick understanding and next steps  
**Contains:**
- What was found
- What the confusion was about
- What's already implemented
- What you can add
- Action items

### CUSTOM_ATTRIBUTES_ANALYSIS.md
**Best for:** Deep understanding and complete details  
**Contains:**
- Complete database structure explanation
- All attributes by project
- All list values
- Implementation steps
- Testing queries
- Key insights

### CUSTOM_ATTRIBUTES_QUICK_REF.md
**Best for:** Day-to-day reference  
**Contains:**
- Data flow diagram
- All attribute values
- Quick implementation pattern
- Common queries
- Important notes

### CUSTOM_ATTRIBUTES_VISUAL_GUIDE.md
**Best for:** Visual learners and presentations  
**Contains:**
- Visual diagrams of projects and attributes
- Flow charts showing data relationships
- Distribution charts
- Code structure visualizations
- Before/after comparisons

---

## 🛠️ Tools You Can Run

### Full Implementation Guide
```bash
python tools\custom_attributes_implementation_guide.py
```
Generates complete report with:
- All projects and their attributes
- All unique attribute names
- SQL to add columns
- List values reference
- Current implementation status
- Summary and recommendations

### Deep Relationship Analysis
```bash
python tools\analyze_attribute_relationships.py
```
Shows:
- Table structure overview
- All attribute definitions by project
- List values for each attribute
- Actual usage by project
- Sample values with resolution
- Multi-project attribute analysis

### Basic Attributes Analyzer
```bash
python tools\analyze_custom_attributes.py
```
Provides:
- Custom attributes found
- Sample values
- SQL view generation

---

## 💡 Key Insights

### The "Naming Confusion"
- Attribute name: **"Priority"** (not "SINSW Priority")
- Only exists in: **SINSW Melrose Park HS project**
- Confusion source: Associating project name with attribute name

### Attribute Inconsistencies
- **"Location" vs "Location 01"**: Same concept, different naming
- Configured in ACC, not the database
- Consider standardizing in ACC if possible

### NULL Values
- Attributes are **project-specific**
- If a project doesn't have an attribute, the column will be **NULL**
- This is **expected behavior**

### Current Implementation
- **Priority already works!** - No action needed for that one
- Extracted from `custom_attributes_json` using OPENJSON
- Same pattern can be used for all 6 attributes

---

## 📞 Support & Maintenance

### Re-run Analysis Anytime
When new custom attributes are added in ACC:
1. Re-import ACC data
2. Run: `python tools\custom_attributes_implementation_guide.py`
3. Check for new attributes
4. Add new columns following the same pattern

### Update Process
1. **Schema changes detected** → Run analysis tools
2. **New attributes found** → Update view with new columns
3. **Update constants** → Add to `constants/schema.py`
4. **Update UI** → Expose in application as needed
5. **Update docs** → Keep documentation current

---

## ✅ Implementation Checklist

- [ ] Understand the current state (Priority already exists)
- [ ] Review all 6 custom attributes found
- [ ] Decide which attributes to expose in view
- [ ] Copy SQL from `sql/add_custom_attribute_columns.sql`
- [ ] Edit `sql/update_vw_issues_expanded_with_priority.sql`
- [ ] Execute ALTER VIEW statement
- [ ] Test with provided queries
- [ ] Update `constants/schema.py`
- [ ] Update UI components (if needed)
- [ ] Update user documentation (if needed)

---

## 🎓 Learning Path

### Beginner
1. Read [SUMMARY.md](CUSTOM_ATTRIBUTES_SUMMARY.md)
2. Review [VISUAL_GUIDE.md](CUSTOM_ATTRIBUTES_VISUAL_GUIDE.md)
3. Understand the Priority column already works

### Intermediate
1. Read [ANALYSIS.md](CUSTOM_ATTRIBUTES_ANALYSIS.md)
2. Understand the 3-table structure
3. Review the OPENJSON extraction pattern

### Advanced
1. Run all three analysis tools
2. Review raw SQL in `sql/update_vw_issues_expanded_with_priority.sql`
3. Understand the full view construction
4. Consider performance optimizations

---

## 📁 File Locations

### Documentation (docs/)
- `CUSTOM_ATTRIBUTES_INDEX.md` ← You are here
- `CUSTOM_ATTRIBUTES_SUMMARY.md`
- `CUSTOM_ATTRIBUTES_ANALYSIS.md`
- `CUSTOM_ATTRIBUTES_QUICK_REF.md`
- `CUSTOM_ATTRIBUTES_VISUAL_GUIDE.md`

### SQL Scripts (sql/)
- `add_custom_attribute_columns.sql` - Ready to use
- `update_vw_issues_expanded_with_priority.sql` - Main view (to edit)

### Analysis Tools (tools/)
- `custom_attributes_implementation_guide.py`
- `analyze_attribute_relationships.py`
- `analyze_custom_attributes.py`

### Schema Constants (constants/)
- `schema.py` - Update with new column constants after implementation

---

## 🎉 You're All Set!

Everything you need is documented and ready to use. The confusion about naming has been clarified, and you now have:

✅ Complete understanding of all custom attributes  
✅ Ready-to-use SQL to add them to your view  
✅ Tools to re-analyze anytime  
✅ Comprehensive documentation for reference  

**Next step:** Review [SUMMARY.md](CUSTOM_ATTRIBUTES_SUMMARY.md) and decide which attributes to add!

---

*Last updated: 2025-10-08*  
*Generated by: Custom Attributes Analysis Suite*
