USE ProjectManagement;
GO

SET QUOTED_IDENTIFIER ON;
SET ANSI_NULLS ON;
SET ANSI_WARNINGS ON;
GO

/* Issue Reliability QA: staging -> dim -> fact -> canonical -> dashboard readiness */

DECLARE @latest_snapshot_sk INT;
DECLARE @latest_snapshot_date DATE;
DECLARE @latest_issue_run_id INT;

SELECT @latest_snapshot_sk = MAX(snapshot_date_sk)
FROM fact.issue_snapshot;

SELECT @latest_snapshot_date = MAX(snapshot_date)
FROM dbo.Issues_Snapshots;

SELECT TOP 1 @latest_issue_run_id = import_run_id
FROM dbo.IssueImportRuns
WHERE status = 'success'
ORDER BY completed_at DESC;

PRINT '--- Summary Counts ---';
SELECT 'stg.issues' AS src, COUNT(*) AS cnt FROM stg.issues
UNION ALL
SELECT 'dim.issue (current)', COUNT(*) FROM dim.issue WHERE current_flag = 1
UNION ALL
SELECT 'fact.issue_snapshot (latest date)', COUNT(*) FROM fact.issue_snapshot WHERE snapshot_date_sk = @latest_snapshot_sk
UNION ALL
SELECT 'Issues_Snapshots (latest successful run)', COUNT(*) FROM dbo.Issues_Snapshots WHERE import_run_id = @latest_issue_run_id
UNION ALL
SELECT 'Issues_Current', COUNT(*) FROM dbo.Issues_Current;

PRINT '--- Latest Run Metadata ---';
SELECT TOP 1 import_run_id, status, started_at, completed_at, row_count, notes
FROM dbo.IssueImportRuns
ORDER BY import_run_id DESC;

PRINT '--- Unmapped Raw Statuses ---';
WITH raw_statuses AS (
    SELECT
        i.source_system,
        LOWER(LTRIM(RTRIM(i.status))) AS raw_status,
        COUNT(*) AS issue_count
    FROM dim.issue i
    WHERE i.current_flag = 1
      AND i.status IS NOT NULL
    GROUP BY i.source_system, LOWER(LTRIM(RTRIM(i.status)))
)
SELECT
    r.source_system,
    r.raw_status,
    r.issue_count
FROM raw_statuses r
LEFT JOIN dbo.issue_status_map m
    ON m.source_system = r.source_system
   AND m.raw_status = r.raw_status
   AND m.is_active = 1
WHERE m.raw_status IS NULL
ORDER BY r.source_system, r.issue_count DESC;

PRINT '--- Staging Issues Missing in dim.issue ---';
SELECT
    s.source_system,
    s.issue_id,
    s.project_id_raw
FROM stg.issues s
LEFT JOIN dim.issue d
    ON d.issue_bk = s.issue_id
   AND d.source_system = s.source_system
   AND d.current_flag = 1
WHERE d.issue_sk IS NULL;

PRINT '--- dim.issue Missing in Latest fact.issue_snapshot ---';
SELECT
    d.issue_sk,
    d.issue_bk,
    d.source_system
FROM dim.issue d
LEFT JOIN fact.issue_snapshot s
    ON s.issue_sk = d.issue_sk
   AND s.snapshot_date_sk = @latest_snapshot_sk
WHERE d.current_flag = 1
  AND s.issue_sk IS NULL;

PRINT '--- Issues_Current vs Latest Snapshot Date ---';
SELECT
    @latest_snapshot_date AS latest_snapshot_date,
    COUNT(*) AS issues_current_count
FROM dbo.Issues_Current;

PRINT '--- Issues_Snapshots Missing in Issues_Current ---';
SELECT
    s.issue_key,
    s.source_system,
    s.source_project_id,
    s.source_issue_id
FROM dbo.Issues_Snapshots s
LEFT JOIN dbo.Issues_Current c
    ON c.issue_key_hash = s.issue_key_hash
WHERE s.import_run_id = @latest_issue_run_id
  AND c.issue_key_hash IS NULL;
GO
