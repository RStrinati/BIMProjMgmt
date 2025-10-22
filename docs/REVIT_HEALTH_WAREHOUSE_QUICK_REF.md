# Revit Health Warehouse - Quick Reference Guide

## 🎯 Quick Start

### View Current Status
```sql
-- All projects health summary
SELECT * FROM dbo.vw_RevitHealth_ProjectSummary ORDER BY avg_health_score ASC;

-- Recent health checks (last 30 days)
SELECT TOP 20 
    revit_file_name,
    pm_project_name,
    calculated_health_score,
    health_category,
    total_warnings,
    export_date
FROM dbo.vw_RevitHealthWarehouse_CrossDB
WHERE days_since_export <= 30
ORDER BY calculated_health_score ASC;

-- Critical files needing attention
SELECT 
    revit_file_name,
    pm_project_name,
    calculated_health_score,
    total_warnings,
    critical_warnings
FROM dbo.vw_RevitHealthWarehouse_CrossDB
WHERE health_category IN ('Poor', 'Critical')
ORDER BY calculated_health_score ASC;
```

### Python Quick Access
```python
from services.revit_health_warehouse_service import get_warehouse_service

# Get service
service = get_warehouse_service()

# All projects overview
all_projects = service.get_all_projects_summary()

# Specific project detail
summary = service.get_project_health_summary(11)  # CWPS

# Critical files across all projects
critical = service.get_critical_files(limit=10)

# Project trends (last 6 months)
trends_df = service.get_health_trends(11, months=6)
```

### Validate File Naming
```python
from services.revit_naming_validator_service import RevitNamingValidator

validator = RevitNamingValidator()

# Validate all unvalidated files
count = validator.validate_all_unvalidated()

# Get validation summary
summary = validator.get_validation_summary()

# Get files with naming issues
invalid = validator.get_invalid_files(limit=20)
```

## 📊 View Columns Reference

### vw_RevitHealthWarehouse_CrossDB (Main Warehouse)

**Identity:**
- `health_check_id` - Unique ID
- `revit_file_name` - File name

**Project Linkage:**
- `pm_project_id` - Internal project ID
- `pm_project_name` - Project name
- `client_name` - Client name
- `mapping_status` - 'Mapped' or 'Unmapped'

**Health Metrics:**
- `calculated_health_score` - 0-100 score
- `health_category` - Good/Fair/Poor/Critical
- `total_warnings` - Warning count
- `critical_warnings` - Critical warning count

**File Info:**
- `file_size_mb` - Size in MB
- `file_size_category` - Size classification
- `export_date` - When exported
- `days_since_export` - Age in days
- `data_freshness` - Current/Recent/Outdated

**Element Metrics:**
- `total_elements` - Total element count
- `family_count` - Family count
- `revit_links` - Revit link count
- `dwg_imports` - DWG import count

**View Metrics:**
- `total_views` - Total views
- `views_not_on_sheets` - Orphaned views
- `view_efficiency_pct` - % of views on sheets

**Validation:**
- `validation_status` - Valid/Warning/Invalid
- `discipline_code` - ARC, STR, MEP, etc.
- `link_health_flag` - Import risk flag

### vw_RevitHealth_ProjectSummary (Aggregates)

- `pm_project_id`, `pm_project_name`, `client_name`
- `unique_files` - Number of unique files
- `avg_health_score`, `min_health_score`, `max_health_score`
- `total_warnings_all_files`, `total_critical_warnings`
- `total_model_size_mb`, `avg_file_size_mb`
- `good_files`, `fair_files`, `poor_files`, `critical_files`
- `current_files`, `recent_files`, `outdated_files`
- `files_with_link_risks`

### vw_RevitHealth_UnmappedFiles (Discovery)

- `health_check_id`, `revit_file_name`
- `suggested_project_id`, `suggested_project_name`
- `match_confidence` - 0-100% confidence score
- `total_warnings`, `health_category`

## 🔍 Common Queries

### Files by Project
```sql
SELECT 
    revit_file_name,
    calculated_health_score,
    total_warnings,
    file_size_mb,
    export_date
FROM dbo.vw_RevitHealthWarehouse_CrossDB
WHERE pm_project_id = 11  -- CWPS
ORDER BY calculated_health_score ASC;
```

### Worst Health Files Across All Projects
```sql
SELECT TOP 10
    pm_project_name,
    revit_file_name,
    calculated_health_score,
    total_warnings,
    critical_warnings,
    export_date
FROM dbo.vw_RevitHealthWarehouse_CrossDB
ORDER BY calculated_health_score ASC, total_warnings DESC;
```

### Files Needing Review (Outdated + Poor Health)
```sql
SELECT 
    pm_project_name,
    revit_file_name,
    calculated_health_score,
    days_since_export,
    data_freshness
FROM dbo.vw_RevitHealthWarehouse_CrossDB
WHERE health_category IN ('Poor', 'Critical')
  AND data_freshness = 'Outdated'
ORDER BY days_since_export DESC;
```

