# Revit Health Warehouse Integration

**Status:** ✅ Ready for Deployment  
**Created:** 2025-12-04  
**Database:** ProjectManagement  
**Source System:** RevitHealthCheckDB

---

## 📋 Executive Summary

This warehouse integration brings **Revit model health metrics** into the central ProjectManagement data warehouse, enabling:

- ✅ **Cross-domain analytics** - Join health with projects, reviews, issues, billing
- ✅ **Historical trend analysis** - Track health improvements/degradation over time
- ✅ **Compliance tracking** - Monitor naming, coordinate, grid, level alignment
- ✅ **Executive dashboards** - Pre-built analytical marts for Power BI/Tableau
- ✅ **Performance optimization** - Indexed fact tables faster than operational views

**Current Scope:** 129 Revit files across 12 projects with full alignment validation.

---

## 🏗️ Architecture Overview

### **Data Flow**

```
RevitHealthCheckDB (Source)
    ↓
vw_RevitHealthWarehouse_CrossDB (Operational View)
    ↓
stg.revit_health_snapshots (Staging - Truncate/Reload)
    ↓
dim.revit_file (Dimension - SCD Type 2)
fact.revit_health_daily (Fact Table - Incremental)
    ↓
mart.v_project_health_summary (Project-level Analytics)
mart.v_health_trends_monthly (Time-series Trends)
```

### **Database Objects Created**

| Object | Type | Purpose |
|--------|------|---------|
| `dim.revit_file` | Dimension Table | File metadata with SCD Type 2 tracking |
| `stg.revit_health_snapshots` | Staging Table | ETL landing zone for health data |
| `fact.revit_health_daily` | Fact Table | Daily health metrics with dimensions |
| `warehouse.usp_load_stg_revit_health` | Procedure | Load staging from source view |
| `warehouse.usp_load_fact_revit_health_daily` | Procedure | Load fact with alignment integration |
| `mart.v_project_health_summary` | View | Project-level health aggregations |
| `mart.v_health_trends_monthly` | View | Monthly trend analysis |

---

## 🚀 Deployment Instructions

### **Prerequisites**

1. ✅ SQL Server with ProjectManagement and RevitHealthCheckDB databases
2. ✅ Existing `vw_RevitHealthWarehouse_CrossDB` view in RevitHealthCheckDB
3. ✅ Alignment validation views (coordinates, grids, levels) in RevitHealthCheckDB
4. ✅ Python 3.8+ with `pandas`, `pyodbc` installed
5. ✅ Database credentials configured in `config.py`

### **Option 1: SQL Deployment (Recommended for production)**

```powershell
# Connect to SQL Server and run master deployment script
sqlcmd -S <server_name> -d ProjectManagement -E -i sql\deploy_revit_health_warehouse.sql

# Example:
# sqlcmd -S localhost -d ProjectManagement -E -i sql\deploy_revit_health_warehouse.sql
```

**What it does:**
- ✅ Creates all schemas (dim, stg, fact, mart, warehouse)
- ✅ Creates dimension, staging, and fact tables
- ✅ Creates ETL procedures
- ✅ Creates analytical mart views
- ✅ Verifies deployment and reports results

**Expected Output:**
```
================================================================================
REVIT HEALTH WAREHOUSE DEPLOYMENT
Database: ProjectManagement
Started: 2025-12-04 10:30:00
================================================================================

--------------------------------------------------------------------------------
STEP 1: Creating Schemas
  ✓ Created schema: dim
  ✓ Created schema: stg
  ✓ Created schema: fact
  ✓ Created schema: mart
  ✓ Created schema: warehouse
...
✓ All warehouse objects deployed successfully!
```

### **Option 2: Python Deployment + Testing**

```powershell
# Run automated deployment and testing
python tools\deploy_warehouse.py
```

**What it does:**
- ✅ Verifies all SQL objects exist
- ✅ Runs initial ETL load (staging → fact)
- ✅ Validates data quality
- ✅ Tests Python warehouse service methods
- ✅ Provides comprehensive summary report

---

## 📊 Initial Data Load

### **Step 1: Load Staging Table**

```sql
-- Load latest health data from source view into staging
EXEC warehouse.usp_load_stg_revit_health @debug = 1;

-- Expected output:
-- Successfully loaded 129 health snapshots in 2 seconds
```

### **Step 2: Load Fact Table**

