-- =====================================================================
-- Migration: Add Client Snapshot Columns to BillingClaims
-- Purpose: Preserve historical client data when projects change ownership
-- Date: 2025-10-03
-- Risk: LOW - Adding nullable columns, backward compatible
-- Rollback: See 002_rollback_client_snapshot.sql
-- =====================================================================

-- IMPORTANT: Backup recommended before schema changes
-- BACKUP DATABASE ProjectManagement TO DISK='backup_pre_client_snapshot.bak';

BEGIN TRANSACTION;

PRINT 'Starting client snapshot migration...';
PRINT '========================================';

-- =====================================================================
-- PHASE 1: Add client snapshot columns to BillingClaims
-- =====================================================================

PRINT '';
PRINT 'PHASE 1: Adding client snapshot columns...';

-- Add client_id_snapshot
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('BillingClaims') 
    AND name = 'client_id_snapshot'
)
BEGIN
    PRINT '  - Adding client_id_snapshot INT NULL';
    ALTER TABLE BillingClaims
    ADD client_id_snapshot INT NULL;
END
ELSE
BEGIN
    PRINT '  - Column client_id_snapshot already exists';
END

-- Add client_name_snapshot
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('BillingClaims') 
    AND name = 'client_name_snapshot'
)
BEGIN
    PRINT '  - Adding client_name_snapshot NVARCHAR(255) NULL';
    ALTER TABLE BillingClaims
    ADD client_name_snapshot NVARCHAR(255) NULL;
END
ELSE
BEGIN
    PRINT '  - Column client_name_snapshot already exists';
END

-- Add contract_number_snapshot
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('BillingClaims') 
    AND name = 'contract_number_snapshot'
)
BEGIN
    PRINT '  - Adding contract_number_snapshot NVARCHAR(100) NULL';
    ALTER TABLE BillingClaims
    ADD contract_number_snapshot NVARCHAR(100) NULL;
END
ELSE
BEGIN
    PRINT '  - Column contract_number_snapshot already exists';
END

-- Add contract_value_snapshot
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('BillingClaims') 
    AND name = 'contract_value_snapshot'
)
BEGIN
    PRINT '  - Adding contract_value_snapshot DECIMAL(18,2) NULL';
    ALTER TABLE BillingClaims
    ADD contract_value_snapshot DECIMAL(18,2) NULL;
END
ELSE
BEGIN
    PRINT '  - Column contract_value_snapshot already exists';
END

-- =====================================================================
-- PHASE 2: Backfill existing records with current client data
-- =====================================================================

PRINT '';
PRINT 'PHASE 2: Backfilling existing billing claims with current client data...';

UPDATE bc
SET 
    bc.client_id_snapshot = c.client_id,
    bc.client_name_snapshot = c.name,
    bc.contract_number_snapshot = p.contract_number,
    bc.contract_value_snapshot = p.contract_value
FROM BillingClaims bc
INNER JOIN Projects p ON bc.project_id = p.project_id
INNER JOIN Clients c ON p.client_id = c.client_id
WHERE bc.client_id_snapshot IS NULL;

DECLARE @backfill_count INT = @@ROWCOUNT;
PRINT '  - Backfilled ' + CAST(@backfill_count AS NVARCHAR(10)) + ' existing billing claims';

-- =====================================================================
-- PHASE 3: Add index for query performance
-- =====================================================================

PRINT '';
PRINT 'PHASE 3: Adding index for client snapshot queries...';

IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'IX_BillingClaims_ClientSnapshot' 
    AND object_id = OBJECT_ID('BillingClaims')
)
BEGIN
    PRINT '  - Creating IX_BillingClaims_ClientSnapshot';
    CREATE NONCLUSTERED INDEX IX_BillingClaims_ClientSnapshot
    ON BillingClaims(client_id_snapshot, client_name_snapshot)
    INCLUDE (project_id, claim_date, total_amount);
END
ELSE
BEGIN
    PRINT '  - Index IX_BillingClaims_ClientSnapshot already exists';
END

-- =====================================================================
-- PHASE 4: Validation
-- =====================================================================

PRINT '';
PRINT 'PHASE 4: Validating snapshot columns...';

DECLARE @total_claims INT, @claims_with_snapshot INT, @claims_missing_snapshot INT;

SELECT @total_claims = COUNT(*) FROM BillingClaims;
SELECT @claims_with_snapshot = COUNT(*) FROM BillingClaims WHERE client_id_snapshot IS NOT NULL;
SELECT @claims_missing_snapshot = COUNT(*) FROM BillingClaims WHERE client_id_snapshot IS NULL;