### Health Trend for Project (Monthly)
```sql
SELECT 
    DATEFROMPARTS(export_year, export_month, 1) as month,
    COUNT(DISTINCT revit_file_name) as file_count,
    AVG(calculated_health_score) as avg_score,
    SUM(total_warnings) as total_warnings
FROM dbo.vw_RevitHealthWarehouse_CrossDB
WHERE pm_project_id = 11
  AND export_date >= DATEADD(MONTH, -12, GETDATE())
GROUP BY export_year, export_month
ORDER BY export_year, export_month;
```

### Files with Naming Issues
```sql
SELECT 
    revit_file_name,
    validation_status,
    validation_reason,
    discipline_code,
    pm_project_name
FROM dbo.vw_RevitHealthWarehouse_CrossDB
WHERE validation_status IN ('Invalid', 'Warning')
ORDER BY 
    CASE WHEN validation_status = 'Invalid' THEN 1 ELSE 2 END,
    revit_file_name;
```

### Project Health Comparison
```sql
SELECT 
    pm_project_name,
    client_name,
    unique_files,
    avg_health_score,
    good_files + fair_files as acceptable_files,
    poor_files + critical_files as problem_files,
    CAST(
        (good_files + fair_files) * 100.0 / NULLIF(unique_files, 0) 
        AS DECIMAL(5,2)
    ) as acceptable_pct
FROM dbo.vw_RevitHealth_ProjectSummary
ORDER BY acceptable_pct ASC;
```

## 🐍 Python Service Methods

### RevitHealthWarehouseService

```python
service = get_warehouse_service()

# Get all projects
all_projects = service.get_all_projects_summary()
# Returns: List[Dict] with project summaries

# Get specific project
summary = service.get_project_health_summary(project_id)
# Returns: Dict with detailed project metrics

# Get unmapped files
unmapped = service.get_unmapped_files(limit=50, min_confidence=60)
# Returns: List[Dict] with suggested mappings

# Create alias mapping
success, msg = service.create_alias_mapping(health_check_id, project_id, alias_name)
# Returns: Tuple[bool, str]

# Get trends
trends_df = service.get_health_trends(project_id, months=6)
# Returns: pandas DataFrame

# Get file detail
detail = service.get_file_health_detail(health_check_id)
# Returns: Dict

# Get critical files
critical = service.get_critical_files(project_id=None, limit=20)
# Returns: List[Dict]
```

### RevitNamingValidator

```python
validator = RevitNamingValidator()

# Validate file name
status, reason, disc_code, disc_name = validator.validate_file_naming(file_name)
# Returns: Tuple[str, str, Optional[str], Optional[str]]

# Validate new health check
success = validator.validate_new_health_check(health_check_id)
# Returns: bool

# Batch validate
count = validator.validate_all_unvalidated()
# Returns: int (count of validated records)

# Get summary
summary = validator.get_validation_summary()
# Returns: Dict with counts by status

# Get invalid files
invalid = validator.get_invalid_files(limit=50)
# Returns: List[Dict]
```

## 📈 Health Score Interpretation

| Score | Category | Meaning | Action |
|-------|----------|---------|--------|
| 90-100 | Good | Excellent health | Monitor |
| 70-89 | Fair | Some issues | Review warnings |
| 50-69 | Poor | Multiple issues | Immediate review |
| 0-49 | Critical | Severe problems | Urgent action |

## 🚨 Alerts & Thresholds

**Critical Warnings:**
- ≥50 critical warnings = Health score 0 (Critical)

**File Size:**
- <100 MB = Small
- 100-300 MB = Medium
- 300-500 MB = Large
- >500 MB = Very Large

**Data Freshness:**
- ≤7 days = Current
- 8-30 days = Recent
- >30 days = Outdated

**Link Health:**
- >10 DWG imports = High CAD Import Risk
- SketchUp imports present = Warning flag

## 📞 Troubleshooting

**No data in warehouse view:**
```sql
-- Check base table
SELECT COUNT(*) FROM dbo.tblRvtProjHealth WHERE nDeletedOn IS NULL;

-- Check project aliases
SELECT COUNT(*) FROM ProjectManagement.dbo.project_aliases;
```

**Unmapped files appearing:**
```python
# Get suggestions
unmapped = service.get_unmapped_files(min_confidence=50)

# Create mapping
for file in unmapped:
    if file['match_confidence'] >= 80:
        service.create_alias_mapping(
            file['health_check_id'],
            file['suggested_project_id'],
            file['project_number']
        )
```

**Performance issues:**
```sql
-- Rebuild indexes
ALTER INDEX IX_tblRvtProjHealth_FileName ON dbo.tblRvtProjHealth REBUILD;
ALTER INDEX IX_tblRvtProjHealth_ProjectMapping ON dbo.tblRvtProjHealth REBUILD;

-- Update statistics
UPDATE STATISTICS dbo.tblRvtProjHealth;
```

---

**Current Status (2025-10-16):**
- ✅ 137 health checks in warehouse
- ✅ 4 projects mapped
- ✅ 0 unmapped files
- ✅ 58% files with valid naming
