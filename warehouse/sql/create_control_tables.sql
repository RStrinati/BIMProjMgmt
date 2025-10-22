/*
    Control & Metadata Tables for Warehouse Operations
*/

USE [ProjectManagement];
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'ctl')
BEGIN
    EXEC('CREATE SCHEMA ctl AUTHORIZATION dbo;');
END
GO

/* WATERMARK TABLE */
IF OBJECT_ID('ctl.watermark', 'U') IS NULL
BEGIN
    CREATE TABLE ctl.watermark (
        process_name    NVARCHAR(100) NOT NULL,
        source_object   NVARCHAR(255) NOT NULL,
        watermark_value DATETIME2     NULL,
        row_count       BIGINT        NULL,
        updated_at      DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT pk_ctl_watermark PRIMARY KEY (process_name, source_object)
    );
END
GO

/* ETL RUN AUDIT */
IF OBJECT_ID('ctl.etl_run', 'U') IS NULL
BEGIN
    CREATE TABLE ctl.etl_run (
        run_id        BIGINT       NOT NULL IDENTITY(1,1) PRIMARY KEY,
        pipeline_name NVARCHAR(100) NOT NULL,
        status        NVARCHAR(20)  NOT NULL,
        started_at    DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        completed_at  DATETIME2     NULL,
        message       NVARCHAR(MAX) NULL
    );
END
GO

/* DATA QUALITY RESULTS */
IF OBJECT_ID('ctl.data_quality_result', 'U') IS NULL
BEGIN
    CREATE TABLE ctl.data_quality_result (
        dq_result_id BIGINT       NOT NULL IDENTITY(1,1) PRIMARY KEY,
        run_id       BIGINT       NOT NULL,
        check_name   NVARCHAR(255) NOT NULL,
        severity     NVARCHAR(20)  NOT NULL,
        passed       BIT           NOT NULL,
        details      NVARCHAR(MAX) NULL,
        checked_at   DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT fk_dq_run FOREIGN KEY (run_id) REFERENCES ctl.etl_run(run_id)
    );
END
GO
