# Revit Health Warehouse - Quick Start Guide

## 🚀 One-Command Deployment

```powershell
# Deploy all warehouse objects
sqlcmd -S localhost -d ProjectManagement -E -i sql\deploy_revit_health_warehouse.sql

# Run initial ETL and tests
python tools\deploy_warehouse.py
```

---

## 📊 Quick Queries

### **Project Health Summary**
```sql
SELECT * FROM mart.v_project_health_summary
ORDER BY avg_health_score ASC;
```

### **Monthly Trends (Last 6 Months)**
```sql
SELECT * FROM mart.v_health_trends_monthly
WHERE year_month >= FORMAT(DATEADD(MONTH, -6, GETDATE()), 'yyyy-MM')
ORDER BY year_number DESC, month_number DESC;
```

### **Critical Files Requiring Attention**
```sql
SELECT 
    project_name,
    total_files,
    critical_files,
    poor_files,
    overall_compliance_pct
FROM mart.v_project_health_summary
WHERE critical_files > 0 OR poor_files > 0
ORDER BY critical_files DESC, poor_files DESC;
```

---

## 🐍 Python Usage

```python
from services.revit_health_warehouse_service import RevitHealthWarehouseService

service = RevitHealthWarehouseService()

# Get all projects
projects = service.get_all_projects_from_warehouse()

# Get specific project health
health = service.get_project_health_from_warehouse(project_id=5)

# Get trends
trends = service.get_health_trends_from_warehouse(project_id=5, months=6)

# Run ETL
success, msg = service.run_warehouse_etl(debug=True)
```

---

## 🔄 Daily ETL Commands

```sql
-- Step 1: Load staging
EXEC warehouse.usp_load_stg_revit_health @debug = 0;

-- Step 2: Load fact table (incremental)
EXEC warehouse.usp_load_fact_revit_health_daily @incremental = 1, @debug = 0;
```

---

## 📁 File Locations

| File | Purpose |
|------|---------|
| `sql/deploy_revit_health_warehouse.sql` | Master deployment script |
| `tools/deploy_warehouse.py` | Python deployment & testing |
| `docs/REVIT_HEALTH_WAREHOUSE_INTEGRATION.md` | Full documentation |
| `sql/tables/dim_revit_file.sql` | Dimension table |
| `sql/tables/fact_revit_health_daily.sql` | Fact table |
| `sql/procedures/usp_load_stg_revit_health.sql` | Staging ETL |
| `sql/procedures/usp_load_fact_revit_health_daily.sql` | Fact ETL |
| `sql/views/mart_v_project_health_summary.sql` | Project summary mart |
| `sql/views/mart_v_health_trends_monthly.sql` | Monthly trends mart |

---

## ✅ Deployment Checklist

- [ ] Run SQL deployment script
- [ ] Run Python testing script
- [ ] Verify data loaded (>100 fact records expected)
- [ ] Schedule daily ETL job
- [ ] Create Power BI dashboards
- [ ] Train users on marts

---

## 🎯 Key Metrics Available

### **Project-Level**
- Total files, control model files, files by discipline
- Average/min/max health scores
- Health category distribution (Good/Fair/Poor/Critical)
- Total warnings, critical warnings
- **Validation compliance:**
  - Naming compliance %
  - Coordinate alignment %
  - Grid alignment %
  - Level alignment %
  - Overall compliance %

### **Trend Analysis**
- Monthly health score trends
- Warning trends over time
- Compliance trends by discipline
- File size trends
- View efficiency trends

---

## 📞 Troubleshooting

**No data in staging?**
```sql
-- Check source view
SELECT COUNT(*) FROM RevitHealthCheckDB.dbo.vw_RevitHealthWarehouse_CrossDB
WHERE mapping_status = 'Mapped';
```

**Fact table load fails?**
```sql
-- Check dimension populated
SELECT COUNT(*) FROM dim.revit_file WHERE current_flag = 1;
```

**Performance slow?**
```sql
-- Rebuild indexes
ALTER INDEX ALL ON fact.revit_health_daily REBUILD;
UPDATE STATISTICS fact.revit_health_daily WITH FULLSCAN;
```

---

For full documentation, see: [`docs/REVIT_HEALTH_WAREHOUSE_INTEGRATION.md`](REVIT_HEALTH_WAREHOUSE_INTEGRATION.md)
