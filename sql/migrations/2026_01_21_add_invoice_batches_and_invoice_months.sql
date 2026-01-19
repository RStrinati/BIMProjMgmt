-- =====================================================================
-- Migration: Add invoice months + invoice batches for deliverables
-- =====================================================================
-- Date: 2026-01-21
-- Purpose: Support invoice month derivation, overrides, and batching
-- Scope: ProjectManagement database
-- Type: Additive (non-destructive)
-- Rollback: Drop columns/table/views added here
-- =====================================================================

USE [ProjectManagement];
GO

-- Add invoice month + batch columns to ServiceReviews
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_NAME = 'ServiceReviews' AND COLUMN_NAME = 'invoice_month_override'
)
BEGIN
  ALTER TABLE dbo.ServiceReviews
  ADD invoice_month_override CHAR(7) NULL;
  PRINT 'Column invoice_month_override added to dbo.ServiceReviews.';
END
ELSE
BEGIN
  PRINT 'Column invoice_month_override already exists on dbo.ServiceReviews.';
END;

IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_NAME = 'ServiceReviews' AND COLUMN_NAME = 'invoice_month_auto'
)
BEGIN
  ALTER TABLE dbo.ServiceReviews
  ADD invoice_month_auto CHAR(7) NULL;
  PRINT 'Column invoice_month_auto added to dbo.ServiceReviews.';
END
ELSE
BEGIN
  PRINT 'Column invoice_month_auto already exists on dbo.ServiceReviews.';
END;

IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_NAME = 'ServiceReviews' AND COLUMN_NAME = 'invoice_month_final'
)
BEGIN
  ALTER TABLE dbo.ServiceReviews
  ADD invoice_month_final CHAR(7) NULL;
  PRINT 'Column invoice_month_final added to dbo.ServiceReviews.';
END
ELSE
BEGIN
  PRINT 'Column invoice_month_final already exists on dbo.ServiceReviews.';
END;

IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_NAME = 'ServiceReviews' AND COLUMN_NAME = 'invoice_batch_id'
)
BEGIN
  ALTER TABLE dbo.ServiceReviews
  ADD invoice_batch_id INT NULL;
  PRINT 'Column invoice_batch_id added to dbo.ServiceReviews.';
END
ELSE
BEGIN
  PRINT 'Column invoice_batch_id already exists on dbo.ServiceReviews.';
END;

-- Create InvoiceBatches table
IF NOT EXISTS (
  SELECT 1 FROM sys.tables WHERE name = 'InvoiceBatches' AND schema_id = SCHEMA_ID('dbo')
)
BEGIN
  CREATE TABLE dbo.InvoiceBatches (
    invoice_batch_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    project_id INT NOT NULL,
    service_id INT NULL,
    invoice_month CHAR(7) NOT NULL,
    status VARCHAR(20) NOT NULL CONSTRAINT DF_InvoiceBatches_status DEFAULT ('draft'),
    title NVARCHAR(200) NULL,
    notes NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_InvoiceBatches_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_InvoiceBatches_updated_at DEFAULT (SYSUTCDATETIME())
  );

  PRINT 'Table dbo.InvoiceBatches created.';
END
ELSE
BEGIN
  PRINT 'Table dbo.InvoiceBatches already exists.';
END;

-- Add foreign keys if missing
IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_InvoiceBatches_Project'
)
BEGIN
  ALTER TABLE dbo.InvoiceBatches
  ADD CONSTRAINT FK_InvoiceBatches_Project
  FOREIGN KEY (project_id) REFERENCES dbo.projects(project_id);
END;

IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_InvoiceBatches_Service'
)
BEGIN
  ALTER TABLE dbo.InvoiceBatches
  ADD CONSTRAINT FK_InvoiceBatches_Service
  FOREIGN KEY (service_id) REFERENCES dbo.ProjectServices(service_id);
END;

IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_ServiceReviews_InvoiceBatch'
)
BEGIN
  ALTER TABLE dbo.ServiceReviews
  ADD CONSTRAINT FK_ServiceReviews_InvoiceBatch
  FOREIGN KEY (invoice_batch_id) REFERENCES dbo.InvoiceBatches(invoice_batch_id);
END;

-- Backfill invoice_month_auto/final from due_date
UPDATE dbo.ServiceReviews
SET invoice_month_auto = FORMAT(due_date, 'yyyy-MM')
WHERE due_date IS NOT NULL AND invoice_month_auto IS NULL;

UPDATE dbo.ServiceReviews
SET invoice_month_final = COALESCE(invoice_month_override, invoice_month_auto)
WHERE invoice_month_final IS NULL AND (invoice_month_override IS NOT NULL OR invoice_month_auto IS NOT NULL);

