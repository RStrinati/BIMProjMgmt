USE ProjectManagement;
GO

IF COL_LENGTH('stg.issues', 'source_issue_id') IS NULL
    ALTER TABLE stg.issues ADD source_issue_id NVARCHAR(255) NULL;
GO

IF COL_LENGTH('stg.issues', 'source_project_id') IS NULL
    ALTER TABLE stg.issues ADD source_project_id NVARCHAR(255) NULL;
GO

IF COL_LENGTH('stg.issues', 'status_normalized') IS NULL
    ALTER TABLE stg.issues ADD status_normalized NVARCHAR(50) NULL;
GO

IF COL_LENGTH('stg.issues', 'is_deleted') IS NULL
    ALTER TABLE stg.issues ADD is_deleted BIT NULL;
GO

IF COL_LENGTH('stg.issues', 'project_mapped') IS NULL
    ALTER TABLE stg.issues ADD project_mapped BIT NULL;
GO

IF COL_LENGTH('dim.issue', 'source_issue_id') IS NULL
    ALTER TABLE dim.issue ADD source_issue_id NVARCHAR(255) NULL;
GO

IF COL_LENGTH('dim.issue', 'source_project_id') IS NULL
    ALTER TABLE dim.issue ADD source_project_id NVARCHAR(255) NULL;
GO

IF COL_LENGTH('dim.issue', 'status_normalized') IS NULL
    ALTER TABLE dim.issue ADD status_normalized NVARCHAR(50) NULL;
GO

IF COL_LENGTH('dim.issue', 'is_deleted') IS NULL
    ALTER TABLE dim.issue ADD is_deleted BIT NULL;
GO

IF COL_LENGTH('dim.issue', 'project_mapped') IS NULL
    ALTER TABLE dim.issue ADD project_mapped BIT NULL;
GO
