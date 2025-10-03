-- =====================================================================
-- Rollback Migration: Remove Client Snapshot Columns
-- Purpose: Remove snapshot columns from BillingClaims
-- Date: 2025-10-03
-- Use: If 002_add_client_snapshot.sql causes issues
-- =====================================================================

BEGIN TRANSACTION;

PRINT 'Starting client snapshot rollback...';
PRINT '========================================';

-- =====================================================================
-- PHASE 1: Drop view
-- =====================================================================

PRINT '';
PRINT 'PHASE 1: Dropping client history view...';

IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_BillingClaims_WithClientHistory')
BEGIN
    PRINT '  - Dropping vw_BillingClaims_WithClientHistory';
    DROP VIEW vw_BillingClaims_WithClientHistory;
END
ELSE
BEGIN
    PRINT '  - View vw_BillingClaims_WithClientHistory does not exist';
END

-- =====================================================================
-- PHASE 2: Drop index
-- =====================================================================

PRINT '';
PRINT 'PHASE 2: Dropping index...';

IF EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'IX_BillingClaims_ClientSnapshot' 
    AND object_id = OBJECT_ID('BillingClaims')
)
BEGIN
    PRINT '  - Dropping IX_BillingClaims_ClientSnapshot';
    DROP INDEX IX_BillingClaims_ClientSnapshot ON BillingClaims;
END
ELSE
BEGIN
    PRINT '  - Index IX_BillingClaims_ClientSnapshot does not exist';
END

-- =====================================================================
-- PHASE 3: Drop snapshot columns
-- =====================================================================

PRINT '';
PRINT 'PHASE 3: Dropping snapshot columns...';

IF EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('BillingClaims') 
    AND name = 'client_id_snapshot'
)
BEGIN
    PRINT '  - Dropping client_id_snapshot';
    ALTER TABLE BillingClaims DROP COLUMN client_id_snapshot;
END

IF EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('BillingClaims') 
    AND name = 'client_name_snapshot'
)
BEGIN
    PRINT '  - Dropping client_name_snapshot';
    ALTER TABLE BillingClaims DROP COLUMN client_name_snapshot;
END

IF EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('BillingClaims') 
    AND name = 'contract_number_snapshot'
)
BEGIN
    PRINT '  - Dropping contract_number_snapshot';
    ALTER TABLE BillingClaims DROP COLUMN contract_number_snapshot;
END

IF EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('BillingClaims') 
    AND name = 'contract_value_snapshot'
)
BEGIN
    PRINT '  - Dropping contract_value_snapshot';
    ALTER TABLE BillingClaims DROP COLUMN contract_value_snapshot;
END

-- =====================================================================
-- PHASE 4: Validation
-- =====================================================================

PRINT '';
PRINT 'PHASE 4: Validating rollback...';

DECLARE @snapshot_columns INT;
SELECT @snapshot_columns = COUNT(*)
FROM sys.columns 
WHERE object_id = OBJECT_ID('BillingClaims') 
AND name LIKE '%snapshot%';

PRINT '  - Remaining snapshot columns: ' + CAST(@snapshot_columns AS NVARCHAR(10));
PRINT '    (Should be 0 after rollback)';

-- =====================================================================
-- COMMIT or ROLLBACK
-- =====================================================================

-- Uncomment one of the following:

-- COMMIT TRANSACTION;
-- PRINT '';
-- PRINT '✅ SUCCESS: Client snapshot rollback completed';
-- PRINT '';
-- PRINT 'WARNING: Historical client data has been permanently lost!';
-- PRINT 'WARNING: Existing billing claims will only show current client (not historical)';

ROLLBACK TRANSACTION;
PRINT '';
PRINT '⚠️  ROLLED BACK: Review the output above, then change ROLLBACK to COMMIT';
PRINT '';
PRINT 'WARNING: Proceeding will permanently delete client snapshot data!';

GO
