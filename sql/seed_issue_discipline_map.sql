USE ProjectManagement;
GO

UPDATE dbo.issue_discipline_map
SET normalized_discipline = 'BIM Manager',
    updated_at = SYSUTCDATETIME()
WHERE source_system = 'ACC'
  AND raw_discipline LIKE '%BIM Manager%'
  AND active_flag = 1;

UPDATE dbo.issue_discipline_map
SET normalized_discipline = 'BIM Manager',
    updated_at = SYSUTCDATETIME()
WHERE source_system = 'ACC'
  AND raw_discipline LIKE '%Digital Engineering Manager%'
  AND active_flag = 1;

UPDATE dbo.issue_discipline_map
SET normalized_discipline = 'Structural',
    updated_at = SYSUTCDATETIME()
WHERE source_system = 'ACC'
  AND raw_discipline = 'Engineer'
  AND active_flag = 1;

UPDATE dbo.issue_discipline_map
SET normalized_discipline = 'Landscape',
    updated_at = SYSUTCDATETIME()
WHERE source_system = 'ACC'
  AND raw_discipline LIKE 'Landscape%'
  AND active_flag = 1;

INSERT INTO dbo.issue_discipline_map (
    source_system,
    raw_discipline,
    normalized_discipline,
    is_default,
    active_flag
)
SELECT DISTINCT
    'ACC' AS source_system,
    d.raw_discipline,
    CASE
        WHEN d.raw_discipline LIKE '%elect%' THEN 'Electrical'
        WHEN d.raw_discipline LIKE '%mech%' OR d.raw_discipline LIKE '%hvac%' THEN 'Mechanical (HVAC)'
        WHEN d.raw_discipline LIKE '%hyd%' OR d.raw_discipline LIKE '%plumb%' THEN 'Hydraulic/Plumbing'
        WHEN d.raw_discipline LIKE '%fire%' THEN 'Fire Protection'
        WHEN d.raw_discipline LIKE '%arch%' THEN 'Architectural'
        WHEN d.raw_discipline LIKE '%struct%' THEN 'Structural'
        WHEN d.raw_discipline LIKE '%civil%' THEN 'Civil'
        WHEN d.raw_discipline LIKE '%bim manager%' THEN 'BIM Manager'
        WHEN d.raw_discipline = 'Engineer' THEN 'Structural'
        WHEN d.raw_discipline LIKE 'Landscape%' THEN 'Landscape'
        WHEN d.raw_discipline LIKE '%multi%' THEN 'Multi-Discipline'
        ELSE NULL
    END AS normalized_discipline,
    1 AS is_default,
    1 AS active_flag
FROM (
    SELECT DISTINCT LTRIM(RTRIM(discipline)) AS raw_discipline
    FROM stg.issues
    WHERE source_system = 'ACC'
      AND discipline IS NOT NULL
      AND LTRIM(RTRIM(discipline)) <> ''
) d
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.issue_discipline_map m
    WHERE m.source_system = 'ACC'
      AND m.raw_discipline = d.raw_discipline
);
GO