PRINT '  - Total billing claims: ' + CAST(@total_claims AS NVARCHAR(10));
PRINT '  - Claims with client snapshot: ' + CAST(@claims_with_snapshot AS NVARCHAR(10));
PRINT '  - Claims missing snapshot: ' + CAST(@claims_missing_snapshot AS NVARCHAR(10));

IF @claims_missing_snapshot > 0
BEGIN
    PRINT '';
    PRINT '⚠️  WARNING: ' + CAST(@claims_missing_snapshot AS NVARCHAR(10)) + ' claims missing snapshot data';
    PRINT '   This may indicate orphaned claims (project/client deleted)';
END

-- =====================================================================
-- PHASE 5: Create view for historical client reporting
-- =====================================================================

PRINT '';
PRINT 'PHASE 5: Creating historical client view...';

IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_BillingClaims_WithClientHistory')
BEGIN
    PRINT '  - Dropping existing vw_BillingClaims_WithClientHistory';
    DROP VIEW vw_BillingClaims_WithClientHistory;
END

PRINT '  - Creating vw_BillingClaims_WithClientHistory';

EXEC('
CREATE VIEW vw_BillingClaims_WithClientHistory AS
SELECT 
    bc.claim_id,
    bc.project_id,
    bc.claim_date,
    bc.total_amount,
    bc.status,
    -- Historical snapshot data (preserves data at time of claim)
    bc.client_id_snapshot AS historical_client_id,
    bc.client_name_snapshot AS historical_client_name,
    bc.contract_number_snapshot AS historical_contract_number,
    bc.contract_value_snapshot AS historical_contract_value,
    -- Current project data (may differ if project changed ownership)
    p.client_id AS current_client_id,
    c.name AS current_client_name,
    p.contract_number AS current_contract_number,
    p.contract_value AS current_contract_value,
    -- Flag if client changed since claim
    CASE 
        WHEN bc.client_id_snapshot != p.client_id THEN 1 
        ELSE 0 
    END AS client_changed_flag,
    -- Additional project context
    p.project_name,
    p.project_number,
    p.status AS project_status
FROM BillingClaims bc
LEFT JOIN Projects p ON bc.project_id = p.project_id
LEFT JOIN Clients c ON p.client_id = c.client_id;
');

PRINT '  - View created successfully';
PRINT '';
PRINT '  Use this view to:';
PRINT '    - Track historical client billing (who was billed at time of claim)';
PRINT '    - Identify projects that changed ownership';
PRINT '    - Generate accurate historical financial reports';

-- =====================================================================
-- COMMIT or ROLLBACK
-- =====================================================================

-- Uncomment one of the following:

-- COMMIT TRANSACTION;
-- PRINT '';
-- PRINT '✅ SUCCESS: Client snapshot migration completed!';
-- PRINT '';
-- PRINT 'Next steps:';
-- PRINT '1. Update generate_claim() function to populate snapshot columns';
-- PRINT '2. Update billing reports to use vw_BillingClaims_WithClientHistory';
-- PRINT '3. Test client change scenarios';

ROLLBACK TRANSACTION;
PRINT '';
PRINT '⚠️  ROLLED BACK: Review the output above, then change ROLLBACK to COMMIT';
PRINT '';
PRINT 'Validation queries to run after COMMIT:';
PRINT '-- Check snapshot data:';
PRINT 'SELECT TOP 10 * FROM vw_BillingClaims_WithClientHistory;';
PRINT '';
PRINT '-- Find claims where client changed:';
PRINT 'SELECT * FROM vw_BillingClaims_WithClientHistory WHERE client_changed_flag = 1;';

GO

-- =====================================================================
-- Example Usage After Migration
-- =====================================================================

/*
-- Query historical billing by client (accurate even if ownership changed)
SELECT 
    historical_client_name,
    COUNT(*) AS claim_count,
    SUM(total_amount) AS total_billed,
    MIN(claim_date) AS first_claim,
    MAX(claim_date) AS last_claim
FROM vw_BillingClaims_WithClientHistory
GROUP BY historical_client_name
ORDER BY total_billed DESC;

-- Identify projects that changed ownership after billing
SELECT 
    project_name,
    historical_client_name AS original_client,
    current_client_name AS new_client,
    COUNT(*) AS claims_under_original_client,
    SUM(total_amount) AS amount_billed_to_original
FROM vw_BillingClaims_WithClientHistory
WHERE client_changed_flag = 1
GROUP BY project_name, historical_client_name, current_client_name;

-- Billing claims with missing snapshot (orphaned claims)
SELECT bc.*
FROM BillingClaims bc
WHERE bc.client_id_snapshot IS NULL;
*/
