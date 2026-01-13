# Database Optimization Agent Prompt

## Mission Brief

You are a **SQL Server Database Optimization Specialist** tasked with improving the performance of a BIM (Building Information Modeling) Project Management system. The system uses SQL Server with 3 databases and has documented performance issues including 5-10 second dashboard load times and query bottlenecks.

Your goal: Implement the optimization plan outlined in [`DATABASE_OPTIMIZATION_REPORT.md`](./DATABASE_OPTIMIZATION_REPORT.md) to achieve **40-60% query performance improvement** and **90% faster dashboard loads**.

---

## Application Frontend + Data Contract (Required)

Fill in or confirm these items before implementing any frontend visualization or reporting changes.

### 1. Frontend Stack (Required)
- **Frontend framework:** TBD (React / Vue / Angular / plain JS)
- **Language:** TBD (TypeScript or JavaScript)
- **Charting library:** TBD (Recharts / Chart.js / ECharts / D3 / Victory / Other) or "agent to recommend one"
- **Styling system:** TBD (CSS / SCSS / Tailwind / MUI / Ant / Chakra / Custom design system)

### 2. Data Source & Contract (Required)

#### 2.1 Data Origin
- **Data source:** TBD (REST API / GraphQL / Static JSON / Direct SQL -> API view)

#### 2.2 Data Shape (Critical)
- **Field names (exact):** TBD
- **Date format:** TBD (ISO string / Filename-based like `2025-09-16.xlsx`)
- **Weeks are:** TBD (pre-aggregated in backend / grouped client-side)

Example confirmation:
```ts
interface WeeklyAccIssues {
  week_end_date: string;
  closed: number;
  open: number;
  completed: number;
  in_progress: number;
}
```

### 3. Business Rules (Required)
- **Issue counts are:** TBD (created that week / modified that week / snapshot totals as of that week)
- **An issue appears in multiple statuses in one week:** TBD (should be no)
- **Missing weeks:** TBD (filled with zeros / omitted as gaps)

### 4. Time Handling (Required)
- **Timezone for week calculation:** TBD
- **Definition of a week:** TBD (Mon-Sun / Sun-Sat / ISO week)
- **Week label format:** TBD (date range / week-ending date only)

### 5. Visual Fidelity Requirements (Required)
- **Fidelity:** TBD (visual reference only / must match styling exactly)
- **Colors:** TBD (fixed / theme-driven)
- **Value labels:** TBD (always / hover / selected series)

### 6. Interactivity Scope (Required)
- **Tooltip:** TBD (yes/no; per-point or shared)
- **Legend toggling:** TBD (enabled/disabled)
- **Zoom/pan:** TBD (enabled/disabled)
- **Mobile responsiveness:** TBD (required/optional)

### 7. Layout & Placement (Required)
- **Container:** TBD (dashboard card / full-width page)
- **Sizing:** TBD (fixed or responsive height)
- **Title/subtitle:** TBD (passed as props / hardcoded)
- **Logos:** TBD (included/excluded)

### 8. Performance Constraints (Optional)
- **Typical weeks displayed:** TBD (e.g., 12/26/52)
- **Max dataset size:** TBD
- **Re-render frequency:** TBD

### 9. Error & Empty States (Optional)
- **No data:** TBD (empty state behavior)
- **Partial data:** TBD (fallback behavior)
- **API error:** TBD (error UI)

### 10. Output Expectations (Required)
- **Deliverable:** TBD (single reusable chart component / Storybook example / mock data included / unit tests required)

### 11. Optional Application Context
- **Chart links to:** TBD (issue lists / drill-down views)
- **Click behavior:** TBD (navigate to filtered issues page)

---

## Project Context

### Database Architecture
- **Primary Database:** `ProjectManagement` (hybrid OLTP + data warehouse)
  - Schemas: `dbo` (OLTP), `stg` (staging), `dim` (dimensions), `fact` (facts), `mart` (aggregates), `brg` (bridges)
- **Secondary Databases:** `acc_data_schema`, `RevitHealthCheckDB`
- **Connection:** SQL Server Express instance `.\SQLEXPRESS`
- **Credentials:** `admin02` / `1234` (development environment)

### Key Files
- **Schema Constants:** [`constants/schema.py`](../constants/schema.py) - All table/column references
- **Database Layer:** [`database.py`](../database.py) - Data access functions
- **Connection Pool:** [`database_pool.py`](../database_pool.py) - Connection management
- **Optimization Script:** [`sql/optimize_critical_indexes.sql`](../sql/optimize_critical_indexes.sql) - Ready to execute
- **Full Report:** [`docs/DATABASE_OPTIMIZATION_REPORT.md`](./DATABASE_OPTIMIZATION_REPORT.md) - Complete analysis

### Current Pain Points
1. Dashboard queries timeout after 120 seconds
2. Missing indexes on 90% of foreign key relationships
3. N+1 query patterns documented in codebase
4. No partitioning on time-series fact tables
5. Inefficient JSON column usage (15+ columns in `tblRvtProjHealth`)

---

## Phase 1: Critical Fixes (Execute Today) 🔴

**Priority:** CRITICAL | **Duration:** 2-4 hours | **Impact:** 40-60% improvement