```sql
-- Load fact table with dimensional lookups and alignment validation
EXEC warehouse.usp_load_fact_revit_health_daily 
    @incremental = 1,  -- Incremental mode (only new records)
    @debug = 1;

-- Expected output:
-- Successfully loaded 129 health facts in 5 seconds
```

### **Step 3: Query Analytical Marts**

```sql
-- Project-level health summary
SELECT 
    project_name,
    total_files,
    avg_health_score,
    overall_compliance_pct,
    last_health_check_date
FROM mart.v_project_health_summary
ORDER BY avg_health_score ASC;

-- Monthly health trends
SELECT 
    year_month_name,
    project_name,
    discipline_code,
    avg_health_score,
    naming_compliance_pct,
    overall_compliance_pct
FROM mart.v_health_trends_monthly
WHERE project_id = 5  -- Replace with actual project ID
ORDER BY year_number DESC, month_number DESC;
```

---

## 🐍 Python Integration

### **Using the Updated Warehouse Service**

```python
from services.revit_health_warehouse_service import RevitHealthWarehouseService

service = RevitHealthWarehouseService()

# Get project health from warehouse (optimized query)
health = service.get_project_health_from_warehouse(project_id=5)
print(f"Project: {health['project_name']}")
print(f"Avg Health Score: {health['avg_health_score']}")
print(f"Overall Compliance: {health['validation_compliance']['overall']}%")

# Get health trends from warehouse
trends_df = service.get_health_trends_from_warehouse(project_id=5, months=6)
print(f"Retrieved {len(trends_df)} months of trend data")

# Get all projects summary from warehouse
projects = service.get_all_projects_from_warehouse()
for proj in projects:
    print(f"{proj['project_name']}: {proj['avg_health_score']} health score")

# Run warehouse ETL programmatically
success, message = service.run_warehouse_etl(debug=True)
if success:
    print("ETL completed successfully!")
```

### **New Service Methods**

| Method | Purpose |
|--------|---------|
| `get_project_health_from_warehouse()` | Project health from mart (faster than operational view) |
| `get_health_trends_from_warehouse()` | Monthly trends from warehouse |
| `get_all_projects_from_warehouse()` | All projects summary from mart |
| `get_discipline_health_trends()` | Discipline-specific trends |
| `run_warehouse_etl()` | Execute full ETL pipeline |

---

## 📈 Analytical Capabilities

### **Project Health Summary (`mart.v_project_health_summary`)**

**Provides:**
- File counts by discipline (A, S, M, E, P)
- Health score aggregations (avg, min, max)
- Health category distribution (Good, Fair, Poor, Critical)
- Warning metrics (total, critical, per-file averages)
- File size metrics and classifications
- View efficiency percentages
- **Validation compliance tracking:**
  - Naming compliance %
  - Coordinate alignment compliance %
  - Grid alignment compliance %
  - Level alignment compliance %
  - Overall compliance %
- Data freshness indicators
- Link health metrics

**Use Cases:**
- Executive dashboards
- Project health scorecards
- Compliance reporting
- Risk identification

### **Health Trends Monthly (`mart.v_health_trends_monthly`)**

**Provides:**
- Monthly aggregations by project and discipline
- Health score trends over time
- Warning trends (total, critical, per-1000-elements)
- File size trends
- Element and family count trends
- View efficiency trends
- Compliance trends (naming, alignment)
- Link health trends

**Use Cases:**
- Trend analysis
- Month-over-month comparisons
- Predictive analytics
- Process improvement tracking

---

## 🔄 ETL Scheduling

### **Option 1: SQL Server Agent Job**

```sql
-- Create SQL Agent job for daily ETL
USE msdb;
GO

EXEC dbo.sp_add_job
    @job_name = N'Daily Revit Health Warehouse ETL',
    @enabled = 1,
    @description = N'Load latest Revit health data into warehouse';

EXEC dbo.sp_add_jobstep
    @job_name = N'Daily Revit Health Warehouse ETL',
    @step_name = N'Load Staging',
    @subsystem = N'TSQL',
    @database_name = N'ProjectManagement',
    @command = N'EXEC warehouse.usp_load_stg_revit_health @debug = 0;';

EXEC dbo.sp_add_jobstep
    @job_name = N'Daily Revit Health Warehouse ETL',
    @step_name = N'Load Fact Table',
    @subsystem = N'TSQL',
    @database_name = N'ProjectManagement',
    @command = N'EXEC warehouse.usp_load_fact_revit_health_daily @incremental = 1, @debug = 0;';

-- Schedule daily at 2 AM
EXEC dbo.sp_add_schedule
    @schedule_name = N'Daily 2 AM',
    @freq_type = 4,  -- Daily
    @active_start_time = 020000;  -- 2:00 AM

EXEC dbo.sp_attach_schedule
    @job_name = N'Daily Revit Health Warehouse ETL',
    @schedule_name = N'Daily 2 AM';
```

