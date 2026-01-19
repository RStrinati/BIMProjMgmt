-- Migration: Add service template bindings and generated keys
-- Scope: ProjectManagement database
-- Rollback: Drop new columns/table if needed.

IF OBJECT_ID('dbo.ProjectServiceTemplateBindings', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.ProjectServiceTemplateBindings (
        binding_id INT IDENTITY PRIMARY KEY,
        project_id INT NOT NULL REFERENCES dbo.Projects(project_id) ON DELETE CASCADE,
        service_id INT NOT NULL REFERENCES dbo.ProjectServices(service_id) ON DELETE CASCADE,
        template_id NVARCHAR(100) NOT NULL,
        template_version NVARCHAR(50) NOT NULL,
        template_hash NVARCHAR(64) NOT NULL,
        options_enabled NVARCHAR(MAX) NULL,
        applied_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        applied_by_user_id INT NULL REFERENCES dbo.Users(user_id)
    );
END;

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'UX_ProjectServiceTemplateBindings_ServiceId'
      AND object_id = OBJECT_ID('dbo.ProjectServiceTemplateBindings')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_ProjectServiceTemplateBindings_ServiceId
        ON dbo.ProjectServiceTemplateBindings(service_id);
END;

IF COL_LENGTH('dbo.ServiceReviews', 'project_id') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceReviews
        ADD project_id INT NULL;
END;

IF COL_LENGTH('dbo.ServiceReviews', 'generated_from_template_id') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceReviews
        ADD generated_from_template_id NVARCHAR(100) NULL;
END;

IF COL_LENGTH('dbo.ServiceReviews', 'generated_from_template_version') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceReviews
        ADD generated_from_template_version NVARCHAR(50) NULL;
END;

IF COL_LENGTH('dbo.ServiceReviews', 'generated_key') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceReviews
        ADD generated_key NVARCHAR(200) NULL;
END;

GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'UX_ServiceReviews_GeneratedKey'
      AND object_id = OBJECT_ID('dbo.ServiceReviews')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_ServiceReviews_GeneratedKey
        ON dbo.ServiceReviews(service_id, generated_key)
        WHERE generated_key IS NOT NULL;
END;

IF COL_LENGTH('dbo.ServiceItems', 'project_id') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceItems
        ADD project_id INT NULL;
END;

IF COL_LENGTH('dbo.ServiceItems', 'generated_from_template_id') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceItems
        ADD generated_from_template_id NVARCHAR(100) NULL;
END;

IF COL_LENGTH('dbo.ServiceItems', 'generated_from_template_version') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceItems
        ADD generated_from_template_version NVARCHAR(50) NULL;
END;

IF COL_LENGTH('dbo.ServiceItems', 'generated_key') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceItems
        ADD generated_key NVARCHAR(200) NULL;
END;

GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'UX_ServiceItems_GeneratedKey'
      AND object_id = OBJECT_ID('dbo.ServiceItems')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_ServiceItems_GeneratedKey
        ON dbo.ServiceItems(service_id, generated_key)
        WHERE generated_key IS NOT NULL;
END;
