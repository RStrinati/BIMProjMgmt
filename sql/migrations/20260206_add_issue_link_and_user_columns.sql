USE ProjectManagement;
GO

IF COL_LENGTH('stg.issues', 'created_by') IS NULL
BEGIN
    ALTER TABLE stg.issues ADD created_by NVARCHAR(255) NULL;
END
IF COL_LENGTH('stg.issues', 'updated_by') IS NULL
BEGIN
    ALTER TABLE stg.issues ADD updated_by NVARCHAR(255) NULL;
END
IF COL_LENGTH('stg.issues', 'closed_by') IS NULL
BEGIN
    ALTER TABLE stg.issues ADD closed_by NVARCHAR(255) NULL;
END
IF COL_LENGTH('stg.issues', 'linked_document_urn') IS NULL
BEGIN
    ALTER TABLE stg.issues ADD linked_document_urn NVARCHAR(255) NULL;
END
IF COL_LENGTH('stg.issues', 'snapshot_urn') IS NULL
BEGIN
    ALTER TABLE stg.issues ADD snapshot_urn NVARCHAR(255) NULL;
END
IF COL_LENGTH('stg.issues', 'web_link') IS NULL
BEGIN
    ALTER TABLE stg.issues ADD web_link NVARCHAR(1000) NULL;
END
IF COL_LENGTH('stg.issues', 'preview_middle_url') IS NULL
BEGIN
    ALTER TABLE stg.issues ADD preview_middle_url NVARCHAR(1000) NULL;
END
GO

IF COL_LENGTH('dim.issue', 'created_by') IS NULL
BEGIN
    ALTER TABLE dim.issue ADD created_by NVARCHAR(255) NULL;
END
IF COL_LENGTH('dim.issue', 'updated_by') IS NULL
BEGIN
    ALTER TABLE dim.issue ADD updated_by NVARCHAR(255) NULL;
END
IF COL_LENGTH('dim.issue', 'closed_by') IS NULL
BEGIN
    ALTER TABLE dim.issue ADD closed_by NVARCHAR(255) NULL;
END
IF COL_LENGTH('dim.issue', 'linked_document_urn') IS NULL
BEGIN
    ALTER TABLE dim.issue ADD linked_document_urn NVARCHAR(255) NULL;
END
IF COL_LENGTH('dim.issue', 'snapshot_urn') IS NULL
BEGIN
    ALTER TABLE dim.issue ADD snapshot_urn NVARCHAR(255) NULL;
END
IF COL_LENGTH('dim.issue', 'web_link') IS NULL
BEGIN
    ALTER TABLE dim.issue ADD web_link NVARCHAR(1000) NULL;
END
IF COL_LENGTH('dim.issue', 'preview_middle_url') IS NULL
BEGIN
    ALTER TABLE dim.issue ADD preview_middle_url NVARCHAR(1000) NULL;
END
GO

IF COL_LENGTH('dbo.Issues_Snapshots', 'created_by') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Snapshots ADD created_by NVARCHAR(255) NULL;
END
IF COL_LENGTH('dbo.Issues_Snapshots', 'updated_by') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Snapshots ADD updated_by NVARCHAR(255) NULL;
END
IF COL_LENGTH('dbo.Issues_Snapshots', 'closed_by') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Snapshots ADD closed_by NVARCHAR(255) NULL;
END
IF COL_LENGTH('dbo.Issues_Snapshots', 'linked_document_urn') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Snapshots ADD linked_document_urn NVARCHAR(255) NULL;
END
IF COL_LENGTH('dbo.Issues_Snapshots', 'snapshot_urn') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Snapshots ADD snapshot_urn NVARCHAR(255) NULL;
END
IF COL_LENGTH('dbo.Issues_Snapshots', 'web_link') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Snapshots ADD web_link NVARCHAR(1000) NULL;
END
IF COL_LENGTH('dbo.Issues_Snapshots', 'preview_middle_url') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Snapshots ADD preview_middle_url NVARCHAR(1000) NULL;
END
GO

IF COL_LENGTH('dbo.Issues_Current', 'created_by') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Current ADD created_by NVARCHAR(255) NULL;
END
IF COL_LENGTH('dbo.Issues_Current', 'updated_by') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Current ADD updated_by NVARCHAR(255) NULL;
END
IF COL_LENGTH('dbo.Issues_Current', 'closed_by') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Current ADD closed_by NVARCHAR(255) NULL;
END
IF COL_LENGTH('dbo.Issues_Current', 'linked_document_urn') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Current ADD linked_document_urn NVARCHAR(255) NULL;
END
IF COL_LENGTH('dbo.Issues_Current', 'snapshot_urn') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Current ADD snapshot_urn NVARCHAR(255) NULL;
END
IF COL_LENGTH('dbo.Issues_Current', 'web_link') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Current ADD web_link NVARCHAR(1000) NULL;
END
IF COL_LENGTH('dbo.Issues_Current', 'preview_middle_url') IS NULL
BEGIN
    ALTER TABLE dbo.Issues_Current ADD preview_middle_url NVARCHAR(1000) NULL;
END
GO