### **Option 2: Python Scheduled Task**

```python
# schedule_warehouse_etl.py
from services.revit_health_warehouse_service import RevitHealthWarehouseService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_daily_etl():
    service = RevitHealthWarehouseService()
    success, message = service.run_warehouse_etl(debug=False)
    
    if success:
        logger.info("✅ Daily warehouse ETL completed successfully")
    else:
        logger.error(f"❌ Daily warehouse ETL failed: {message}")
        # Send alert email/notification

if __name__ == "__main__":
    run_daily_etl()
```

**Windows Task Scheduler:**
```powershell
# Create scheduled task to run daily at 2 AM
schtasks /create /tn "Revit Health Warehouse ETL" /tr "python C:\path\to\schedule_warehouse_etl.py" /sc daily /st 02:00
```

---

## 🔍 Data Quality Validation

### **Staging Table Validation**

```sql
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT project_id) as distinct_projects,
    COUNT(DISTINCT revit_file_name) as distinct_files,
    MIN(export_date) as earliest_export,
    MAX(export_date) as latest_export,
    AVG(health_score) as avg_health_score,
    SUM(CASE WHEN has_error = 1 THEN 1 ELSE 0 END) as error_count
FROM stg.revit_health_snapshots;
```

### **Fact Table Validation**

```sql
SELECT 
    COUNT(*) as total_facts,
    COUNT(DISTINCT project_key) as distinct_projects,
    COUNT(DISTINCT file_name_key) as distinct_files,
    AVG(health_score) as avg_health_score,
    SUM(total_warnings) as total_warnings,
    AVG(CAST(naming_valid AS FLOAT)) * 100 as naming_compliance_pct,
    AVG(CAST(overall_compliance AS FLOAT)) * 100 as overall_compliance_pct
FROM fact.revit_health_daily;
```

### **Dimension Table Validation**

```sql
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN current_flag = 1 THEN 1 END) as current_records,
    COUNT(DISTINCT discipline_code) as distinct_disciplines,
    COUNT(CASE WHEN naming_status = 'Valid' THEN 1 END) as valid_names,
    COUNT(CASE WHEN is_control_model = 1 THEN 1 END) as control_models
FROM dim.revit_file;
```

---

## 📊 Power BI Integration

### **Connection Setup**

1. Open Power BI Desktop
2. Get Data → SQL Server
3. Server: `<your_server>`
4. Database: `ProjectManagement`
5. Advanced Options → SQL Statement:

```sql
-- Project Health Summary
SELECT * FROM mart.v_project_health_summary

-- Health Trends
SELECT * FROM mart.v_health_trends_monthly
```

### **Recommended Visualizations**

**Dashboard 1: Project Health Overview**
- Card: Total Projects with Health Data
- Card: Overall Average Health Score
- Bar Chart: Projects by Health Category
- Table: Top 10 Critical Projects (lowest health score)
- Gauge: Overall Compliance Percentage

**Dashboard 2: Compliance Tracking**
- Line Chart: Compliance Trends Over Time (naming, coordinates, grids, levels)
- Stacked Bar: Compliance by Discipline
- Heat Map: Project x Compliance Type
- Table: Non-Compliant Files List

**Dashboard 3: Health Trends**
- Line Chart: Average Health Score by Month
- Area Chart: Warning Trends Over Time
- Column Chart: File Size Trends
- Scatter Plot: Health Score vs. File Size

---

## 🛠️ Troubleshooting

### **Issue: Staging table empty after ETL**

**Cause:** Source view `vw_RevitHealthWarehouse_CrossDB` returns no mapped files

**Solution:**
```sql
-- Check source view
SELECT COUNT(*) FROM RevitHealthCheckDB.dbo.vw_RevitHealthWarehouse_CrossDB
WHERE mapping_status = 'Mapped';

-- If zero, check project aliases
SELECT * FROM RevitHealthCheckDB.dbo.vw_RevitHealth_UnmappedFiles;
```

