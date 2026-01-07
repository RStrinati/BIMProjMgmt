-- =============================================
-- MASTER DEPLOYMENT SCRIPT
-- Revit Health Warehouse Integration (SQLCMD-free)
--
-- Purpose: Deploy all warehouse objects in correct dependency order without :r
-- Author: Data Warehouse Team
-- Date: 2025-12-04
-- =============================================

SET NOCOUNT ON;

PRINT '';
PRINT '================================================================================';
PRINT 'REVIT HEALTH WAREHOUSE DEPLOYMENT';
PRINT 'Database: ProjectManagement';
PRINT 'Started: ' + CONVERT(VARCHAR, GETDATE(), 120);
PRINT '================================================================================';
PRINT '';

DECLARE @start_time DATETIME2 = SYSDATETIME();
DECLARE @step_start DATETIME2;
DECLARE @step_duration INT;
DECLARE @error_count INT = 0;
DECLARE @base_path NVARCHAR(500) = N'c:\Users\RicoStrinati\Documents\research\BIMProjMngmt\';
DECLARE @file_sql NVARCHAR(MAX);
DECLARE @load_cmd NVARCHAR(MAX);

PRINT 'Using base path: ' + @base_path;

-- ============================================================================
-- STEP 1: CREATE SCHEMAS
-- ============================================================================
PRINT '--------------------------------------------------------------------------------';
PRINT 'STEP 1: Creating Schemas';
PRINT '--------------------------------------------------------------------------------';
SET @step_start = SYSDATETIME();

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'dim') EXEC('CREATE SCHEMA dim');
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'stg') EXEC('CREATE SCHEMA stg');
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'fact') EXEC('CREATE SCHEMA fact');
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'mart') EXEC('CREATE SCHEMA mart');
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'warehouse') EXEC('CREATE SCHEMA warehouse');

SET @step_duration = DATEDIFF(SECOND, @step_start, SYSDATETIME());
PRINT CONCAT('  Duration: ', @step_duration, ' seconds');
PRINT '';

-- ============================================================================
-- STEP 1B: VALIDATE SOURCE DEPENDENCIES
-- ============================================================================
PRINT '--------------------------------------------------------------------------------';
PRINT 'STEP 1B: Validating source dependencies (RevitHealthCheckDB views)';
PRINT '--------------------------------------------------------------------------------';
SET @step_start = SYSDATETIME();

IF DB_ID('RevitHealthCheckDB') IS NULL
BEGIN
    PRINT '  ERROR: RevitHealthCheckDB not accessible on this instance.';
    SET @error_count += 1;
END
ELSE
BEGIN
    IF OBJECT_ID('RevitHealthCheckDB.dbo.vw_RevitHealthWarehouse_CrossDB', 'V') IS NULL
    BEGIN
        PRINT '  ERROR: vw_RevitHealthWarehouse_CrossDB missing in RevitHealthCheckDB.';
        SET @error_count += 1;
    END ELSE PRINT '  [OK] Found vw_RevitHealthWarehouse_CrossDB';

    IF OBJECT_ID('RevitHealthCheckDB.dbo.vw_CoordinateAlignmentCheck', 'V') IS NULL
       AND OBJECT_ID('RevitHealthCheckDB.dbo.qry_CoordinateAlignmentCheck', 'V') IS NULL
    BEGIN
        PRINT '  ERROR: vw_CoordinateAlignmentCheck missing in RevitHealthCheckDB.';
        SET @error_count += 1;
    END ELSE PRINT '  [OK] Found coordinate alignment view (vw_/qry_)';

    IF OBJECT_ID('RevitHealthCheckDB.dbo.vw_GridAlignmentCheck', 'V') IS NULL
       AND OBJECT_ID('RevitHealthCheckDB.dbo.qry_GridAlignmentCheck', 'V') IS NULL
    BEGIN
        PRINT '  ERROR: vw_GridAlignmentCheck missing in RevitHealthCheckDB.';
        SET @error_count += 1;
    END ELSE PRINT '  [OK] Found grid alignment view (vw_/qry_)';

    IF OBJECT_ID('RevitHealthCheckDB.dbo.vw_LevelAlignmentCheck', 'V') IS NULL
       AND OBJECT_ID('RevitHealthCheckDB.dbo.qry_LevelAlignmentCheck', 'V') IS NULL
    BEGIN
        PRINT '  ERROR: vw_LevelAlignmentCheck missing in RevitHealthCheckDB.';
        SET @error_count += 1;
    END ELSE PRINT '  [OK] Found level alignment view (vw_/qry_)';
