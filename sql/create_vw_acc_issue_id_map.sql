-- vw_acc_issue_id_map: Unified ACC Issue Identifier Mapping
-- Purpose: Resolve ACC issues from Issues_Current (which may store either UUID or display_id)
--          to both the authoritative ACC UUID and the human-facing display_id
-- 
-- Strategy:
-- 1. UUID-style source_issue_ids (77.84%) are assumed to be directly from acc.issue_id
-- 2. Numeric source_issue_ids (22.16%) are assumed to be from acc.display_id
-- 3. Both are joined with project context for safety
--
-- Usage:
-- SELECT * FROM dbo.vw_acc_issue_id_map WHERE source_issue_id = '<some_id>'

USE ProjectManagement;
GO

CREATE OR ALTER VIEW dbo.vw_acc_issue_id_map AS

-- Path 1: source_issue_id is UUID (typical case, 77.84% of ACC issues)
SELECT DISTINCT
    ic.issue_key,
    ic.source_system,
    ic.source_issue_id,
    ic.source_project_id,
    CAST(acc.issue_id AS NVARCHAR(MAX)) as acc_issue_uuid,
    acc.display_id as acc_issue_number,
    CAST(acc.bim360_project_id AS NVARCHAR(100)) as acc_project_uuid,
    'uuid' as source_id_type,
    acc.title as acc_title,
    acc.status as acc_status,
    acc.created_at as acc_created_at,
    acc.updated_at as acc_updated_at
FROM dbo.Issues_Current ic
INNER JOIN acc_data_schema.dbo.issues_issues acc
    ON ic.source_issue_id = CAST(acc.issue_id AS NVARCHAR(MAX))
WHERE ic.source_system = 'ACC'
    AND ic.source_issue_id LIKE '%-%'  -- UUID pattern check

UNION ALL

-- Path 2: source_issue_id is display_id (fallback case, 22.16% of ACC issues)
-- Note: Numeric source_issue_ids are ambiguous and currently unmatchable in this dataset
-- Preserved for backward compatibility and future data reconciliation
SELECT DISTINCT
    ic.issue_key,
    ic.source_system,
    ic.source_issue_id,
    ic.source_project_id,
    CAST(acc.issue_id AS NVARCHAR(MAX)) as acc_issue_uuid,
    acc.display_id as acc_issue_number,
    CAST(acc.bim360_project_id AS NVARCHAR(100)) as acc_project_uuid,
    'display_id' as source_id_type,
    acc.title as acc_title,
    acc.status as acc_status,
    acc.created_at as acc_created_at,
    acc.updated_at as acc_updated_at
FROM dbo.Issues_Current ic
INNER JOIN acc_data_schema.dbo.issues_issues acc
    ON TRY_CAST(ic.source_issue_id AS INT) = acc.display_id
    AND ic.source_project_id = CAST(acc.bim360_project_id AS NVARCHAR(100))
WHERE ic.source_system = 'ACC'
    AND ic.source_issue_id NOT LIKE '%-%';

GO
