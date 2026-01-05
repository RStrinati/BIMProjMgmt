DROP PROCEDURE IF EXISTS warehouse.usp_load_fact_revit_health_daily;
GO

CREATE PROCEDURE warehouse.usp_load_fact_revit_health_daily
    @incremental BIT = 1,
    @batch_id UNIQUEIDENTIFIER = NULL,
    @debug BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @rows_inserted INT = 0;
    DECLARE @start_time DATETIME2 = SYSDATETIME();
    DECLARE @coord_view_name SYSNAME = NULL;
    DECLARE @grid_view_name SYSNAME = NULL;
    DECLARE @level_view_name SYSNAME = NULL;
    DECLARE @has_coord_view BIT = 0;
    DECLARE @has_grid_view BIT = 0;
    DECLARE @has_level_view BIT = 0;

    IF DB_ID('RevitHealthCheckDB') IS NOT NULL
    BEGIN
        SELECT TOP 1 @coord_view_name = v.name FROM RevitHealthCheckDB.sys.views v WHERE v.name IN ('vw_CoordinateAlignmentCheck','qry_CoordinateAlignmentCheck') ORDER BY CASE WHEN v.name LIKE 'vw_%' THEN 0 ELSE 1 END;
        SELECT TOP 1 @grid_view_name  = v.name FROM RevitHealthCheckDB.sys.views v WHERE v.name IN ('vw_GridAlignmentCheck','qry_GridAlignmentCheck') ORDER BY CASE WHEN v.name LIKE 'vw_%' THEN 0 ELSE 1 END;
        SELECT TOP 1 @level_view_name = v.name FROM RevitHealthCheckDB.sys.views v WHERE v.name IN ('vw_LevelAlignmentCheck','qry_LevelAlignmentCheck') ORDER BY CASE WHEN v.name LIKE 'vw_%' THEN 0 ELSE 1 END;
        SET @has_coord_view = CASE WHEN @coord_view_name IS NOT NULL THEN 1 ELSE 0 END;
        SET @has_grid_view  = CASE WHEN @grid_view_name  IS NOT NULL THEN 1 ELSE 0 END;
        SET @has_level_view = CASE WHEN @level_view_name IS NOT NULL THEN 1 ELSE 0 END;
    END

    SET @batch_id = COALESCE(@batch_id, NEWID());

    BEGIN TRY
        IF @debug = 1
            PRINT CONCAT('Starting fact load at ', FORMAT(@start_time, 'yyyy-MM-dd HH:mm:ss'), ' (Mode: ', CASE WHEN @incremental = 1 THEN 'Incremental' ELSE 'Full Refresh' END, ', Batch: ', @batch_id, ')');

        IF @debug = 1 PRINT 'Loading dim.revit_file...';
        INSERT INTO dim.revit_file (file_name_bk, normalized_file_name, discipline_code, model_functional_code, naming_status, is_control_model, zone_code, file_extension)
        SELECT DISTINCT stg.revit_file_name, stg.revit_file_name, stg.discipline_code, stg.model_functional_code, stg.naming_status, COALESCE(stg.control_is_primary,0), stg.zone_code,
               RIGHT(stg.revit_file_name, CHARINDEX('.', REVERSE(stg.revit_file_name)))
        FROM stg.revit_health_snapshots stg
        WHERE NOT EXISTS (SELECT 1 FROM dim.revit_file df WHERE df.file_name_bk = stg.revit_file_name AND df.current_flag = 1);
        IF @debug = 1 PRINT CONCAT('  - Inserted ', @@ROWCOUNT, ' new files into dim.revit_file');

        IF @debug = 1 PRINT 'Loading fact.revit_health_daily...';

        CREATE TABLE #alignment_checks (
            health_check_id INT PRIMARY KEY,
            coordinates_aligned BIT,
            grids_aligned BIT,
            levels_aligned BIT
        );

        IF @has_coord_view = 1 AND @has_grid_view = 1 AND @has_level_view = 1
        BEGIN
            DECLARE @align_sql NVARCHAR(MAX) = N'
                INSERT INTO #alignment_checks (health_check_id, coordinates_aligned, grids_aligned, levels_aligned)
                SELECT DISTINCT stg.health_check_id,
                       COALESCE(coord.is_aligned,0),
                       COALESCE(grid.is_aligned,0),
                       COALESCE(lvl.is_aligned,0)
                FROM stg.revit_health_snapshots stg
                LEFT JOIN RevitHealthCheckDB.dbo.' + QUOTENAME(@coord_view_name) + N' coord ON stg.health_check_id = coord.health_check_id
                LEFT JOIN RevitHealthCheckDB.dbo.' + QUOTENAME(@grid_view_name)  + N' grid  ON stg.health_check_id = grid.health_check_id
                LEFT JOIN RevitHealthCheckDB.dbo.' + QUOTENAME(@level_view_name) + N' lvl   ON stg.health_check_id = lvl.health_check_id;';
            EXEC (@align_sql);
            IF @debug = 1 PRINT CONCAT('  - Loaded alignment checks for ', @@ROWCOUNT, ' health checks');
        END
        ELSE
        BEGIN
            INSERT INTO #alignment_checks (health_check_id, coordinates_aligned, grids_aligned, levels_aligned)
            SELECT DISTINCT stg.health_check_id, NULL, NULL, NULL FROM stg.revit_health_snapshots stg;
            IF @debug = 1 PRINT '  - Alignment check views missing; inserted NULL alignment flags.';
        END

        INSERT INTO fact.revit_health_daily (
            date_key, project_key, file_name_key, health_check_id, model_functional_code,
            health_score, health_category, total_warnings, critical_warnings,
            file_size_mb, file_size_category, total_elements, family_count,
            total_views, views_not_on_sheets, view_efficiency_pct,
            revit_links, dwg_imports, dwg_links, link_health_flag,
            naming_valid, coordinates_aligned, grids_aligned, levels_aligned,
            is_control_model, zone_code, export_datetime, days_since_export, data_freshness,
            warnings_per_1000_elements, critical_warning_ratio,
            batch_id, source_system
        )
        SELECT 
            COALESCE(d.date_key, -1) AS date_key,
            p.project_id AS project_key,
            df.revit_file_key,
            stg.health_check_id,
            stg.model_functional_code,
            stg.health_score,
            stg.health_category,
            stg.total_warnings,
            stg.critical_warnings,
            stg.file_size_mb,
            CASE WHEN stg.file_size_mb < 100 THEN 'Small' WHEN stg.file_size_mb < 300 THEN 'Medium' WHEN stg.file_size_mb < 500 THEN 'Large' ELSE 'Very Large' END,
            stg.total_elements,
            stg.family_count,
            stg.total_views,
            stg.views_not_on_sheets,
            stg.view_efficiency_pct,
            stg.revit_links,
            stg.dwg_imports,
            stg.dwg_links,
            stg.link_health_flag,
            CASE WHEN stg.naming_status = 'Valid' THEN 1 ELSE 0 END,
            align.coordinates_aligned,
            align.grids_aligned,
            align.levels_aligned,
            COALESCE(stg.control_is_primary, 0),
            stg.zone_code,
            stg.export_date,
            stg.days_since_export,
            stg.data_freshness,
            CASE WHEN stg.total_elements > 0 THEN CAST(stg.total_warnings AS DECIMAL(10,2)) * 1000.0 / stg.total_elements ELSE NULL END,
            CASE WHEN stg.total_warnings > 0 THEN CAST(stg.critical_warnings AS DECIMAL(10,4)) / stg.total_warnings ELSE NULL END,
            @batch_id,
            stg.source_system
        FROM stg.revit_health_snapshots stg
        LEFT JOIN (
            SELECT DISTINCT CAST(export_date AS DATE) AS date_value, CAST(FORMAT(export_date,'yyyyMMdd') AS INT) AS date_key
            FROM stg.revit_health_snapshots
        ) d ON CAST(stg.export_date AS DATE) = d.date_value
        LEFT JOIN dbo.projects p ON stg.project_id = p.project_id
        INNER JOIN dim.revit_file df ON stg.revit_file_name = df.file_name_bk AND df.current_flag = 1
        LEFT JOIN #alignment_checks align ON stg.health_check_id = align.health_check_id
        WHERE (@incremental = 0 OR NOT EXISTS (SELECT 1 FROM fact.revit_health_daily f WHERE f.health_check_id = stg.health_check_id));

        SET @rows_inserted = @@ROWCOUNT;
        DROP TABLE #alignment_checks;

        DECLARE @duration_seconds INT = DATEDIFF(SECOND, @start_time, SYSDATETIME());
        PRINT CONCAT('Successfully loaded ', @rows_inserted, ' health facts in ', @duration_seconds, ' seconds (Batch: ', @batch_id, ')');

        IF @debug = 1
        BEGIN
            SELECT COUNT(*) AS total_facts, COUNT(DISTINCT project_key) AS distinct_projects, COUNT(DISTINCT file_name_key) AS distinct_files,
                   AVG(health_score) AS avg_health_score, MIN(health_score) AS min_health_score, MAX(health_score) AS max_health_score,
                   SUM(total_warnings) AS total_warnings,
                   SUM(CASE WHEN naming_valid = 1 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*),0) AS naming_compliance_pct,
                   SUM(CASE WHEN coordinates_aligned = 1 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*),0) AS coord_compliance_pct
            FROM fact.revit_health_daily WHERE batch_id = @batch_id;

            SELECT TOP 5 p.project_name, df.file_name_bk, f.health_score, f.health_category, f.total_warnings, f.critical_warnings,
                   f.naming_valid, f.coordinates_aligned, f.grids_aligned, f.levels_aligned
            FROM fact.revit_health_daily f
            LEFT JOIN dbo.projects p ON f.project_key = p.project_id
            INNER JOIN dim.revit_file df ON f.file_name_key = df.revit_file_key
            WHERE f.batch_id = @batch_id
            ORDER BY f.health_score ASC;
        END

        RETURN 0;
    END TRY
    BEGIN CATCH
        IF OBJECT_ID('tempdb..#alignment_checks') IS NOT NULL DROP TABLE #alignment_checks;
        PRINT CONCAT('ERROR in fact load: ', ERROR_MESSAGE());
        PRINT CONCAT('Error Line: ', ERROR_LINE());
        PRINT CONCAT('Error Procedure: ', ERROR_PROCEDURE());
        RETURN 1;
    END CATCH
END;
GO

PRINT 'Successfully created procedure: warehouse.usp_load_fact_revit_health_daily';
GO
