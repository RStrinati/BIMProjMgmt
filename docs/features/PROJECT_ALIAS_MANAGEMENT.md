# Project Alias Management System

## 🎯 **Overview**

The Project Alias Management System provides comprehensive tools to **continuously map and maintain** aliases between internal project names and external system names (Revizto, ACC, etc.). This ensures that all project issues are properly associated with the correct internal projects.

## 📊 **Current Status**

Based on the latest analysis:

- **✅ 12 existing aliases** mapping to 5 internal projects
- **✅ 4 projects successfully linked** to external issues (1,067 total issues)  
- **⚠️ 12 unmapped external projects** with 14,357+ additional issues available
- **📈 Potential**: Adding proper aliases could unlock **15,424+ total issues**

### **Mapped Projects (Working)**
| Project | Aliases | Total Issues | Sources |
|---------|---------|--------------|---------|
| CWPS (11) | 4 aliases | 38 issues | ACC |
| MPHS (10) | 2 aliases | 249 issues | ACC |
| NFPS (2) | 2 aliases | 488 issues | ACC |
| SPS (3) | 2 aliases | 292 issues | ACC |

### **Top Unmapped Projects (High Priority)**
| External Project Name | Issues | Potential |
|----------------------|---------|-----------|
| 55 Pitt Street | 7,737 | High Value |
| MEL01A | 2,828 | High Value |
| NEXTDC S4 | 1,794 | High Value |
| SYD054 | 1,332 | High Value |
| SYD01 - Goodman | 666 | Medium Value |

## 🚀 **Getting Started**

### **Launch the Alias Management Interface**
```bash
python run_enhanced_ui.py
```
Navigate to the **🔗 Project Aliases** tab

### **Key Features Available**
1. **📊 Real-time statistics** - Total aliases, validation status, unmapped projects
2. **🏷️ Alias management** - Add, edit, delete aliases with validation
3. **🔍 Auto-discovery** - Find unmapped projects with issue counts and suggestions  
4. **✅ Validation tools** - Detect orphaned aliases and unused projects
5. **📤📥 Import/Export** - CSV bulk operations for large-scale management

## 📋 **Daily/Weekly Management Workflow**

### **1. Monitor Unmapped Projects (Weekly)**
- Click **"🔍 Discover Unmapped"** to refresh unmapped projects
- Review the **"❓ Unmapped Projects"** tab for high-value projects
- Focus on projects with **high issue counts** first

### **2. Create New Aliases (As Needed)**
- **Option A**: From unmapped list - double-click project to create mapping
- **Option B**: Manual - click **"➕ Add Alias"** button
- Use **suggested matches** when available

### **3. Validate Existing Aliases (Monthly)**
- Click **"📊 Validate Aliases"** to check for issues
- Fix any **orphaned aliases** (point to deleted projects)
- Review **unused projects** for potential new aliases

### **4. Bulk Operations (For Large Changes)**
- **Export**: Click **"📤 Export CSV"** for backup/review
- **Import**: Click **"📥 Import CSV"** for bulk updates
- **Format**: `alias_name, pm_project_id, project_name, project_status, project_manager, project_created`

## 🔍 **Discovery & Mapping Strategy**

### **Auto-Suggestion Algorithm**
The system automatically suggests matches based on:
- **Exact substring matching** (highest confidence)
- **Word overlap analysis** (partial matches)
- **Common abbreviations** and naming patterns

### **Mapping Priority Matrix**
| Issue Count | Action Priority | Time Investment |
|-------------|----------------|-----------------|
| 1000+ issues | 🔴 Immediate | High value, map first |
| 100-999 issues | 🟡 This week | Medium priority |
| 10-99 issues | 🟢 This month | Low priority |
| <10 issues | ⚪ As needed | Optional |

## ⚠️ **Common Patterns & Solutions**

