-- ========================================
-- TASK B: Create dbo.IssueAnchorLinks linking table
-- ========================================
-- Purpose: Track relationships between issues and anchors (services, reviews, items)
-- Key Design:
--   - Uses issue_key_hash (stable, from Issues_Current)
--   - Supports multiple anchor types (service, review, item)
--   - Enforces exactly-one anchor per link
--   - Supports soft delete (deleted_at)
--   - Includes role semantics (blocks, evidence, relates)

USE ProjectManagement;
GO

-- Drop if exists (fresh start)
IF OBJECT_ID('dbo.IssueAnchorLinks', 'U') IS NOT NULL
    DROP TABLE dbo.IssueAnchorLinks;
GO

CREATE TABLE dbo.IssueAnchorLinks (
    link_id BIGINT IDENTITY(1, 1) PRIMARY KEY,
    
    -- Issue reference (stable)
    project_id INT NOT NULL,
    issue_key_hash VARBINARY(32) NOT NULL,
    
    -- Anchor reference (exactly one of service_id, review_id, item_id)
    anchor_type VARCHAR(10) NOT NULL 
        CHECK (anchor_type IN ('service', 'review', 'item')),
    
    service_id INT NULL,
    review_id INT NULL,
    item_id INT NULL,
    
    -- Link semantics
    link_role VARCHAR(10) NOT NULL DEFAULT 'blocks'
        CHECK (link_role IN ('blocks', 'evidence', 'relates')),
    
    -- Metadata
    note NVARCHAR(400) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    created_by NVARCHAR(255) NULL,
    deleted_at DATETIME2 NULL,  -- Soft delete support
    
    -- Constraint: exactly one anchor type is set
    CONSTRAINT CK_AnchorTypeMatch CHECK (
        (anchor_type = 'service' AND service_id IS NOT NULL AND review_id IS NULL AND item_id IS NULL)
        OR (anchor_type = 'review' AND service_id IS NULL AND review_id IS NOT NULL AND item_id IS NULL)
        OR (anchor_type = 'item' AND service_id IS NULL AND review_id IS NULL AND item_id IS NOT NULL)
    ),
    
    -- Prevent duplicates per (issue, anchor)
    CONSTRAINT UQ_IssueAnchorLink UNIQUE (
        issue_key_hash, anchor_type, service_id, review_id, item_id, link_role
    )
);

-- Indexes for query performance
CREATE INDEX IX_IssueAnchorLinks_ProjectAnchor 
    ON dbo.IssueAnchorLinks (project_id, anchor_type, service_id, review_id, item_id);
GO

CREATE INDEX IX_IssueAnchorLinks_Issue 
    ON dbo.IssueAnchorLinks (issue_key_hash);
GO

CREATE INDEX IX_IssueAnchorLinks_AnchorLookup
    ON dbo.IssueAnchorLinks (anchor_type, service_id, review_id, item_id);
GO

PRINT 'Table dbo.IssueAnchorLinks created with indexes'
GO

-- Validation: Table structure
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'IssueAnchorLinks'
    AND TABLE_SCHEMA = 'dbo'
ORDER BY ORDINAL_POSITION;
GO

-- Validation: Indexes exist
SELECT 
    INDEX_NAME,
    COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_NAME = 'IssueAnchorLinks'
    AND TABLE_SCHEMA = 'dbo'
ORDER BY INDEX_NAME, ORDINAL_POSITION;
GO
