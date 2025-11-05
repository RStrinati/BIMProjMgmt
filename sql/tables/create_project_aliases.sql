USE ProjectManagement;
GO

IF OBJECT_ID('dbo.project_aliases', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.project_aliases (
        pm_project_id INT NOT NULL,
        alias_name    NVARCHAR(510) NOT NULL,
        created_at    DATETIME2(0) NOT NULL CONSTRAINT DF_project_aliases_created_at DEFAULT (SYSDATETIME()),
        CONSTRAINT pk_project_aliases PRIMARY KEY (pm_project_id, alias_name)
    );
END
GO
