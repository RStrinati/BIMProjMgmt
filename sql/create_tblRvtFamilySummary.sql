/*
    Creates tblRvtFamilySummary to store processed family metadata per
    health check import. Run this once on the RevitHealthCheckDB database.
*/

USE [RevitHealthCheckDB];
GO

IF OBJECT_ID(N'dbo.tblRvtFamilySummary', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.tblRvtFamilySummary (
        id                     INT IDENTITY(1,1) PRIMARY KEY,
        health_check_id        INT            NOT NULL,
        family_name            NVARCHAR(255)  NOT NULL,
        category               NVARCHAR(255)  NULL,
        instance_count         INT            NULL,
        size_mb                DECIMAL(18,4)  NULL,
        file_path              NVARCHAR(500)  NULL,
        shared_parameters_json NVARCHAR(MAX)  NULL,
        created_at             DATETIME2(0)   NOT NULL CONSTRAINT DF_tblRvtFamilySummary_created_at DEFAULT (SYSUTCDATETIME())
    );

    CREATE INDEX IX_tblRvtFamilySummary_HealthCheck
        ON dbo.tblRvtFamilySummary (health_check_id, family_name);
END
GO
