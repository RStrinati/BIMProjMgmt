-- Diagnose why ACC issues aren't mapping to PM projects
USE ProjectManagement;
GO

PRINT '=== 1. Sample of project_id_raw values from ACC issues ===';
SELECT TOP 20
    issue_id,
    project_name,
    project_id_raw,
    TRY_CONVERT(INT, project_id_raw) AS project_id_int,
    CASE 
        WHEN TRY_CONVERT(INT, project_id_raw) IS NULL THEN 'Not convertible to INT'
        WHEN NOT EXISTS (SELECT 1 FROM dim.project p WHERE p.project_bk = TRY_CONVERT(INT, project_id_raw) AND p.current_flag = 1)
        THEN 'No matching project_bk in dim.project'
        ELSE 'Should match'
    END AS mapping_status
FROM stg.issues
WHERE source_system = 'ACC'
ORDER BY project_name;
GO

PRINT '=== 2. Distribution of project_name values in ACC issues ===';
SELECT 
    project_name,
    COUNT(*) AS issue_count,
    MIN(project_id_raw) AS sample_project_id_raw
FROM stg.issues
WHERE source_system = 'ACC'
GROUP BY project_name
ORDER BY COUNT(*) DESC;
GO

PRINT '=== 3. Check if project_aliases table is populated ===';
SELECT pa.pm_project_id, pa.alias_name, p.project_name AS actual_pm_name
FROM dbo.project_aliases pa
LEFT JOIN dim.project p ON p.project_bk = pa.pm_project_id AND p.current_flag = 1
ORDER BY pa.alias_name;
GO

PRINT '=== 4. ACC project names that need aliases ===';
SELECT DISTINCT
    i.project_name AS acc_project_name,
    i.project_id_raw,
    'Missing alias or mapping' AS status
FROM stg.issues i
WHERE i.source_system = 'ACC'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.project_aliases pa WHERE pa.alias_name = i.project_name
  )
  AND (
      TRY_CONVERT(INT, i.project_id_raw) IS NULL
      OR NOT EXISTS (
          SELECT 1 FROM dim.project p 
          WHERE p.project_bk = TRY_CONVERT(INT, i.project_id_raw) AND p.current_flag = 1
      )
  )
ORDER BY i.project_name;
GO

PRINT '=== 5. Suggested INSERT statements for project_aliases ===';
SELECT 
    'INSERT INTO dbo.project_aliases (pm_project_id, alias_name) VALUES (' 
    + ISNULL(CAST(closest_match.project_bk AS NVARCHAR), 'NULL') 
    + ', ''' + i.project_name + ''');' AS suggested_insert
FROM (
    SELECT DISTINCT project_name
    FROM stg.issues
    WHERE source_system = 'ACC'
      AND NOT EXISTS (SELECT 1 FROM dbo.project_aliases pa WHERE pa.alias_name = project_name)
) i
OUTER APPLY (
    SELECT TOP 1 p.project_bk, p.project_name
    FROM dim.project p
    WHERE p.current_flag = 1
      AND (
          p.project_name LIKE '%' + i.project_name + '%'
          OR i.project_name LIKE '%' + p.project_name + '%'
      )
    ORDER BY LEN(p.project_name)
) closest_match
ORDER BY i.project_name;
GO