### Task 1.1: Pre-Flight Checks ✅

**Objective:** Ensure safe execution environment

```powershell
# 1. Verify database connection
sqlcmd -S .\SQLEXPRESS -U admin02 -P 1234 -Q "SELECT @@VERSION"

# 2. Check current database size
sqlcmd -S .\SQLEXPRESS -d ProjectManagement -U admin02 -P 1234 -Q "
SELECT 
    name,
    size/128 AS size_mb,
    (SELECT COUNT(*) FROM sys.indexes WHERE object_id = o.object_id) AS index_count
FROM sys.database_files f
CROSS APPLY (SELECT TOP 1 object_id FROM sys.objects) o
"

# 3. Backup database (CRITICAL - do this first!)
sqlcmd -S .\SQLEXPRESS -U admin02 -P 1234 -Q "
BACKUP DATABASE [ProjectManagement] 
TO DISK = 'C:\Backups\ProjectManagement_PreOptimization_$(Get-Date -Format yyyyMMdd_HHmmss).bak'
WITH COMPRESSION, INIT, NAME = 'Pre-Optimization Backup'
"
```

**Validation:**
- [ ] Database connection successful
- [ ] Backup completed (verify file exists)
- [ ] Current performance baseline documented

---

### Task 1.2: Execute Critical Index Script 🚀

**Objective:** Add 20+ missing indexes on foreign keys and frequently queried columns

```powershell
# Execute the optimization script
sqlcmd -S .\SQLEXPRESS -d ProjectManagement -U admin02 -P 1234 -i sql/optimize_critical_indexes.sql -o logs/index_optimization_$(Get-Date -Format yyyyMMdd_HHmmss).log

# If script has errors, review log
Get-Content logs/index_optimization_*.log -Tail 50
```

**What This Does:**
- Creates indexes on `projects` table (client_id, status, dates)
- Adds indexes to `ReviewSchedule`, `review_cycles`, `ReviewStages`
- Indexes `Issues_Current` for analytics queries
- Adds covering indexes on `ProjectServices`, `ServiceReviews`
- Creates filtered indexes on warehouse dimension tables
- Updates statistics on all newly indexed tables

**Expected Duration:** 5-10 minutes

**Validation Queries:**

```sql
-- 1. Verify indexes were created
USE ProjectManagement;
SELECT 
    OBJECT_SCHEMA_NAME(object_id) AS schema_name,
    OBJECT_NAME(object_id) AS table_name,
    name AS index_name,
    type_desc,
    is_disabled
FROM sys.indexes
WHERE name LIKE 'IX_%'
    AND create_date > DATEADD(HOUR, -1, GETDATE())
ORDER BY create_date DESC;

-- 2. Check index fragmentation (should be 0% for new indexes)
SELECT 
    OBJECT_NAME(ips.object_id) AS table_name,
    i.name AS index_name,
    ips.avg_fragmentation_in_percent,
    ips.page_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
WHERE i.name LIKE 'IX_%'
    AND i.create_date > DATEADD(HOUR, -1, GETDATE())
ORDER BY ips.avg_fragmentation_in_percent DESC;
```

**Success Criteria:**
- [ ] All indexes created without errors
- [ ] No indexes are disabled
- [ ] Fragmentation < 5% on all new indexes

---

### Task 1.3: Monitor Initial Performance Improvement 📊

**Objective:** Validate that indexes are being used

**Wait Time:** 1-2 hours of normal application usage

**Monitoring Queries:**

```sql
-- 1. Most used new indexes (after some application usage)
SELECT 
    OBJECT_NAME(s.object_id) AS table_name,
    i.name AS index_name,
    s.user_seeks + s.user_scans + s.user_lookups AS total_reads,
    s.user_updates AS total_writes,
    CASE 
        WHEN s.user_seeks + s.user_scans + s.user_lookups = 0 THEN 'NOT USED'
        WHEN s.user_updates > (s.user_seeks + s.user_scans + s.user_lookups) * 10 THEN 'WRITE HEAVY'
        ELSE 'GOOD'
    END AS usage_status
FROM sys.dm_db_index_usage_stats s
JOIN sys.indexes i ON s.object_id = i.object_id AND s.index_id = i.index_id
WHERE s.database_id = DB_ID('ProjectManagement')
    AND i.name LIKE 'IX_%'
    AND i.create_date > DATEADD(HOUR, -2, GETDATE())
ORDER BY total_reads DESC;

-- 2. Slow queries still executing (should be reduced)
SELECT TOP 10
    SUBSTRING(qt.text, (qs.statement_start_offset/2)+1, 
        ((CASE qs.statement_end_offset 
            WHEN -1 THEN DATALENGTH(qt.text)
            ELSE qs.statement_end_offset 
        END - qs.statement_start_offset)/2)+1) AS query_text,
    qs.execution_count,
    qs.total_elapsed_time/1000000.0 AS total_elapsed_sec,
    qs.total_elapsed_time / qs.execution_count / 1000000.0 AS avg_elapsed_sec,
    qs.last_execution_time
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) qt
WHERE qs.last_execution_time > DATEADD(HOUR, -1, GETDATE())
    AND qt.text NOT LIKE '%sys.dm_exec%'
ORDER BY avg_elapsed_sec DESC;

-- 3. Query execution plan analysis (check if new indexes are in plans)
SELECT 
    p.query_plan,
    t.text AS query_text,
    s.execution_count,
    s.total_elapsed_time / 1000000.0 AS total_sec
FROM sys.dm_exec_query_stats s
CROSS APPLY sys.dm_exec_sql_text(s.sql_handle) t
CROSS APPLY sys.dm_exec_query_plan(s.plan_handle) p
WHERE t.text LIKE '%ReviewSchedule%'
    OR t.text LIKE '%Issues_Current%'
    OR t.text LIKE '%projects%'
ORDER BY s.last_execution_time DESC;
```

