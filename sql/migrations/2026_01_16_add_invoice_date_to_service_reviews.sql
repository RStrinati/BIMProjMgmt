-- =====================================================================
-- Migration: Add invoice_date column to ServiceReviews
-- =====================================================================
-- Date: 2026-01-16
-- Purpose: Support billing date tracking separate from review dates
-- Scope: ProjectManagement database, dbo.ServiceReviews table
-- Type: Additive (non-destructive)
-- Rollback: ALTER TABLE dbo.ServiceReviews DROP COLUMN invoice_date;
-- =====================================================================

USE [ProjectManagement];
GO

-- Add invoice_date column if it doesn't already exist
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_NAME = 'ServiceReviews' AND COLUMN_NAME = 'invoice_date'
)
BEGIN
  ALTER TABLE dbo.ServiceReviews
  ADD invoice_date DATE NULL;
  
  PRINT 'Column invoice_date added to dbo.ServiceReviews.';
END
ELSE
BEGIN
  PRINT 'Column invoice_date already exists on dbo.ServiceReviews. No changes made.';
END;

-- Create index for performance on invoice_date queries
IF NOT EXISTS (
  SELECT 1 FROM sys.indexes 
  WHERE NAME = 'idx_ServiceReviews_invoice_date' AND object_id = OBJECT_ID('dbo.ServiceReviews')
)
BEGIN
  CREATE NONCLUSTERED INDEX idx_ServiceReviews_invoice_date
    ON dbo.ServiceReviews(invoice_date);
  
  PRINT 'Index idx_ServiceReviews_invoice_date created.';
END
ELSE
BEGIN
  PRINT 'Index idx_ServiceReviews_invoice_date already exists.';
END;

-- Verify the column was added
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'ServiceReviews' AND COLUMN_NAME = 'invoice_date';

GO