-- Indexes for invoice month/batching
IF NOT EXISTS (
  SELECT 1 FROM sys.indexes 
  WHERE NAME = 'idx_ServiceReviews_invoice_month_final' AND object_id = OBJECT_ID('dbo.ServiceReviews')
)
BEGIN
  CREATE NONCLUSTERED INDEX idx_ServiceReviews_invoice_month_final
    ON dbo.ServiceReviews(invoice_month_final);
END;

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes 
  WHERE NAME = 'idx_ServiceReviews_invoice_batch_id' AND object_id = OBJECT_ID('dbo.ServiceReviews')
)
BEGIN
  CREATE NONCLUSTERED INDEX idx_ServiceReviews_invoice_batch_id
    ON dbo.ServiceReviews(invoice_batch_id);
END;

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes 
  WHERE NAME = 'idx_InvoiceBatches_project_month' AND object_id = OBJECT_ID('dbo.InvoiceBatches')
)
BEGIN
  CREATE NONCLUSTERED INDEX idx_InvoiceBatches_project_month
    ON dbo.InvoiceBatches(project_id, invoice_month);
END;

-- Invoice pipeline by project/month
DROP VIEW IF EXISTS dbo.vw_invoice_pipeline_by_project_month;
GO

CREATE VIEW dbo.vw_invoice_pipeline_by_project_month AS
SELECT
  ps.project_id,
  COALESCE(
    sr.invoice_month_final,
    sr.invoice_month_override,
    sr.invoice_month_auto,
    CASE WHEN sr.due_date IS NOT NULL THEN FORMAT(sr.due_date, 'yyyy-MM') END
  ) AS invoice_month,
  COUNT(*) AS deliverables_count,
  SUM(CAST(ISNULL(sr.billing_amount, 0) AS DECIMAL(18,4))) AS total_amount,
  SUM(CASE WHEN (sr.status = 'completed' OR sr.status = 'ready') AND ISNULL(sr.is_billed, 0) = 0 THEN 1 ELSE 0 END) AS ready_count,
  SUM(CASE WHEN (sr.status = 'completed' OR sr.status = 'ready') AND ISNULL(sr.is_billed, 0) = 0
      THEN CAST(ISNULL(sr.billing_amount, 0) AS DECIMAL(18,4)) ELSE 0 END) AS ready_amount,
  SUM(CASE WHEN ISNULL(sr.is_billed, 0) = 1 OR ib.status = 'issued' THEN 1 ELSE 0 END) AS issued_count
FROM dbo.ServiceReviews sr
JOIN dbo.ProjectServices ps ON sr.service_id = ps.service_id
LEFT JOIN dbo.InvoiceBatches ib ON sr.invoice_batch_id = ib.invoice_batch_id
WHERE COALESCE(
  sr.invoice_month_final,
  sr.invoice_month_override,
  sr.invoice_month_auto,
  CASE WHEN sr.due_date IS NOT NULL THEN FORMAT(sr.due_date, 'yyyy-MM') END
) IS NOT NULL
GROUP BY ps.project_id,
  COALESCE(
    sr.invoice_month_final,
    sr.invoice_month_override,
    sr.invoice_month_auto,
    CASE WHEN sr.due_date IS NOT NULL THEN FORMAT(sr.due_date, 'yyyy-MM') END
  );
GO

-- Projects finance rollup view
DROP VIEW IF EXISTS dbo.vw_projects_finance_rollup;
GO

CREATE VIEW dbo.vw_projects_finance_rollup AS
SELECT
  p.project_id,
  SUM(CAST(ISNULL(ps.agreed_fee, 0) AS DECIMAL(18,4))) AS agreed_fee,
  SUM(CAST(
    CASE
      WHEN ISNULL(ps.claimed_to_date, 0) > 0 THEN ISNULL(ps.claimed_to_date, 0)
      WHEN ISNULL(ps.agreed_fee, 0) > 0 THEN ISNULL(ps.agreed_fee, 0) * (ISNULL(ps.progress_pct, 0) / 100.0)
      ELSE 0
    END AS DECIMAL(18,4)
  )) AS billed_to_date,
  SUM(CAST(ISNULL(ps.agreed_fee, 0) * (ISNULL(ps.progress_pct, 0) / 100.0) AS DECIMAL(18,4))) AS earned_value,
  CASE
    WHEN SUM(ISNULL(ps.agreed_fee, 0)) > 0
      THEN (SUM(CAST(ISNULL(ps.agreed_fee, 0) * (ISNULL(ps.progress_pct, 0) / 100.0) AS DECIMAL(18,4)))
        / NULLIF(SUM(ISNULL(ps.agreed_fee, 0)), 0)) * 100.0
    ELSE 0
  END AS earned_value_pct
FROM dbo.projects p
LEFT JOIN dbo.ProjectServices ps ON ps.project_id = p.project_id
GROUP BY p.project_id;
GO

PRINT 'Invoice month + batch migration complete.';
GO