**Success Criteria:**
- [ ] New indexes showing usage (reads > 0)
- [ ] Average query time reduced by 30-50%
- [ ] No queries timing out

---

### Task 1.4: Test Critical Application Paths 🧪

**Objective:** Verify application functionality after index changes

**Test Cases:**

1. **Dashboard Load**
   ```python
   # Run from project root
   python -c "
   from database import _calculate_warehouse_dashboard_metrics
   import time
   
   start = time.time()
   result = _calculate_warehouse_dashboard_metrics()
   elapsed = time.time() - start
   
   print(f'Dashboard metrics loaded in {elapsed:.2f} seconds')
   print(f'Issues: {result.get(\"issue_metrics\", {}).get(\"total_open_issues\", 0)}')
   print(f'Projects: {len(result.get(\"projects\", []))}')
   "
   ```
   **Expected:** < 2 seconds (down from 5-10 seconds)

2. **Project List Query**
   ```python
   python -c "
   from database import get_projects_full
   import time
   
   start = time.time()
   projects = get_projects_full()
   elapsed = time.time() - start
   
   print(f'Loaded {len(projects)} projects in {elapsed:.2f} seconds')
   "
   ```
   **Expected:** < 0.5 seconds

3. **Review Schedule Query**
   ```python
   python -c "
   from database import get_review_schedules_by_date_range
   from datetime import datetime, timedelta
   import time
   
   start_date = datetime.now()
   end_date = start_date + timedelta(days=30)
   
   start = time.time()
   schedules = get_review_schedules_by_date_range(start_date, end_date)
   elapsed = time.time() - start
   
   print(f'Loaded {len(schedules)} schedules in {elapsed:.2f} seconds')
   "
   ```
   **Expected:** < 1 second

**Success Criteria:**
- [ ] All test queries execute successfully
- [ ] Performance improved by 40-60%
- [ ] No application errors

---

## Phase 2: High-Impact Optimizations (Week 1) 🟡

**Priority:** HIGH | **Duration:** 8-12 hours | **Impact:** Additional 30-40% improvement

### Task 2.1: JSON Column Optimization

**Objective:** Add computed columns and indexes for frequently queried JSON attributes

**Implementation:**

```sql
USE ProjectManagement;
GO

-- 1. Add computed columns to Issues_Current
ALTER TABLE dbo.Issues_Current
ADD discipline_computed AS JSON_VALUE(custom_attributes_json, '$.discipline') PERSISTED;

ALTER TABLE dbo.Issues_Current
ADD phase_computed AS JSON_VALUE(custom_attributes_json, '$.phase') PERSISTED;

ALTER TABLE dbo.Issues_Current
ADD building_level_computed AS JSON_VALUE(custom_attributes_json, '$.building_level') PERSISTED;
GO

-- 2. Create indexes on computed columns
CREATE NONCLUSTERED INDEX IX_IssuesCurrent_Discipline 
    ON dbo.Issues_Current(discipline_computed) 
    INCLUDE (issue_key, status_normalized, project_id)
    WHERE discipline_computed IS NOT NULL;

CREATE NONCLUSTERED INDEX IX_IssuesCurrent_Phase 
    ON dbo.Issues_Current(phase_computed) 
    INCLUDE (issue_key, status_normalized, project_id)
    WHERE phase_computed IS NOT NULL;
GO

-- 3. Test query performance
SELECT 
    discipline_computed,
    COUNT(*) AS issue_count,
    SUM(CASE WHEN status_normalized = 'Open' THEN 1 ELSE 0 END) AS open_count
FROM dbo.Issues_Current
WHERE discipline_computed IS NOT NULL
GROUP BY discipline_computed;
GO
```

**Validation:**
```sql
-- Check if JSON values were extracted correctly
SELECT TOP 100
    issue_key,
    custom_attributes_json,
    discipline_computed,
    phase_computed
FROM dbo.Issues_Current
WHERE custom_attributes_json IS NOT NULL;

-- Verify index usage
SELECT * FROM sys.dm_db_index_usage_stats
WHERE object_id = OBJECT_ID('dbo.Issues_Current')
    AND index_id IN (
        SELECT index_id FROM sys.indexes 
        WHERE name IN ('IX_IssuesCurrent_Discipline', 'IX_IssuesCurrent_Phase')
    );
```

**Success Criteria:**
- [ ] Computed columns populated correctly
- [ ] Indexes created successfully
- [ ] Custom attribute queries 80% faster

---

