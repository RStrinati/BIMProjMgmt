-- =====================================================================
-- Migration: Add project_overview_summaries table
-- =====================================================================
-- Date: 2026-02-20
-- Purpose: Store generated overview summaries (human-readable + JSON snapshot)
-- Scope: ProjectManagement database
-- Type: Additive (non-destructive)
-- Rollback: Drop table project_overview_summaries
-- =====================================================================

USE [ProjectManagement];
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.tables WHERE name = 'project_overview_summaries' AND schema_id = SCHEMA_ID('dbo')
)
BEGIN
  CREATE TABLE dbo.project_overview_summaries (
    summary_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    project_id INT NOT NULL,
    summary_month CHAR(7) NULL,
    summary_text NVARCHAR(MAX) NOT NULL,
    summary_json NVARCHAR(MAX) NULL,
    generated_at DATETIME2 NOT NULL CONSTRAINT DF_project_overview_summaries_generated_at DEFAULT (SYSUTCDATETIME()),
    generated_by NVARCHAR(100) NULL
  );

  PRINT 'Table dbo.project_overview_summaries created.';
END
ELSE
BEGIN
  PRINT 'Table dbo.project_overview_summaries already exists.';
END;

IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_project_overview_summaries_project'
)
BEGIN
  ALTER TABLE dbo.project_overview_summaries
  ADD CONSTRAINT FK_project_overview_summaries_project
  FOREIGN KEY (project_id) REFERENCES dbo.projects(project_id);
END;

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE name = 'IX_project_overview_summaries_project_month'
    AND object_id = OBJECT_ID('dbo.project_overview_summaries')
)
BEGIN
  CREATE NONCLUSTERED INDEX IX_project_overview_summaries_project_month
    ON dbo.project_overview_summaries(project_id, summary_month, generated_at DESC);
END;

PRINT 'project_overview_summaries migration complete.';
GO
