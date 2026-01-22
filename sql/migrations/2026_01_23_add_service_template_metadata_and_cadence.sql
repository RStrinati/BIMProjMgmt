-- Migration: Add service template metadata, cadence anchors, and user edit tracking
-- Scope: ProjectManagement database
-- Rollback: Drop new columns/indexes if needed.

IF COL_LENGTH('dbo.ProjectServices', 'source_template_id') IS NULL
BEGIN
    ALTER TABLE dbo.ProjectServices
        ADD source_template_id NVARCHAR(100) NULL;
END;

IF COL_LENGTH('dbo.ProjectServices', 'source_template_version') IS NULL
BEGIN
    ALTER TABLE dbo.ProjectServices
        ADD source_template_version NVARCHAR(50) NULL;
END;

IF COL_LENGTH('dbo.ProjectServices', 'source_template_hash') IS NULL
BEGIN
    ALTER TABLE dbo.ProjectServices
        ADD source_template_hash NVARCHAR(64) NULL;
END;

IF COL_LENGTH('dbo.ProjectServices', 'template_mode') IS NULL
BEGIN
    ALTER TABLE dbo.ProjectServices
        ADD template_mode NVARCHAR(20) NULL;
END;

IF COL_LENGTH('dbo.ProjectServices', 'start_date') IS NULL
BEGIN
    ALTER TABLE dbo.ProjectServices
        ADD start_date DATE NULL;
END;

IF COL_LENGTH('dbo.ProjectServices', 'end_date') IS NULL
BEGIN
    ALTER TABLE dbo.ProjectServices
        ADD end_date DATE NULL;
END;

IF COL_LENGTH('dbo.ProjectServices', 'review_anchor_date') IS NULL
BEGIN
    ALTER TABLE dbo.ProjectServices
        ADD review_anchor_date DATE NULL;
END;

IF COL_LENGTH('dbo.ProjectServices', 'review_interval_days') IS NULL
BEGIN
    ALTER TABLE dbo.ProjectServices
        ADD review_interval_days INT NULL;
END;

IF COL_LENGTH('dbo.ProjectServices', 'review_count_planned') IS NULL
BEGIN
    ALTER TABLE dbo.ProjectServices
        ADD review_count_planned INT NULL;
END;

IF COL_LENGTH('dbo.ServiceReviews', 'template_node_key') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceReviews
        ADD template_node_key NVARCHAR(200) NULL;
END;

IF COL_LENGTH('dbo.ServiceReviews', 'is_user_modified') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceReviews
        ADD is_user_modified BIT NOT NULL CONSTRAINT DF_ServiceReviews_IsUserModified DEFAULT 0;
END;

IF COL_LENGTH('dbo.ServiceReviews', 'user_modified_at') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceReviews
        ADD user_modified_at DATETIME2 NULL;
END;

IF COL_LENGTH('dbo.ServiceReviews', 'user_modified_fields') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceReviews
        ADD user_modified_fields NVARCHAR(MAX) NULL;
END;

IF COL_LENGTH('dbo.ServiceItems', 'template_node_key') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceItems
        ADD template_node_key NVARCHAR(200) NULL;
END;

IF COL_LENGTH('dbo.ServiceItems', 'is_user_modified') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceItems
        ADD is_user_modified BIT NOT NULL CONSTRAINT DF_ServiceItems_IsUserModified DEFAULT 0;
END;

IF COL_LENGTH('dbo.ServiceItems', 'user_modified_at') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceItems
        ADD user_modified_at DATETIME2 NULL;
END;

IF COL_LENGTH('dbo.ServiceItems', 'user_modified_fields') IS NULL
BEGIN
    ALTER TABLE dbo.ServiceItems
        ADD user_modified_fields NVARCHAR(MAX) NULL;
END;

GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'UX_ServiceReviews_TemplateNodeKey'
      AND object_id = OBJECT_ID('dbo.ServiceReviews')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_ServiceReviews_TemplateNodeKey
        ON dbo.ServiceReviews(service_id, template_node_key)
        WHERE template_node_key IS NOT NULL;
END;

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'UX_ServiceItems_TemplateNodeKey'
      AND object_id = OBJECT_ID('dbo.ServiceItems')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_ServiceItems_TemplateNodeKey
        ON dbo.ServiceItems(service_id, template_node_key)
        WHERE template_node_key IS NOT NULL;
END;