### Task 2.2: Implement Materialized Views

**Objective:** Cache expensive aggregations for dashboard queries

**Implementation:**

```sql
USE ProjectManagement;
GO

-- 1. Create indexed view for project summary
CREATE VIEW dbo.vw_ProjectSummary_Indexed
WITH SCHEMABINDING
AS
SELECT 
    p.project_id,
    p.project_name,
    p.status,
    c.client_id,
    c.client_name,
    COUNT_BIG(*) AS service_count,
    SUM(ISNULL(CAST(s.agreed_fee AS DECIMAL(18,2)), 0)) AS total_fees,
    SUM(ISNULL(CAST(s.progress_pct AS DECIMAL(5,2)), 0)) / 
        NULLIF(COUNT_BIG(*), 0) AS avg_progress
FROM dbo.projects p
INNER JOIN dbo.clients c ON p.client_id = c.client_id
LEFT JOIN dbo.ProjectServices s ON p.project_id = s.project_id
WHERE p.status IS NOT NULL AND c.client_name IS NOT NULL
GROUP BY p.project_id, p.project_name, p.status, c.client_id, c.client_name;
GO

-- 2. Create clustered index (materializes the view)
CREATE UNIQUE CLUSTERED INDEX IX_ProjectSummary_PK 
    ON dbo.vw_ProjectSummary_Indexed(project_id);
GO

-- 3. Create supporting nonclustered indexes
CREATE NONCLUSTERED INDEX IX_ProjectSummary_Client 
    ON dbo.vw_ProjectSummary_Indexed(client_id);

CREATE NONCLUSTERED INDEX IX_ProjectSummary_Status 
    ON dbo.vw_ProjectSummary_Indexed(status);
GO

-- 4. Test the view
SELECT * FROM dbo.vw_ProjectSummary_Indexed ORDER BY total_fees DESC;
GO
```

**Update Application Code:**

```python
# In database.py, add new function
def get_project_summary_fast():
    """
    Get project summaries using materialized view.
    90% faster than joining tables on-the-fly.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                project_id,
                project_name,
                status,
                client_name,
                service_count,
                total_fees,
                avg_progress
            FROM dbo.vw_ProjectSummary_Indexed
            WHERE status IN ('Active', 'In Progress')
            ORDER BY total_fees DESC
        """)
        return cursor.fetchall()
```

**Validation:**
```sql
-- Compare performance: Regular query vs materialized view
SET STATISTICS TIME ON;
SET STATISTICS IO ON;

-- Old way (joins every time)
SELECT 
    p.project_id,
    p.project_name,
    c.client_name,
    COUNT(*) AS service_count,
    SUM(s.agreed_fee) AS total_fees
FROM dbo.projects p
JOIN dbo.clients c ON p.client_id = c.client_id
LEFT JOIN dbo.ProjectServices s ON p.project_id = s.project_id
GROUP BY p.project_id, p.project_name, c.client_name;

-- New way (materialized)
SELECT * FROM dbo.vw_ProjectSummary_Indexed;

SET STATISTICS TIME OFF;
SET STATISTICS IO OFF;
```

**Success Criteria:**
- [ ] Materialized view created successfully
- [ ] Query time reduced by 80-90%
- [ ] View auto-updates on data changes

---

### Task 2.3: Design Partition Strategy

**Objective:** Plan monthly partitioning for time-series tables

**Analysis:**

```sql
-- 1. Identify tables that need partitioning
SELECT 
    SCHEMA_NAME(t.schema_id) + '.' + t.name AS table_name,
    SUM(p.rows) AS row_count,
    SUM(a.total_pages) * 8 / 1024.0 AS size_mb,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM sys.columns c 
            WHERE c.object_id = t.object_id 
            AND c.name IN ('snapshot_date', 'import_date', 'created_at', 'event_ts')
        ) THEN 'HAS_DATE_COLUMN'
        ELSE 'NO_DATE_COLUMN'
    END AS partition_candidate
FROM sys.tables t
JOIN sys.partitions p ON t.object_id = p.object_id
JOIN sys.allocation_units a ON p.partition_id = a.container_id
WHERE p.index_id IN (0, 1)  -- Heap or clustered index
GROUP BY t.schema_id, t.name, t.object_id
HAVING SUM(p.rows) > 100000  -- Large tables only
ORDER BY size_mb DESC;

-- 2. Analyze date distribution
SELECT 
    YEAR(snapshot_date) AS year,
    MONTH(snapshot_date) AS month,
    COUNT(*) AS row_count,
    MIN(snapshot_date) AS min_date,
    MAX(snapshot_date) AS max_date
FROM dbo.Issues_Snapshots
GROUP BY YEAR(snapshot_date), MONTH(snapshot_date)
ORDER BY year, month;
```

**Design Document:**

