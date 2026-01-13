USE ProjectManagement;
GO

SET QUOTED_IDENTIFIER ON;
SET ANSI_NULLS ON;
SET ANSI_WARNINGS ON;
GO

/* Unmapped raw issue statuses by source system (warehouse dim). */
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
GO
