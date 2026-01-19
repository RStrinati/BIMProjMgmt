-- Migration: Service template v1.1 columns (origin, managed flags, options json, sort order)
-- Scope: ProjectManagement database

IF COL_LENGTH('dbo.ProjectServiceTemplateBindings', 'options_enabled_json') IS NULL
BEGIN
    ALTER TABLE dbo.ProjectServiceTemplateBindings
        ADD options_enabled_json NVARCHAR(MAX) NULL;
END;

IF COL_LENGTH('dbo.ProjectServiceTemplateBindings', 'options_enabled') IS NOT NULL
BEGIN
    UPDATE dbo.ProjectServiceTemplateBindings
    SET options_enabled_json = options_enabled
    WHERE options_enabled_json IS NULL
      AND options_enabled IS NOT NULL;
END;

IF COL_LENGTH('dbo.ServiceItems', 'origin') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceItems
        ADD origin NVARCHAR(32) NULL;
END;

IF COL_LENGTH('dbo.ServiceItems', 'is_template_managed') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceItems
        ADD is_template_managed BIT NULL;
END;

IF COL_LENGTH('dbo.ServiceItems', 'sort_order') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceItems
        ADD sort_order INT NULL;
END;

IF COL_LENGTH('dbo.ServiceReviews', 'origin') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceReviews
        ADD origin NVARCHAR(32) NULL;
END;

IF COL_LENGTH('dbo.ServiceReviews', 'is_template_managed') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceReviews
        ADD is_template_managed BIT NULL;
END;

IF COL_LENGTH('dbo.ServiceReviews', 'sort_order') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceReviews
        ADD sort_order INT NULL;
END;