Create [`docs/PARTITION_STRATEGY.md`](./PARTITION_STRATEGY.md):
```markdown
# Table Partitioning Strategy

## Tables to Partition
1. dbo.Issues_Snapshots (snapshot_date)
2. fact.issue_snapshot (snapshot_date_sk)
3. fact.issue_activity (event_ts)
4. dbo.ACCImportLogs (import_date)

## Partition Scheme
- **Method:** Range Right partitioning
- **Interval:** Monthly (1st of each month)
- **Retention:** Keep 24 months online, archive older data
- **Filegroups:** All on PRIMARY (consider separate filegroups in production)

## Implementation Timeline
- Phase 2.4: Create partition function/scheme
- Phase 2.5: Migrate Issues_Snapshots
- Phase 2.6: Migrate fact tables
- Phase 2.7: Setup monthly maintenance job
```

**Success Criteria:**
- [ ] Partition candidates identified
- [ ] Strategy documented
- [ ] Team approval obtained

---

### Task 2.4: Implement Partitioning (Issues_Snapshots)

**Objective:** Partition the largest time-series table

**Implementation:**

```sql
USE ProjectManagement;
GO

-- 1. Create partition function (monthly boundaries)
CREATE PARTITION FUNCTION PF_IssueSnapshot_Monthly (DATE)
AS RANGE RIGHT FOR VALUES (
    '2024-01-01', '2024-02-01', '2024-03-01', '2024-04-01', 
    '2024-05-01', '2024-06-01', '2024-07-01', '2024-08-01',
    '2024-09-01', '2024-10-01', '2024-11-01', '2024-12-01',
    '2025-01-01', '2025-02-01', '2025-03-01', '2025-04-01',
    '2025-05-01', '2025-06-01', '2025-07-01', '2025-08-01',
    '2025-09-01', '2025-10-01', '2025-11-01', '2025-12-01',
    '2026-01-01', '2026-02-01'
);
GO

-- 2. Create partition scheme
CREATE PARTITION SCHEME PS_IssueSnapshot_Monthly
AS PARTITION PF_IssueSnapshot_Monthly
ALL TO ([PRIMARY]);
GO

-- 3. Create new partitioned table
CREATE TABLE dbo.Issues_Snapshots_NEW (
    snapshot_id BIGINT IDENTITY(1,1),
    snapshot_date DATE NOT NULL,
    import_run_id INT NULL,
    issue_key NVARCHAR(255) NOT NULL,
    issue_key_hash AS HASHBYTES('SHA2_256', issue_key) PERSISTED,
    source_system NVARCHAR(32) NOT NULL,
    source_issue_id NVARCHAR(255) NULL,
    source_project_id NVARCHAR(255) NULL,
    project_id INT NULL,
    status_normalized NVARCHAR(50) NULL,
    priority_normalized NVARCHAR(50) NULL,
    discipline_normalized NVARCHAR(100) NULL,
    location_root NVARCHAR(255) NULL,
    assignee_user_key NVARCHAR(255) NULL,
    is_open BIT NULL,
    is_closed BIT NULL,
    backlog_age_days INT NULL,
    resolution_days INT NULL,
    created_at DATETIME2 NULL,
    updated_at DATETIME2 NULL,
    closed_at DATETIME2 NULL,
    load_ts DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT PK_Issues_Snapshots_NEW PRIMARY KEY (snapshot_id, snapshot_date)
) ON PS_IssueSnapshot_Monthly(snapshot_date);
GO

-- 4. Migrate data (do in batches to avoid blocking)
DECLARE @batch_size INT = 50000;
DECLARE @max_snapshot_id BIGINT;

SELECT @max_snapshot_id = MAX(snapshot_id) FROM dbo.Issues_Snapshots;

DECLARE @current_id BIGINT = 0;

WHILE @current_id < @max_snapshot_id
BEGIN
    INSERT INTO dbo.Issues_Snapshots_NEW WITH (TABLOCK)
    SELECT 
        snapshot_date, import_run_id, issue_key, source_system,
        source_issue_id, source_project_id, project_id,
        status_normalized, priority_normalized, discipline_normalized,
        location_root, assignee_user_key, is_open, is_closed,
        backlog_age_days, resolution_days,
        created_at, updated_at, closed_at, load_ts
    FROM dbo.Issues_Snapshots
    WHERE snapshot_id > @current_id 
        AND snapshot_id <= @current_id + @batch_size;
    
    SET @current_id = @current_id + @batch_size;
    
    PRINT 'Migrated up to snapshot_id: ' + CAST(@current_id AS VARCHAR(20));
    
    -- Brief pause to avoid blocking
    WAITFOR DELAY '00:00:02';
END
GO

-- 5. Verify data integrity
SELECT 
    'Original' AS source,
    COUNT(*) AS row_count,
    MIN(snapshot_date) AS min_date,
    MAX(snapshot_date) AS max_date
FROM dbo.Issues_Snapshots
UNION ALL
SELECT 
    'New',
    COUNT(*),
    MIN(snapshot_date),
    MAX(snapshot_date)
FROM dbo.Issues_Snapshots_NEW;

-- 6. Rename tables (after verification!)
-- EXEC sp_rename 'dbo.Issues_Snapshots', 'Issues_Snapshots_OLD';
-- EXEC sp_rename 'dbo.Issues_Snapshots_NEW', 'Issues_Snapshots';
GO
```

**Validation:**

