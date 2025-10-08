-- Query to find issues WITH custom attributes populated
-- Save this and use it to filter your view

-- Option 1: All issues with ANY custom attribute
SELECT 
    issue_id,
    display_id,
    title,
    status,
    Building_Level,
    Clash_Level,
    Location,
    Location_01,
    Phase,
    Priority,
    project_name,
    created_at
FROM acc_data_schema.dbo.vw_issues_expanded
WHERE Building_Level IS NOT NULL 
   OR Clash_Level IS NOT NULL
   OR Location IS NOT NULL
   OR Location_01 IS NOT NULL
   OR Phase IS NOT NULL
   OR Priority IS NOT NULL
ORDER BY display_id;

-- Option 2: Filter by specific project (e.g., MEL071)
SELECT 
    issue_id,
    display_id,
    title,
    Building_Level,
    Clash_Level,
    Location,
    Phase,
    Priority
FROM acc_data_schema.dbo.vw_issues_expanded
WHERE project_name LIKE '%MEL071%'
  AND (Building_Level IS NOT NULL 
    OR Clash_Level IS NOT NULL
    OR Location IS NOT NULL
    OR Phase IS NOT NULL)
ORDER BY Clash_Level, Building_Level;

-- Option 3: Count issues by custom attribute
SELECT 
    'Building Level' as attribute_name,
    COUNT(*) as issue_count
FROM acc_data_schema.dbo.vw_issues_expanded
WHERE Building_Level IS NOT NULL

UNION ALL

SELECT 
    'Clash Level',
    COUNT(*)
FROM acc_data_schema.dbo.vw_issues_expanded
WHERE Clash_Level IS NOT NULL

UNION ALL

SELECT 
    'Location',
    COUNT(*)
FROM acc_data_schema.dbo.vw_issues_expanded
WHERE Location IS NOT NULL

UNION ALL

SELECT 
    'Phase',
    COUNT(*)
FROM acc_data_schema.dbo.vw_issues_expanded
WHERE Phase IS NOT NULL

UNION ALL

SELECT 
    'Priority',
    COUNT(*)
FROM acc_data_schema.dbo.vw_issues_expanded
WHERE Priority IS NOT NULL;

-- Option 4: Group by project to see which projects use which attributes
SELECT 
    project_name,
    COUNT(CASE WHEN Building_Level IS NOT NULL THEN 1 END) as building_level_count,
    COUNT(CASE WHEN Clash_Level IS NOT NULL THEN 1 END) as clash_level_count,
    COUNT(CASE WHEN Location IS NOT NULL THEN 1 END) as location_count,
    COUNT(CASE WHEN Phase IS NOT NULL THEN 1 END) as phase_count,
    COUNT(CASE WHEN Priority IS NOT NULL THEN 1 END) as priority_count,
    COUNT(*) as total_issues
FROM acc_data_schema.dbo.vw_issues_expanded
GROUP BY project_name
HAVING COUNT(CASE WHEN Building_Level IS NOT NULL THEN 1 END) > 0
    OR COUNT(CASE WHEN Clash_Level IS NOT NULL THEN 1 END) > 0
    OR COUNT(CASE WHEN Location IS NOT NULL THEN 1 END) > 0
    OR COUNT(CASE WHEN Phase IS NOT NULL THEN 1 END) > 0
    OR COUNT(CASE WHEN Priority IS NOT NULL THEN 1 END) > 0
ORDER BY project_name;
