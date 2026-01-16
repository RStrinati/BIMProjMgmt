-- =====================================================================
-- Migration: Add invoice_date column to ServiceItems
-- =====================================================================
-- Date: 2026-01-16
-- Purpose: Support billing date tracking for service items (if included in Deliverables)
-- Scope: ProjectManagement database, dbo.ServiceItems table
-- Type: Additive (non-destructive)
-- Rollback: ALTER TABLE dbo.ServiceItems DROP COLUMN invoice_date;
-- =====================================================================

USE [ProjectManagement];
GO

-- Add invoice_date column if it doesn't already exist
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_NAME = 'ServiceItems' AND COLUMN_NAME = 'invoice_date'
)
BEGIN
  ALTER TABLE dbo.ServiceItems
  ADD invoice_date DATE NULL;
  
  PRINT 'Column invoice_date added to dbo.ServiceItems.';
END
ELSE
BEGIN
  PRINT 'Column invoice_date already exists on dbo.ServiceItems. No changes made.';
END;

-- Create index for performance on invoice_date queries
IF NOT EXISTS (
  SELECT 1 FROM sys.indexes 
  WHERE NAME = 'idx_ServiceItems_invoice_date' AND object_id = OBJECT_ID('dbo.ServiceItems')
)
BEGIN
  CREATE NONCLUSTERED INDEX idx_ServiceItems_invoice_date
    ON dbo.ServiceItems(invoice_date);
  
  PRINT 'Index idx_ServiceItems_invoice_date created.';
END
ELSE
BEGIN
  PRINT 'Index idx_ServiceItems_invoice_date already exists.';
END;

-- Verify the column was added
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'ServiceItems' AND COLUMN_NAME = 'invoice_date';

GO