### **Naming Pattern Examples**
- **School Projects**: `"Schofields PS [P220702]"` → `"SPS"`  
- **Construction Sites**: `"MEL071 - Site A"` → `"MEL071"`
- **Building Codes**: `"Calderwood PS [P230521]"` → `"CWPS"`

### **Multiple Aliases Strategy**
Many projects benefit from **multiple aliases**:
```
CWPS Project → Aliases:
├── "250613" (project code)
├── "Calderwood PS [P230521]" (full name)
├── "CWD" (abbreviation)  
└── "CWPS" (internal name)
```

## 🛠️ **Troubleshooting**

### **"No Issues Found" After Adding Alias**
1. **Verify exact spelling** - External names are case-sensitive
2. **Check the issues view** - `vw_ProjectManagement_AllIssues`
3. **Use Discovery tool** - Confirm the project name appears in unmapped list

### **"Alias Already Exists" Error** 
1. **Check existing aliases** - May be mapped to different project
2. **Use Edit function** - Update existing mapping instead
3. **Consider variations** - Add suffix like "_v2" if needed

### **Performance Issues**
1. **Large datasets** - Use CSV export/import for bulk operations
2. **Slow discovery** - Run during off-peak hours
3. **Database timeouts** - Check connection settings

## 📈 **Success Metrics**

Track these KPIs for continuous improvement:

### **Coverage Metrics**
- **Alias Coverage**: Currently 5/15 projects (33%) have aliases
- **Issue Coverage**: Currently 1,067/15,424 issues (7%) accessible
- **Target**: 80%+ issue coverage for active projects

### **Quality Metrics**
- **Orphaned Aliases**: Currently 0 (✅ Good)
- **Duplicate Aliases**: Currently 0 (✅ Good)  
- **Unused Projects**: Currently 10 (⚠️ Opportunity)

### **Activity Metrics**
- **New Mappings/Week**: Track alias creation rate
- **Validation Frequency**: Run validation monthly
- **Discovery Updates**: Check unmapped weekly

## 🔄 **Automation Opportunities**

### **Future Enhancements**
1. **Auto-mapping** - Smart suggestions with high confidence scores
2. **Change detection** - Alert when new external projects appear  
3. **Batch processing** - Import from external systems automatically
4. **Integration hooks** - Update aliases when projects are renamed

### **API Integration Possibilities**
```python
# Example: Auto-discover and suggest mappings
unmapped = manager.discover_unmapped_projects()
high_priority = [p for p in unmapped if p['total_issues'] > 500]

for project in high_priority:
    suggestion = project.get('suggested_match')
    if suggestion and suggestion['confidence'] > 0.8:
        # Auto-create high-confidence mappings
        manager.add_alias(suggestion['project_id'], project['project_name'])
```

## 📞 **Support & Resources**

### **Files & Locations**
- **Service**: `services/project_alias_service.py`
- **UI Tab**: `ui/project_alias_tab.py`  
- **Database**: `project_aliases` table in ProjectManagement DB
- **Issues View**: `vw_ProjectManagement_AllIssues`

### **Key Functions**
```python
from services.project_alias_service import ProjectAliasManager

manager = ProjectAliasManager()

# Essential operations
aliases = manager.get_all_aliases()
unmapped = manager.discover_unmapped_projects() 
validation = manager.validate_aliases()
stats = manager.get_alias_usage_stats()

# CRUD operations
manager.add_alias(project_id, alias_name)
manager.update_alias(old_name, new_name, new_project_id)
manager.delete_alias(alias_name)
```

---

## 🎯 **Quick Start Checklist**

- [ ] Launch UI and navigate to **🔗 Project Aliases** tab
- [ ] Review current **📊 Statistics** and **📈 Usage Statistics**  
- [ ] Check **❓ Unmapped Projects** for high-priority mappings
- [ ] Create aliases for projects with **1000+ issues**
- [ ] Run **📊 Validate Aliases** to check system health
- [ ] Export current state with **📤 Export CSV** for backup

**Result**: Dramatically improved project issue visibility and management capabilities!