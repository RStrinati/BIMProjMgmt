USE ProjectManagement;
GO

IF COL_LENGTH('dim.issue', 'issue_link') IS NULL
BEGIN
    ALTER TABLE dim.issue ADD issue_link NVARCHAR(1000) NULL;
END
IF COL_LENGTH('dim.issue', 'snapshot_preview_url') IS NULL
BEGIN
    ALTER TABLE dim.issue ADD snapshot_preview_url NVARCHAR(1000) NULL;
END
GO

IF COL_LENGTH('dbo.Issues_Snapshots', 'issue_link') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Snapshots ADD issue_link NVARCHAR(1000) NULL;
END
IF COL_LENGTH('dbo.Issues_Snapshots', 'snapshot_preview_url') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Snapshots ADD snapshot_preview_url NVARCHAR(1000) NULL;
END
GO

IF COL_LENGTH('dbo.Issues_Current', 'issue_link') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Current ADD issue_link NVARCHAR(1000) NULL;
END
IF COL_LENGTH('dbo.Issues_Current', 'snapshot_preview_url') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Current ADD snapshot_preview_url NVARCHAR(1000) NULL;
END
GO