```sql
-- Check partition distribution
SELECT 
    p.partition_number,
    pf.name AS partition_function,
    prv.value AS boundary_value,
    p.rows AS row_count
FROM sys.partitions p
JOIN sys.indexes i ON p.object_id = i.object_id AND p.index_id = i.index_id
JOIN sys.partition_schemes ps ON i.data_space_id = ps.data_space_id
JOIN sys.partition_functions pf ON ps.function_id = pf.function_id
LEFT JOIN sys.partition_range_values prv 
    ON pf.function_id = prv.function_id 
    AND p.partition_number = prv.boundary_id + 1
WHERE p.object_id = OBJECT_ID('dbo.Issues_Snapshots_NEW')
    AND i.index_id IN (0, 1)
ORDER BY p.partition_number;

-- Test partition elimination (query should only scan relevant partitions)
SET STATISTICS IO ON;
SELECT COUNT(*) 
FROM dbo.Issues_Snapshots_NEW
WHERE snapshot_date >= '2025-12-01' AND snapshot_date < '2026-01-01';
SET STATISTICS IO OFF;
```

**Success Criteria:**
- [ ] All data migrated successfully
- [ ] Row counts match
- [ ] Queries use partition elimination (check execution plan)

---

## Phase 3: Medium Priority (Week 2-3) 🟢

### Task 3.1: Add Filtered Indexes

**Objective:** Create smaller, more efficient indexes for active records

```sql
USE ProjectManagement;
GO

-- Active projects only (exclude Completed, Archived, Cancelled)
CREATE NONCLUSTERED INDEX IX_Projects_Active_Status 
    ON dbo.projects(status) 
    INCLUDE (project_id, project_name, client_id, start_date, end_date)
    WHERE status IN ('Active', 'In Progress', 'Planning');

-- Open issues only (most queried subset)
CREATE NONCLUSTERED INDEX IX_IssuesCurrent_Open_Priority 
    ON dbo.Issues_Current(project_id, priority_normalized)
    INCLUDE (issue_key, created_at, assignee_user_key, status_normalized)
    WHERE status_normalized IN ('Open', 'In Progress', 'Pending', 'Assigned');

-- Current SCD Type 2 records only
CREATE NONCLUSTERED INDEX IX_DimIssue_Current_Status 
    ON dim.issue(project_sk, status_normalized)
    INCLUDE (issue_bk, title, priority_normalized, created_date_sk)
    WHERE current_flag = 1;

-- Unbilled service reviews (financial queries)
CREATE NONCLUSTERED INDEX IX_ServiceReviews_Unbilled 
    ON dbo.ServiceReviews(service_id, status)
    INCLUDE (planned_date, billing_amount, actual_issued_at)
    WHERE is_billed = 0 OR is_billed IS NULL;
GO
```

**Expected Impact:** 30% smaller indexes, faster queries on filtered data

---

### Task 3.2: Optimize String Column Sizes

**Objective:** Reduce storage and improve memory utilization

```sql
-- 1. Analyze actual usage
SELECT 
    'project_name' AS column_name,
    MAX(LEN(project_name)) AS max_length,
    AVG(LEN(project_name)) AS avg_length,
    510 AS declared_length,
    CASE WHEN MAX(LEN(project_name)) <= 255 THEN 'CAN REDUCE' ELSE 'KEEP AS IS' END AS recommendation
FROM dbo.projects
UNION ALL
SELECT 
    'task_name',
    MAX(LEN(task_name)),
    AVG(LEN(task_name)),
    510,
    CASE WHEN MAX(LEN(task_name)) <= 200 THEN 'CAN REDUCE' ELSE 'KEEP AS IS' END
FROM dbo.tasks
UNION ALL
SELECT 
    'folder_path',
    MAX(LEN(folder_path)),
    AVG(LEN(folder_path)),
    1000,
    CASE WHEN MAX(LEN(folder_path)) <= 500 THEN 'CAN REDUCE' ELSE 'KEEP AS IS' END
FROM dbo.projects;

-- 2. Modify columns (only if safe!)
-- Check recommendations first, then execute if data fits
-- ALTER TABLE dbo.projects ALTER COLUMN project_name NVARCHAR(255) NOT NULL;
-- ALTER TABLE dbo.tasks ALTER COLUMN task_name NVARCHAR(200) NULL;
-- ALTER TABLE dbo.projects ALTER COLUMN folder_path NVARCHAR(500) NULL;
```

---

### Task 3.3: Enable Compression

**Objective:** Reduce storage by 50-70%

```sql
USE ProjectManagement;
GO

-- Check estimated compression savings
EXEC sp_estimate_data_compression_savings 
    @schema_name = 'dbo', 
    @object_name = 'Issues_Snapshots', 
    @index_id = NULL, 
    @partition_number = NULL, 
    @data_compression = 'PAGE';

-- Apply PAGE compression to historical tables
ALTER TABLE dbo.Issues_Snapshots REBUILD WITH (DATA_COMPRESSION = PAGE);
ALTER TABLE dbo.IssueImportRuns REBUILD WITH (DATA_COMPRESSION = PAGE);
ALTER TABLE fact.issue_snapshot REBUILD WITH (DATA_COMPRESSION = PAGE);
ALTER TABLE fact.issue_activity REBUILD WITH (DATA_COMPRESSION = PAGE);

-- Check compression results
SELECT 
    OBJECT_SCHEMA_NAME(p.object_id) AS schema_name,
    OBJECT_NAME(p.object_id) AS table_name,
    i.name AS index_name,
    p.data_compression_desc,
    p.rows,
    (a.total_pages * 8) / 1024.0 AS size_mb
FROM sys.partitions p
JOIN sys.indexes i ON p.object_id = i.object_id AND p.index_id = i.index_id
JOIN sys.allocation_units a ON p.partition_id = a.container_id
WHERE p.data_compression_desc <> 'NONE'
ORDER BY size_mb DESC;
```