END

SET @step_duration = DATEDIFF(SECOND, @step_start, SYSDATETIME());
PRINT CONCAT('  Duration: ', @step_duration, ' seconds');
PRINT '';

-- Helper to execute a SQL file via OPENROWSET (no :r required)
DECLARE @files TABLE (
    seq INT IDENTITY(1,1),
    label NVARCHAR(200),
    relative_path NVARCHAR(300),
    success_msg NVARCHAR(200)
);

INSERT INTO @files (label, relative_path, success_msg)
VALUES
('sql/tables/dim_revit_file.sql', 'sql\tables\dim_revit_file.sql', 'Dimension table created: dim.revit_file'),
('sql/tables/stg_revit_health_snapshots.sql', 'sql\tables\stg_revit_health_snapshots.sql', 'Staging table created: stg.revit_health_snapshots'),
('sql/tables/fact_revit_health_daily.sql', 'sql\tables\fact_revit_health_daily.sql', 'Fact table created: fact.revit_health_daily'),
('sql/tables/fact_coordinate_alignment_daily.sql', 'sql\tables\fact_coordinate_alignment_daily.sql', 'Fact table created: fact.coordinate_alignment_daily'),
('sql/procedures/usp_load_stg_revit_health.sql', 'sql\procedures\usp_load_stg_revit_health.sql', 'Procedure created: warehouse.usp_load_stg_revit_health'),
('sql/procedures/usp_load_fact_revit_health_daily.sql', 'sql\procedures\usp_load_fact_revit_health_daily.sql', 'Procedure created: warehouse.usp_load_fact_revit_health_daily (alignment views optional; see log)'),
('sql/procedures/usp_load_fact_coordinate_alignment_daily.sql', 'sql\procedures\usp_load_fact_coordinate_alignment_daily.sql', 'Procedure created: warehouse.usp_load_fact_coordinate_alignment_daily'),
('sql/views/mart_v_project_health_summary.sql', 'sql\views\mart_v_project_health_summary.sql', 'View created: mart.v_project_health_summary'),
('sql/views/mart_v_health_trends_monthly.sql', 'sql\views\mart_v_health_trends_monthly.sql', 'View created: mart.v_health_trends_monthly'),
('sql/views/mart_v_coordinate_alignment_models.sql', 'sql\views\mart_v_coordinate_alignment_models.sql', 'View created: mart.v_coordinate_alignment_models'),
('sql/views/mart_v_coordinate_alignment_controls.sql', 'sql\views\mart_v_coordinate_alignment_controls.sql', 'View created: mart.v_coordinate_alignment_controls');

