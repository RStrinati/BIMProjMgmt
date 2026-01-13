USE ProjectManagement;
GO

IF OBJECT_ID('dbo.Issues_Snapshots', 'U') IS NOT NULL
BEGIN
    IF COL_LENGTH('dbo.Issues_Snapshots', 'assignee_user_key') IS NULL
    BEGIN
        ALTER TABLE dbo.Issues_Snapshots
            ADD assignee_user_key NVARCHAR(255) NULL;
    END
END
GO