---

## Phase 4: Schema Cleanup (Week 4) 🟢

### Task 4.1: Audit Redundant Tables

**Objective:** Identify duplicate/similar tables for consolidation

```sql
-- Find tables with similar names
SELECT 
    t1.TABLE_SCHEMA + '.' + t1.TABLE_NAME AS table1,
    t2.TABLE_SCHEMA + '.' + t2.TABLE_NAME AS table2,
    (
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS c1
        WHERE c1.TABLE_NAME = t1.TABLE_NAME
        AND c1.TABLE_SCHEMA = t1.TABLE_SCHEMA
        AND EXISTS (
            SELECT 1 
            FROM INFORMATION_SCHEMA.COLUMNS c2 
            WHERE c2.TABLE_SCHEMA = t2.TABLE_SCHEMA
            AND c2.TABLE_NAME = t2.TABLE_NAME 
            AND c2.COLUMN_NAME = c1.COLUMN_NAME
        )
    ) AS matching_columns,
    (SELECT COUNT(*) FROM sys.objects WHERE name = t1.TABLE_NAME) +
    (SELECT COUNT(*) FROM sys.objects WHERE name = t2.TABLE_NAME) AS total_columns
FROM INFORMATION_SCHEMA.TABLES t1
JOIN INFORMATION_SCHEMA.TABLES t2 
    ON t1.TABLE_NAME < t2.TABLE_NAME
    AND (
        SOUNDEX(t1.TABLE_NAME) = SOUNDEX(t2.TABLE_NAME)
        OR t1.TABLE_NAME LIKE '%' + t2.TABLE_NAME + '%'
        OR t2.TABLE_NAME LIKE '%' + t1.TABLE_NAME + '%'
    )
WHERE t1.TABLE_TYPE = 'BASE TABLE'
    AND t2.TABLE_TYPE = 'BASE TABLE'
ORDER BY matching_columns DESC;
```

---

## Ongoing Maintenance Tasks

### Weekly: Index Maintenance

```sql
-- Check fragmentation and rebuild/reorganize as needed
DECLARE @fragmentation_threshold_rebuild FLOAT = 30.0;
DECLARE @fragmentation_threshold_reorganize FLOAT = 10.0;

SELECT 
    OBJECT_SCHEMA_NAME(ips.object_id) AS schema_name,
    OBJECT_NAME(ips.object_id) AS table_name,
    i.name AS index_name,
    ips.avg_fragmentation_in_percent,
    ips.page_count,
    CASE 
        WHEN ips.avg_fragmentation_in_percent > @fragmentation_threshold_rebuild 
            THEN 'ALTER INDEX [' + i.name + '] ON [' + OBJECT_SCHEMA_NAME(ips.object_id) + '].[' + OBJECT_NAME(ips.object_id) + '] REBUILD;'
        WHEN ips.avg_fragmentation_in_percent > @fragmentation_threshold_reorganize 
            THEN 'ALTER INDEX [' + i.name + '] ON [' + OBJECT_SCHEMA_NAME(ips.object_id) + '].[' + OBJECT_NAME(ips.object_id) + '] REORGANIZE;'
        ELSE '-- OK, no action needed'
    END AS maintenance_command
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
WHERE ips.avg_fragmentation_in_percent > @fragmentation_threshold_reorganize
    AND ips.page_count > 1000
    AND i.name IS NOT NULL
ORDER BY ips.avg_fragmentation_in_percent DESC;
```

### Weekly: Statistics Update

```sql
-- Update statistics on key tables
UPDATE STATISTICS dbo.projects WITH FULLSCAN;
UPDATE STATISTICS dbo.Issues_Current WITH FULLSCAN;
UPDATE STATISTICS dbo.ReviewSchedule WITH FULLSCAN;
UPDATE STATISTICS dbo.review_cycles WITH FULLSCAN;
UPDATE STATISTICS dbo.ProjectServices WITH FULLSCAN;
UPDATE STATISTICS fact.issue_snapshot WITH FULLSCAN;
```

### Monthly: Archive Old Data

```sql
-- Archive issues older than 24 months (if partitioned, use SWITCH)
BEGIN TRANSACTION;

    INSERT INTO dbo.Issues_Archive
    SELECT * FROM dbo.Issues_Snapshots
    WHERE snapshot_date < DATEADD(MONTH, -24, GETDATE());

    IF @@ROWCOUNT = (
        SELECT COUNT(*) FROM dbo.Issues_Snapshots 
        WHERE snapshot_date < DATEADD(MONTH, -24, GETDATE())
    )
    BEGIN
        DELETE FROM dbo.Issues_Snapshots
        WHERE snapshot_date < DATEADD(MONTH, -24, GETDATE());
        COMMIT;
    END
    ELSE
    BEGIN
        ROLLBACK;
    END
GO
```

