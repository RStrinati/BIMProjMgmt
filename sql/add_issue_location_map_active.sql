USE ProjectManagement;
GO

IF COL_LENGTH('dbo.issue_location_map', 'is_active') IS NULL
BEGIN
    ALTER TABLE dbo.issue_location_map
    ADD is_active BIT NOT NULL CONSTRAINT DF_issue_location_map_active DEFAULT 1;
END
GO
