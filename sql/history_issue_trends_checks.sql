USE ProjectManagement;
GO

-- History validation checks for mart.issue_trends_monthly and mart.issue_trends_weekly.
-- These checks mirror snapshot quality expectations at an aggregate level.

PRINT '--- Check: mart.issue_trends_monthly exists';
SELECT 1 AS exists_flag
FROM sys.tables t
JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE s.name = 'mart' AND t.name = 'issue_trends_monthly';

PRINT '--- Check: mart.issue_trends_weekly exists';
SELECT 1 AS exists_flag
FROM sys.tables t
JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE s.name = 'mart' AND t.name = 'issue_trends_weekly';

PRINT '--- Check: monthly history range';
SELECT
    MIN(month_start) AS earliest_month,
    MAX(month_start) AS latest_month,
    COUNT(*) AS rows
FROM mart.issue_trends_monthly;

PRINT '--- Check: weekly history range';
SELECT
    MIN(week_start) AS earliest_week,
    MAX(week_start) AS latest_week,
    COUNT(*) AS rows
FROM mart.issue_trends_weekly;

PRINT '--- Check: monthly totals are non-negative';
SELECT COUNT(*) AS bad_rows
FROM mart.issue_trends_monthly
WHERE open_issues < 0 OR closed_issues < 0 OR total_issues < 0;

PRINT '--- Check: weekly totals are non-negative';
SELECT COUNT(*) AS bad_rows
FROM mart.issue_trends_weekly
WHERE open_issues < 0 OR closed_issues < 0 OR total_issues < 0;

PRINT '--- Check: monthly open + closed does not exceed total';
SELECT COUNT(*) AS bad_rows
FROM mart.issue_trends_monthly
WHERE open_issues + closed_issues > total_issues;

PRINT '--- Check: weekly open + closed does not exceed total';
SELECT COUNT(*) AS bad_rows
FROM mart.issue_trends_weekly
WHERE open_issues + closed_issues > total_issues;

PRINT '--- Check: monthly missing months (expected monthly continuity)';
WITH months AS (
    SELECT DISTINCT month_start FROM mart.issue_trends_monthly
),
bounds AS (
    SELECT MIN(month_start) AS min_month, MAX(month_start) AS max_month FROM months
),
series AS (
    SELECT min_month AS month_start FROM bounds
    UNION ALL
    SELECT DATEADD(MONTH, 1, month_start)
    FROM series
    WHERE month_start < (SELECT max_month FROM bounds)
)
SELECT s.month_start
FROM series s
LEFT JOIN months m ON s.month_start = m.month_start
WHERE m.month_start IS NULL
OPTION (MAXRECURSION 32767);

PRINT '--- Check: weekly missing weeks (expected weekly continuity)';
WITH weeks AS (
    SELECT DISTINCT week_start FROM mart.issue_trends_weekly
),
bounds AS (
    SELECT MIN(week_start) AS min_week, MAX(week_start) AS max_week FROM weeks
),
series AS (
    SELECT min_week AS week_start FROM bounds
    UNION ALL
    SELECT DATEADD(WEEK, 1, week_start)
    FROM series
    WHERE week_start < (SELECT max_week FROM bounds)
)
SELECT s.week_start
FROM series s
LEFT JOIN weeks w ON s.week_start = w.week_start
WHERE w.week_start IS NULL
OPTION (MAXRECURSION 32767);

PRINT '--- Check: project_sk joins for monthly history';
SELECT COUNT(*) AS orphan_rows
FROM mart.issue_trends_monthly m
LEFT JOIN dim.project p ON m.project_sk = p.project_sk
WHERE p.project_sk IS NULL AND m.project_sk <> 0;

PRINT '--- Check: project_sk joins for weekly history';
SELECT COUNT(*) AS orphan_rows
FROM mart.issue_trends_weekly w
LEFT JOIN dim.project p ON w.project_sk = p.project_sk
WHERE p.project_sk IS NULL AND w.project_sk <> 0;

PRINT '--- Check: spot sample monthly totals';
SELECT TOP 12 *
FROM mart.issue_trends_monthly
ORDER BY month_start DESC;

PRINT '--- Check: spot sample weekly totals';
SELECT TOP 12 *
FROM mart.issue_trends_weekly
ORDER BY week_start DESC;
GO
