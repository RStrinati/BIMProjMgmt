USE acc_data_schema;
GO

IF COL_LENGTH('staging.issues_issues', 'source_load_ts') IS NULL
BEGIN
    ALTER TABLE staging.issues_issues
        ADD source_load_ts DATETIME2 NOT NULL
            CONSTRAINT DF_staging_issues_issues_source_load_ts DEFAULT SYSUTCDATETIME();
END
GO

IF COL_LENGTH('dbo.issues_issues', 'source_load_ts') IS NULL
BEGIN
    ALTER TABLE dbo.issues_issues
        ADD source_load_ts DATETIME2 NOT NULL
            CONSTRAINT DF_dbo_issues_issues_source_load_ts DEFAULT SYSUTCDATETIME();
END
GO