DECLARE @i INT = 1, @max INT = (SELECT COUNT(*) FROM @files);
WHILE @i <= @max
BEGIN
    DECLARE @label NVARCHAR(200), @rel NVARCHAR(300), @success NVARCHAR(200);
    SELECT @label = label, @rel = relative_path, @success = success_msg FROM @files WHERE seq = @i;

    PRINT '--------------------------------------------------------------------------------';
    PRINT 'Executing: ' + @label;
    SET @step_start = SYSDATETIME();

    BEGIN TRY
        SET @load_cmd = N'SELECT @content = BulkColumn FROM OPENROWSET(BULK ''' + @base_path + @rel + ''', SINGLE_CLOB) AS src;';
        EXEC sp_executesql @load_cmd, N'@content NVARCHAR(MAX) OUTPUT', @content=@file_sql OUTPUT;
        EXEC (@file_sql);
        PRINT '  [OK] ' + @success;
    END TRY
    BEGIN CATCH
        PRINT '  ERROR executing ' + @label + ': ' + ERROR_MESSAGE();
        SET @error_count += 1;
    END CATCH

    SET @step_duration = DATEDIFF(SECOND, @step_start, SYSDATETIME());
    PRINT CONCAT('  Duration: ', @step_duration, ' seconds');
    PRINT '';

    SET @i += 1;
END

-- ============================================================================
-- STEP 7: VERIFY DEPLOYMENT
-- ============================================================================
PRINT '--------------------------------------------------------------------------------';
PRINT 'STEP 7: Verifying Deployment';
PRINT '--------------------------------------------------------------------------------';
SET @step_start = SYSDATETIME();

IF OBJECT_ID('dim.revit_file', 'U') IS NOT NULL
    PRINT '  [OK] dim.revit_file exists';
ELSE BEGIN PRINT '  ERROR: dim.revit_file not found'; SET @error_count += 1; END

IF OBJECT_ID('stg.revit_health_snapshots', 'U') IS NOT NULL
    PRINT '  [OK] stg.revit_health_snapshots exists';
ELSE BEGIN PRINT '  ERROR: stg.revit_health_snapshots not found'; SET @error_count += 1; END

IF OBJECT_ID('fact.revit_health_daily', 'U') IS NOT NULL
    PRINT '  [OK] fact.revit_health_daily exists';
ELSE BEGIN PRINT '  ERROR: fact.revit_health_daily not found'; SET @error_count += 1; END

IF OBJECT_ID('fact.coordinate_alignment_daily', 'U') IS NOT NULL
    PRINT '  [OK] fact.coordinate_alignment_daily exists';
ELSE BEGIN PRINT '  ERROR: fact.coordinate_alignment_daily not found'; SET @error_count += 1; END

IF OBJECT_ID('warehouse.usp_load_stg_revit_health', 'P') IS NOT NULL
    PRINT '  [OK] warehouse.usp_load_stg_revit_health exists';
ELSE BEGIN PRINT '  ERROR: warehouse.usp_load_stg_revit_health not found'; SET @error_count += 1; END

IF OBJECT_ID('warehouse.usp_load_fact_revit_health_daily', 'P') IS NOT NULL
    PRINT '  [OK] warehouse.usp_load_fact_revit_health_daily exists';
ELSE BEGIN PRINT '  ERROR: warehouse.usp_load_fact_revit_health_daily not found'; SET @error_count += 1; END

IF OBJECT_ID('warehouse.usp_load_fact_coordinate_alignment_daily', 'P') IS NOT NULL
    PRINT '  [OK] warehouse.usp_load_fact_coordinate_alignment_daily exists';
ELSE BEGIN PRINT '  ERROR: warehouse.usp_load_fact_coordinate_alignment_daily not found'; SET @error_count += 1; END

IF OBJECT_ID('mart.v_project_health_summary', 'V') IS NOT NULL
    PRINT '  [OK] mart.v_project_health_summary exists';
ELSE BEGIN PRINT '  ERROR: mart.v_project_health_summary not found'; SET @error_count += 1; END

IF OBJECT_ID('mart.v_health_trends_monthly', 'V') IS NOT NULL
    PRINT '  [OK] mart.v_health_trends_monthly exists';
ELSE BEGIN PRINT '  ERROR: mart.v_health_trends_monthly not found'; SET @error_count += 1; END

SET @step_duration = DATEDIFF(SECOND, @step_start, SYSDATETIME());
PRINT CONCAT('  Duration: ', @step_duration, ' seconds');
PRINT '';

-- ============================================================================
-- DEPLOYMENT SUMMARY
-- ============================================================================
DECLARE @total_duration INT = DATEDIFF(SECOND, @start_time, SYSDATETIME());

PRINT '';
PRINT '================================================================================';
PRINT 'DEPLOYMENT SUMMARY';
PRINT '================================================================================';
PRINT CONCAT('Status: ', CASE WHEN @error_count = 0 THEN 'SUCCESS' ELSE 'FAILED' END);
PRINT CONCAT('Errors: ', @error_count);
PRINT CONCAT('Total Duration: ', @total_duration, ' seconds');
PRINT CONCAT('Completed: ', CONVERT(VARCHAR, GETDATE(), 120));
PRINT '================================================================================';
PRINT '';

IF @error_count = 0
BEGIN
    PRINT 'All warehouse objects deployed successfully!';
    PRINT 'NEXT STEPS:';
    PRINT '  1. Run initial ETL: EXEC warehouse.usp_load_stg_revit_health @debug = 1;';
    PRINT '  2. Load fact table: EXEC warehouse.usp_load_fact_revit_health_daily @debug = 1;';
    PRINT '  3. Query marts: SELECT TOP 5 * FROM mart.v_project_health_summary;';
END
ELSE
BEGIN
    PRINT 'Deployment completed with errors. Please review the log above.';
END
