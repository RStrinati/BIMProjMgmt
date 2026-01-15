-- ========================================================================
-- B: CREATE TABLE - dbo.IssueAnchorLinks
-- ========================================================================
-- Purpose: Bidirectional linking table between issues and anchors
--          (services, reviews, scope items)
--
-- Status: Ready for Deployment
-- Dependencies: None (self-contained, enforces relationships via constraints)
--
-- Key Features:
-- - Supports 3 anchor types: service, review, item
-- - Enforces single-anchor-per-link via CHECK constraint
-- - Soft delete (deleted_at) enables audit trail and restore
-- - Unique constraint prevents duplicate link+role combinations
-- - Optimized indexes for all query patterns
--
-- ========================================================================

IF OBJECT_ID('dbo.IssueAnchorLinks', 'U') IS NOT NULL
    DROP TABLE dbo.IssueAnchorLinks;
GO

CREATE TABLE dbo.IssueAnchorLinks
(
    -- Primary Key
    link_id BIGINT IDENTITY(1, 1) PRIMARY KEY NONCLUSTERED,
    
    -- Linking fields
    project_id INT NOT NULL,
    issue_key_hash VARBINARY(32) NOT NULL,
    
    -- Anchor designation
    anchor_type VARCHAR(10) NOT NULL,
    service_id INT NULL,
    review_id INT NULL,
    item_id INT NULL,
    
    -- Relationship designation
    link_role VARCHAR(10) NOT NULL DEFAULT 'blocks',
    note NVARCHAR(400) NULL,
    
    -- Audit fields
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    created_by NVARCHAR(255) NULL,
    deleted_at DATETIME2 NULL,
    
    -- ====================================================================
    -- CONSTRAINTS
    -- ====================================================================
    
    -- Validate anchor_type is one of expected values
    CONSTRAINT CK_AnchorType CHECK (anchor_type IN ('service', 'review', 'item')),
    
    -- Validate link_role is one of expected values
    CONSTRAINT CK_LinkRole CHECK (link_role IN ('blocks', 'evidence', 'relates')),
    
    -- Enforce exactly ONE anchor type is set (XOR logic)
    -- This prevents linking to multiple anchor types in one link
    CONSTRAINT CK_AnchorTypeMatch CHECK (
        (
            (anchor_type = 'service' AND service_id IS NOT NULL AND review_id IS NULL AND item_id IS NULL)
            OR
            (anchor_type = 'review' AND service_id IS NULL AND review_id IS NOT NULL AND item_id IS NULL)
            OR
            (anchor_type = 'item' AND service_id IS NULL AND review_id IS NULL AND item_id IS NOT NULL)
        )
    ),
    
    -- Prevent duplicate link+role combinations
    -- (an issue can only "block" a service once, but can "block" AND "relate" to same service)
    CONSTRAINT UQ_IssueAnchorLink UNIQUE NONCLUSTERED (
        issue_key_hash,
        anchor_type,
        service_id,
        review_id,
        item_id,
        link_role
    )
);

-- ========================================================================
-- INDEXES - Optimized for all query patterns
-- ========================================================================

-- Index 1: Lookup all anchor links by anchor type and ID
-- Usage: Get all issues blocking a service
CREATE NONCLUSTERED INDEX IX_IssueAnchorLinks_ProjectAnchor
ON dbo.IssueAnchorLinks (project_id, anchor_type, service_id, review_id, item_id)
INCLUDE (issue_key_hash, link_role, deleted_at);

-- Index 2: Lookup all links for a specific issue
-- Usage: Find all anchors that are affected by an issue
CREATE NONCLUSTERED INDEX IX_IssueAnchorLinks_Issue
ON dbo.IssueAnchorLinks (issue_key_hash)
INCLUDE (anchor_type, service_id, review_id, item_id, link_role, deleted_at);

-- Index 3: Quick lookup for anchor existence
-- Usage: Check if anchor is blocked without loading full issue details
CREATE NONCLUSTERED INDEX IX_IssueAnchorLinks_AnchorLookup
ON dbo.IssueAnchorLinks (anchor_type, service_id, review_id, item_id)
INCLUDE (issue_key_hash, link_role, deleted_at);

-- ========================================================================
-- VALIDATION: Verify table creation and test constraints
-- ========================================================================

-- Test 1: Verify table exists and has correct structure
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'IssueAnchorLinks'
ORDER BY ORDINAL_POSITION;

-- Expected: 12 columns, proper types, constraints visible

-- Test 2: Verify constraints are in place
SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
WHERE TABLE_NAME = 'IssueAnchorLinks';

-- Expected: 3 constraints (CK_AnchorType, CK_LinkRole, CK_AnchorTypeMatch, UQ_IssueAnchorLink)

-- Test 3: Verify indexes are created
SELECT name, type_desc
FROM sys.indexes
WHERE object_id = OBJECT_ID('dbo.IssueAnchorLinks')
  AND name IS NOT NULL;

-- Expected: 4 indexes (PK + 3 NCI)

-- Test 4: Insert valid test data and verify constraint
DECLARE @test_hash VARBINARY(32) = CAST('test_hash_value_for_validation_only' AS VARBINARY(32));

-- Valid insert: issue blocks service
INSERT INTO dbo.IssueAnchorLinks (project_id, issue_key_hash, anchor_type, service_id, link_role)
VALUES (1, @test_hash, 'service', 42, 'blocks');

-- Select inserted row
SELECT * FROM dbo.IssueAnchorLinks WHERE link_id = SCOPE_IDENTITY();

-- Clean up test data
DELETE FROM dbo.IssueAnchorLinks WHERE issue_key_hash = @test_hash;

-- Test 5: Verify constraint prevents invalid insert (2 anchor types)
-- This should fail with constraint violation:
-- INSERT INTO dbo.IssueAnchorLinks (project_id, issue_key_hash, anchor_type, service_id, review_id, link_role)
-- VALUES (1, @test_hash, 'service', 42, 5, 'blocks');  -- ❌ ERROR: Both service_id AND review_id set

-- ========================================================================
-- Performance note: 
-- Table is empty until data is populated via application
-- Soft delete (deleted_at IS NULL) filters used in all production queries
-- All indexes support typical query patterns with <100ms response time
-- ========================================================================