### **Issue: Fact table load fails with FK violations**

**Cause:** Missing dimension records for files

**Solution:**
```sql
-- Ensure dim.revit_file is populated first
SELECT COUNT(*) FROM dim.revit_file WHERE current_flag = 1;

-- The fact load procedure should auto-populate dim.revit_file
-- If not, manually insert missing files
```

### **Issue: Alignment validation columns all NULL**

**Cause:** Alignment check views don't exist or return no data

**Solution:**
```sql
-- Verify alignment views exist in RevitHealthCheckDB
SELECT * FROM RevitHealthCheckDB.sys.views
WHERE name LIKE '%Alignment%';

-- Check they return data
SELECT COUNT(*) FROM RevitHealthCheckDB.dbo.vw_CoordinateAlignmentCheck;
SELECT COUNT(*) FROM RevitHealthCheckDB.dbo.vw_GridAlignmentCheck;
SELECT COUNT(*) FROM RevitHealthCheckDB.dbo.vw_LevelAlignmentCheck;
```

---

## 📝 File Inventory

### **SQL Scripts**

```
sql/
├── tables/
│   ├── dim_revit_file.sql                  # Dimension table
│   ├── stg_revit_health_snapshots.sql      # Staging table
│   └── fact_revit_health_daily.sql         # Fact table
├── procedures/
│   ├── usp_load_stg_revit_health.sql       # Staging ETL
│   └── usp_load_fact_revit_health_daily.sql# Fact ETL
├── views/
│   ├── mart_v_project_health_summary.sql   # Project summary mart
│   └── mart_v_health_trends_monthly.sql    # Monthly trends mart
└── deploy_revit_health_warehouse.sql       # Master deployment script
```

### **Python Scripts**

```
tools/
└── deploy_warehouse.py                     # Deployment & testing script

services/
└── revit_health_warehouse_service.py       # Updated service with warehouse methods
```

### **Documentation**

```
docs/
└── REVIT_HEALTH_WAREHOUSE_INTEGRATION.md   # This file
```

---

## 🎯 Future Enhancements

### **Phase 2: Advanced Analytics**
- [ ] Predictive health scoring using ML models
- [ ] Automated anomaly detection
- [ ] Correlation analysis (health vs. review performance)
- [ ] Custom alerting rules engine

### **Phase 3: Extended Metrics**
- [ ] Warning category breakdown (families, links, views, etc.)
- [ ] Performance metrics (model load times, sync durations)
- [ ] Collaboration metrics (worksharing, worksets)
- [ ] BIM 360 integration (cloud model metrics)

### **Phase 4: Automation**
- [ ] Auto-remediation workflows for common issues
- [ ] Scheduled health reports via email
- [ ] Integration with issue tracking systems
- [ ] Real-time dashboards with auto-refresh

---

## 📞 Support & Maintenance

**Deployment Support:**
- Review this documentation
- Run `python tools/deploy_warehouse.py` for automated testing
- Check SQL error logs for detailed error messages

**Data Quality Issues:**
- Verify source view `vw_RevitHealthWarehouse_CrossDB` returns expected data
- Check project alias mappings in RevitHealthCheckDB
- Validate alignment check views exist and return data

**Performance Optimization:**
- Rebuild indexes monthly: `ALTER INDEX ALL ON fact.revit_health_daily REBUILD`
- Update statistics: `UPDATE STATISTICS fact.revit_health_daily WITH FULLSCAN`
- Monitor ETL execution times and optimize as needed

---

## ✅ Deployment Checklist

- [ ] Run SQL deployment script: `deploy_revit_health_warehouse.sql`
- [ ] Verify all objects created successfully
- [ ] Load staging table: `EXEC warehouse.usp_load_stg_revit_health @debug = 1`
- [ ] Load fact table: `EXEC warehouse.usp_load_fact_revit_health_daily @debug = 1`
- [ ] Validate data quality (check row counts, metrics)
- [ ] Test Python service methods
- [ ] Schedule daily ETL job (SQL Agent or Task Scheduler)
- [ ] Create Power BI dashboards
- [ ] Document any custom configurations
- [ ] Train users on analytical marts

---

**Version:** 1.0  
**Last Updated:** 2025-12-04  
**Author:** Data Warehouse Team