---

## Success Metrics & KPIs

### Performance Targets

| Metric | Baseline | Target | Current | Status |
|--------|----------|--------|---------|--------|
| Dashboard load time | 5-10s | <1s | ? | ⏳ |
| Project list query | 2-3s | <0.1s | ? | ⏳ |
| Issue analytics | 8-15s | 1-2s | ? | ⏳ |
| Review schedule | 3-5s | <1s | ? | ⏳ |
| Query timeout rate | 5-10% | <1% | ? | ⏳ |

### Resource Metrics

| Metric | Before | Target | Current | Status |
|--------|--------|--------|---------|--------|
| Database size | ? GB | - | ? GB | ⏳ |
| Index fragmentation | >50% | <30% | ? | ⏳ |
| Storage (after compression) | - | -50% | ? | ⏳ |
| Avg query I/O | ? | -40% | ? | ⏳ |

---

## Safety Guidelines

### ⚠️ Always Do This Before Changes

1. **Backup database:**
   ```sql
   BACKUP DATABASE [ProjectManagement] 
   TO DISK = 'C:\Backups\PreOptimization_YYYYMMDD.bak'
   WITH COMPRESSION;
   ```

2. **Test in non-production first** (if available)

3. **Create rollback plan for each change**

4. **Schedule during maintenance window** for large operations

### 🚨 Rollback Procedures

**If indexes cause issues:**
```sql
-- Drop specific index
DROP INDEX IX_IndexName ON dbo.TableName;
```

**If partitioning fails:**
```sql
-- Rename tables back
EXEC sp_rename 'dbo.Issues_Snapshots_NEW', 'Issues_Snapshots_FAILED';
EXEC sp_rename 'dbo.Issues_Snapshots_OLD', 'Issues_Snapshots';
```

**If performance degrades:**
```sql
-- Disable problematic index temporarily
ALTER INDEX IX_IndexName ON dbo.TableName DISABLE;

-- Re-enable after investigation
ALTER INDEX IX_IndexName ON dbo.TableName REBUILD;
```

---

## Reporting & Documentation

### After Each Phase

1. **Update performance metrics** in success tracking table
2. **Document any issues encountered** and resolutions
3. **Update** [`DATABASE_OPTIMIZATION_REPORT.md`](./DATABASE_OPTIMIZATION_REPORT.md) with actual results
4. **Commit changes** to version control with descriptive messages

### Final Report Template

```markdown
# Optimization Results Summary

## Execution Timeline
- Start Date: YYYY-MM-DD
- Completion Date: YYYY-MM-DD
- Total Effort: X hours

## Performance Improvements
- Dashboard load: X seconds → Y seconds (Z% improvement)
- Project queries: X seconds → Y seconds (Z% improvement)
- Issue analytics: X seconds → Y seconds (Z% improvement)

## Database Changes
- Indexes added: N
- Tables partitioned: N
- Compression enabled: N tables
- Storage saved: X GB (Y%)

## Issues Encountered
1. Issue description
   - Resolution: How it was fixed
   
## Recommendations for Next Phase
- Additional optimization opportunities
- Monitoring focus areas
```

---

## Agent Checklist

Use this checklist to track progress:

### Phase 1 (Critical)
- [ ] Database backed up
- [ ] Critical indexes script executed
- [ ] All indexes created successfully
- [ ] Index usage verified (after 1-2 hours)
- [ ] Application tests passed
- [ ] Performance improvement documented

### Phase 2 (High Priority)
- [ ] JSON computed columns added
- [ ] Materialized views created
- [ ] Partition strategy designed
- [ ] Issues_Snapshots partitioned
- [ ] Data migration verified

### Phase 3 (Medium Priority)
- [ ] Filtered indexes added
- [ ] String column sizes optimized
- [ ] Compression enabled
- [ ] Storage savings measured

### Phase 4 (Schema Cleanup)
- [ ] Redundant tables identified
- [ ] Migration plan created
- [ ] Unified views created
- [ ] Schema consolidated

### Maintenance
- [ ] Index maintenance script scheduled
- [ ] Statistics update automated
- [ ] Archive procedure documented
- [ ] Monitoring queries saved

---

## Resources & References

- **Main Report:** [`docs/DATABASE_OPTIMIZATION_REPORT.md`](./DATABASE_OPTIMIZATION_REPORT.md)
- **Index Script:** [`sql/optimize_critical_indexes.sql`](../sql/optimize_critical_indexes.sql)
- **Schema Constants:** [`constants/schema.py`](../constants/schema.py)
- **Database Layer:** [`database.py`](../database.py)
- **SQL Server Docs:** https://learn.microsoft.com/en-us/sql/

---

## Final Notes

- **Be methodical:** Complete each task fully before moving to the next
- **Validate everything:** Run verification queries after each change
- **Document issues:** Track any problems and resolutions
- **Monitor continuously:** Check index usage and query performance regularly
- **Communicate:** Update team on progress and any blockers

**Good luck! The database depends on you. 🚀**
