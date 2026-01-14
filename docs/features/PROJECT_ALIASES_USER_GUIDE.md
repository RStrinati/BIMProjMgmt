# Quick Start: Using the Optimized Project Aliases Tab

## 🚀 Immediate Benefits

- **Instant loading** (<100ms vs 5-10 seconds)
- **Run analysis** from UI (no Python scripts needed)
- **Quick-assign** interface (1 click vs 4 clicks)
- **Lazy-loaded** tabs (only load what you view)

---

## 📖 User Guide

### 1. **Opening the Tab**

Navigate to: **Settings → Project Aliases**

You'll immediately see:
- Total Aliases count
- Projects Mapped count
- Unmapped Projects count
- "Run Analysis" button
- "Refresh" button

**Load time:** ~90ms ✨

---

### 2. **View Existing Aliases**

Click: **"Existing Aliases"** tab

You'll see a table with:
- Alias Name (file/project name from external system)
- Mapped Project (your internal project)
- Issue counts (total and open)
- Edit/Delete actions

**Use case:** Verify existing mappings, edit if wrong, delete if obsolete

---

### 3. **Map Unmapped Projects (Quick Method)**

Click: **"Unmapped Projects"** tab

For each unmapped file/project:

1. **AI Suggestion** shows in the middle column:
   - 🟢 Green = High confidence (≥90%)
   - 🟡 Yellow = Medium confidence (70-89%)
   - Gray = Low confidence (<70%)

2. **Quick Assign** dropdown is pre-populated with AI suggestion

3. **Actions:**
   - Click dropdown to change project if AI is wrong
   - Click **"Assign"** button
   - Done! (alias created immediately)

**Time per alias:** ~2 seconds

---

### 4. **Run Enhanced Analysis**

Click: **"Run Analysis"** button (top right)

This executes the enhanced matching algorithm and shows:

```
📊 Confidence Breakdown:
   🟢 High (≥85%):   15 projects
   🟡 Medium (70-84%): 8 projects  
   🔴 Low (<70%):     3 projects
   ⚪ No suggestion:  2 projects
```

**Top Recommendations** are displayed with:
- File name → Suggested project
- Confidence percentage
- Match type (project_code, abbreviation, fuzzy, etc.)
- Issue count

Click **"Proceed to Auto-Map"** to bulk-assign high-confidence matches.

---

### 5. **Auto-Map Multiple Projects (Bulk Method)**

From Unmapped tab, click: **"Auto-Map X Matches"** button

Dialog appears:

1. **Set confidence threshold** (default: 85%)
   - Slider shows how many projects qualify

2. **Preview** button:
   - Shows what would be created
   - No changes made yet
   - Review results

3. **Execute Mapping** button:
   - Creates all aliases at once
   - Shows success/failure count
   - Updates immediately

**Time for 15 projects:** ~5 seconds total

---

### 6. **View Usage Statistics**

Click: **"Usage Statistics"** tab

See which projects have aliases and their issue counts:
- Project name
- Number of aliases
- List of alias names
- Total issues tracked
- Open issues

**Use case:** Identify projects with most external data sources

---

### 7. **Validate Aliases**

Click: **"Validation"** tab

Checks for:
- ✅ **Orphaned Aliases** - point to deleted projects
- ✅ **Duplicate Aliases** - same name mapped twice
- ✅ **Unused Projects** - projects without aliases

Expandable accordions show details for each issue type.

**Use case:** Routine maintenance, cleanup

---

## 🎯 Common Workflows

### Workflow 1: Quick Daily Check
```
1. Open tab → See summary instantly
2. Notice "5 unmapped projects"
3. Switch to Unmapped tab
4. Quick-assign each one (5 × 2 sec = 10 seconds)
5. Done!
```

### Workflow 2: Bulk Import from ACC
```
1. Open tab
2. Click "Run Analysis"
3. See 20 high-confidence matches
4. Click "Proceed to Auto-Map"
5. Set threshold to 85%
6. Preview results
7. Execute → 20 aliases created in 5 seconds
8. Manually review 3 low-confidence ones
```

### Workflow 3: Monthly Cleanup
```
1. Open tab
2. Switch to Validation tab
3. Review orphaned aliases
4. Delete obsolete ones
5. Switch to Unmapped tab
6. Sort by confidence
7. Quick-assign or ignore low-priority ones
```

---

## 🔧 Troubleshooting

### Tab loads slowly
- Check network connection to backend
- Run `Refresh` button
- Check browser console for errors

### AI suggestions are wrong
- This is expected for complex names
- Use the dropdown to manually select correct project
- Click "Assign" button
- System will learn over time (future enhancement)

### Auto-map creates wrong mappings
- Lower confidence threshold (e.g., 90% instead of 85%)
- Use Preview mode first
- Review results before executing
- Use Quick Assign for uncertain ones

### Analysis button shows no results
- Ensure `vw_ProjectManagement_AllIssues` view exists
- Check project names aren't already mapped
- Verify issues table has data
- Check backend logs for SQL errors

---

## 💡 Pro Tips

1. **Use Sort by Confidence** - Process high-confidence ones first
2. **Preview before bulk operations** - Always use dry-run mode
3. **Set confidence threshold high** - Start at 90%, lower if needed
4. **Quick-assign is faster** - For <10 projects, skip auto-map
5. **Run analysis weekly** - Keep unmapped count low
6. **Check validation monthly** - Cleanup orphaned aliases

---

## 🎨 UI Elements Explained

### Confidence Chips
- 🟢 **Green** (90-100%): Safe to auto-map
- 🟡 **Yellow** (75-89%): Review before mapping
- **Gray** (<75%): Manual review required

### Match Type Badges
- **project_code**: Matched P220702, MEL071 codes
- **abbreviation**: Matched MCC, NFPS abbreviations  
- **fuzzy_match**: Similar spelling (typos, variations)
- **substring**: One name contains the other
- **word_match**: Multiple words in common

### Action Buttons
- **Assign**: Create alias immediately (quick method)
- **Edit**: Modify existing alias name or project
- **Delete**: Remove alias permanently
- **Auto-Map X**: Bulk create X high-confidence aliases
- **Run Analysis**: Execute enhanced matching algorithm
- **Refresh**: Reload current tab data

---

## 📞 Support

Issues? Check:
1. Backend logs: `backend/logs/`
2. Browser console (F12)
3. Database connection: `python -c "from database import connect_to_db; print(connect_to_db())"`
4. Test optimized service: `python -c "from services.optimized_alias_service import OptimizedProjectAliasManager; m=OptimizedProjectAliasManager(); print(m.get_summary_quick()); m.close_connection()"`

---

**Last Updated:** October 31, 2025  
**Version:** 2.0 (Optimized)
