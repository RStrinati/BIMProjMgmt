-- Warehouse Dimension Update: Add ACC display identifiers
-- This adds non-breaking columns to dim.issue for ACC issue number visibility
--
-- Goals:
-- 1. Store canonical ACC UUID in source_issue_id (already done, 77.84% of issues)
-- 2. Add acc_issue_number as display attribute for ACC issues
-- 3. Add acc_issue_uuid for explicit clarity
-- 4. Preserve warehouse key stability (no breaking changes to issue_bk, issue_sk)

USE warehouse;
GO

-- Step 1: Add columns to dim.issue if not already present
IF COL_LENGTH('dim.issue', 'acc_issue_number') IS NULL
BEGIN
    ALTER TABLE dim.issue
    ADD acc_issue_number INT NULL,
        acc_issue_uuid NVARCHAR(MAX) NULL;
    
    PRINT 'Added columns: acc_issue_number, acc_issue_uuid to dim.issue';
END
ELSE
BEGIN
    PRINT 'Columns already exist on dim.issue';
END
GO

-- Step 2: Create/update index for acc_issue_number (for ACC-specific queries)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_dim_issue_acc_number')
BEGIN
    CREATE NONCLUSTERED INDEX ix_dim_issue_acc_number
        ON dim.issue(acc_issue_number)
        WHERE source_system = 'ACC' AND current_flag = 1;
    
    PRINT 'Created index: ix_dim_issue_acc_number';
END
GO

-- Step 3: Populate acc_issue_number and acc_issue_uuid from staging
-- This uses the vw_acc_issue_id_map to enrich existing dim.issue records
IF OBJECT_ID('warehouse.usp_update_dim_issue_acc_identifiers', 'P') IS NOT NULL
    DROP PROCEDURE warehouse.usp_update_dim_issue_acc_identifiers;
GO

CREATE PROCEDURE warehouse.usp_update_dim_issue_acc_identifiers
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @updated_count INT = 0;
    
    -- Update dim.issue with ACC identifiers from staging
    UPDATE di
    SET di.acc_issue_number = stg_map.acc_issue_number,
        di.acc_issue_uuid = stg_map.acc_issue_uuid
    FROM dim.issue di
    INNER JOIN (
        -- Derived from vw_acc_issue_id_map logic (no direct join to staging)
        SELECT DISTINCT
            ic.source_issue_id,
            acc.display_id AS acc_issue_number,
            CAST(acc.issue_id AS NVARCHAR(MAX)) AS acc_issue_uuid
        FROM ProjectManagement.dbo.Issues_Current ic
        INNER JOIN acc_data_schema.dbo.issues_issues acc
            ON ic.source_issue_id = CAST(acc.issue_id AS NVARCHAR(MAX))
        WHERE ic.source_system = 'ACC'
            AND ic.source_issue_id LIKE '%-%'
    ) stg_map
        ON di.source_issue_id = stg_map.source_issue_id
        AND di.source_system = 'ACC'
        AND di.current_flag = 1
    WHERE di.acc_issue_number IS NULL OR di.acc_issue_uuid IS NULL;
    
    SET @updated_count = @@ROWCOUNT;
    PRINT 'Updated ' + CAST(@updated_count AS NVARCHAR(20)) + ' dim.issue records with ACC identifiers';
    
END
GO

-- Step 4: Call the update procedure
PRINT 'Executing: usp_update_dim_issue_acc_identifiers';
EXEC warehouse.usp_update_dim_issue_acc_identifiers;
GO

-- Step 5: Verify the update
PRINT 'Verification: ACC issues with and without acc_issue_number';
SELECT 
    COUNT(*) AS total_acc_issues,
    SUM(CASE WHEN acc_issue_number IS NOT NULL THEN 1 ELSE 0 END) AS with_number,
    SUM(CASE WHEN acc_issue_number IS NULL THEN 1 ELSE 0 END) AS without_number,
    CAST(
        100.0 * SUM(CASE WHEN acc_issue_number IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*)
        AS DECIMAL(5,2)
    ) AS coverage_pct
FROM dim.issue
WHERE source_system = 'ACC' AND current_flag = 1;
GO

-- Step 6: Document the changes
PRINT '
===== ACC Issue Identifier Enhancement Summary =====

PURPOSE:
- Reconcile ACC Issues_Current (which stores either UUID or display_id in source_issue_id)
- Add human-facing acc_issue_number to dim.issue for reporting and queries
- Preserve warehouse stability (no breaking changes to keys)

CHANGES:
1. dim.issue: Added columns acc_issue_number (INT, nullable) and acc_issue_uuid (NVARCHAR(MAX), nullable)
2. Index: Added ix_dim_issue_acc_number for efficient ACC issue lookups by number
3. Load procedure: usp_update_dim_issue_acc_identifiers enriches dim.issue with resolved identifiers

IMPACT:
- Issue_sk (PRIMARY KEY) unchanged
- issue_bk (business key) unchanged
- Bridges (brg.review_issue) unchanged
- Mart views can now reference acc_issue_number for ACC-specific reporting
- Dashboard can display human-friendly issue numbers for ACC issues

BACKWARD COMPATIBILITY:
- Fully backward compatible (additive columns only)
- Existing queries unaffected
- New columns are nullable and optional
====================================================
';
GO
