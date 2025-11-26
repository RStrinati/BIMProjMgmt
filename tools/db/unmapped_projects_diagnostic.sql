-- Diagnose why some issues end up with unknown/NULL project_sk (often shown as -1 in reports)
-- Run in ProjectManagement

USE ProjectManagement;
GO

-- 1) Current mapping logic (same as usp_load_dim_issue): try by ID, then alias, then name
;WITH resolved AS (
    SELECT
        i.source_system,
        i.issue_id,
        i.project_name AS issue_project_name,
        i.project_id_raw,
        TRY_CONVERT(INT, i.project_id_raw) AS project_id_int,
        p_id.project_sk AS project_sk_by_id,
        pa.pm_project_id,
        p_alias.project_sk AS project_sk_by_alias,
        p_name.project_sk AS project_sk_by_name,
        COALESCE(p_id.project_sk, p_alias.project_sk, p_name.project_sk) AS resolved_project_sk
    FROM stg.issues i
    LEFT JOIN dim.project p_id
           ON p_id.project_bk = TRY_CONVERT(INT, i.project_id_raw)
          AND p_id.current_flag = 1
    LEFT JOIN dbo.project_aliases pa
           ON pa.alias_name = i.project_name
    LEFT JOIN dim.project p_alias
           ON p_alias.project_bk = pa.pm_project_id
          AND p_alias.current_flag = 1
    LEFT JOIN dim.project p_name
           ON p_name.project_name = i.project_name
          AND p_name.current_flag = 1
)
SELECT TOP 200
    r.source_system,
    r.issue_id,
    r.issue_project_name,
    r.project_id_raw,
    r.project_id_int,
    r.pm_project_id,
    r.project_sk_by_id,
    r.project_sk_by_alias,
    r.project_sk_by_name,
    r.resolved_project_sk
FROM resolved r
WHERE r.resolved_project_sk IS NULL
ORDER BY r.source_system, r.issue_id;
GO

-- 2) Aggregate reasons
;WITH resolved AS (
    SELECT
        i.source_system,
        COUNT(*) AS total,
        SUM(CASE WHEN TRY_CONVERT(INT, i.project_id_raw) IS NULL THEN 1 ELSE 0 END) AS id_not_convertible,
        SUM(CASE WHEN TRY_CONVERT(INT, i.project_id_raw) IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM dim.project p WHERE p.project_bk = TRY_CONVERT(INT, i.project_id_raw) AND p.current_flag = 1
        ) THEN 1 ELSE 0 END) AS id_not_in_dim_project,
        SUM(CASE WHEN pa.alias_name IS NULL THEN 1 ELSE 0 END) AS alias_missing,
        SUM(CASE WHEN pa.alias_name IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM dim.project p WHERE p.project_bk = pa.pm_project_id AND p.current_flag = 1
        ) THEN 1 ELSE 0 END) AS alias_points_to_missing_project,
        SUM(CASE WHEN EXISTS (
            SELECT 1 FROM dim.project p WHERE p.project_name = i.project_name AND p.current_flag = 1
        ) THEN 0 ELSE 1 END) AS name_not_in_dim_project
    FROM stg.issues i
    LEFT JOIN dbo.project_aliases pa ON pa.alias_name = i.project_name
)
SELECT * FROM resolved;
GO

-- 3) Duplicate/similar names in dim.project (may cause 'double up' if reports group by name)
SELECT p.project_name, COUNT(DISTINCT p.project_bk) AS distinct_bk
FROM dim.project p
WHERE p.current_flag = 1
GROUP BY p.project_name
HAVING COUNT(DISTINCT p.project_bk) > 1
ORDER BY distinct_bk DESC, p.project_name;
GO
