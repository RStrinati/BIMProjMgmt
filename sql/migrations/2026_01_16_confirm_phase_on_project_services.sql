-- =====================================================================
-- Migration: Confirm or Add phase column to ProjectServices
-- =====================================================================
-- Date: 2026-01-16
-- Purpose: Establish phase as single source of truth for service grouping
-- Scope: ProjectManagement database, dbo.ProjectServices table
-- Type: Additive (non-destructive) with idempotency check
-- Rollback: ALTER TABLE dbo.ProjectServices DROP COLUMN phase;
-- =====================================================================

USE [ProjectManagement];
GO

-- Check if phase column exists; add if missing
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_NAME = 'ProjectServices' AND COLUMN_NAME = 'phase'
)
BEGIN
  ALTER TABLE dbo.ProjectServices
  ADD phase NVARCHAR(100) NULL;
  
  PRINT 'Column phase added to dbo.ProjectServices.';
END
ELSE
BEGIN
  PRINT 'Column phase already exists on dbo.ProjectServices. Skipping ALTER TABLE.';
END;

-- Create index on phase for filtering performance
IF NOT EXISTS (
  SELECT 1 FROM sys.indexes 
  WHERE NAME = 'idx_ProjectServices_phase' AND object_id = OBJECT_ID('dbo.ProjectServices')
)
BEGIN
  CREATE NONCLUSTERED INDEX idx_ProjectServices_phase
    ON dbo.ProjectServices(phase);
  
  PRINT 'Index idx_ProjectServices_phase created.';
END
ELSE
BEGIN
  PRINT 'Index idx_ProjectServices_phase already exists.';
END;

-- Verify the column exists and report on current values
SELECT 
  COUNT(*) AS total_services,
  SUM(CASE WHEN phase IS NULL THEN 1 ELSE 0 END) AS phase_null_count,
  SUM(CASE WHEN phase IS NOT NULL THEN 1 ELSE 0 END) AS phase_populated_count
FROM dbo.ProjectServices;

-- Display unique phase values (if populated)
SELECT DISTINCT phase
FROM dbo.ProjectServices
WHERE phase IS NOT NULL
ORDER BY phase;

GO
