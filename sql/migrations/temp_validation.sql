-- A) How many ACC issues exist in Issues_Current?
SELECT COUNT(*) as issues_current_acc_total
FROM dbo.Issues_Current 
WHERE source_system = 'ACC';

-- B) How many rows does the mapping view return?
SELECT COUNT(*) as vw_mapping_total
FROM dbo.vw_acc_issue_id_map;

-- C) How many rows have acc_issue_uuid present?
SELECT COUNT(*) as with_uuid
FROM dbo.vw_acc_issue_id_map
WHERE acc_issue_uuid IS NOT NULL;

-- D) How many have acc_issue_number present?
SELECT COUNT(*) as with_number
FROM dbo.vw_acc_issue_id_map
WHERE acc_issue_number IS NOT NULL;

-- E) What numeric IDs are NOT in the mapping view?
SELECT COUNT(*) as unmapped_numeric
FROM dbo.Issues_Current ic
WHERE source_system = 'ACC'
  AND source_issue_id NOT LIKE '%-%'
  AND NOT EXISTS (SELECT 1 FROM dbo.vw_acc_issue_id_map m WHERE m.issue_key = ic.issue_key);

-- F) Sample unmapped numeric IDs (first 10)
SELECT TOP 10 ic.issue_key, ic.source_issue_id, ic.source_project_id
FROM dbo.Issues_Current ic
WHERE source_system = 'ACC'
  AND source_issue_id NOT LIKE '%-%'
  AND NOT EXISTS (SELECT 1 FROM dbo.vw_acc_issue_id_map m WHERE m.issue_key = ic.issue_key)
ORDER BY ic.issue_key;
