USE ProjectManagement;
GO

IF OBJECT_ID('dbo.revizto_project_map', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.revizto_project_map (
        map_id              INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        revizto_project_uuid NVARCHAR(100) NOT NULL,
        pm_project_id       INT            NULL,
        project_name_override NVARCHAR(510) NULL,
        is_active           BIT            NOT NULL CONSTRAINT DF_revizto_project_map_active DEFAULT 1,
        created_at          DATETIME2      NOT NULL CONSTRAINT DF_revizto_project_map_created_at DEFAULT SYSUTCDATETIME(),
        updated_at          DATETIME2      NULL
    );
END
GO
