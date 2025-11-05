-- ProjectManagement SQL object inventory and dependency map
-- Purpose: Help review tables/views and identify potential unused objects to prune
-- Safe to run read-only; includes suggested review queries

USE ProjectManagement;
GO

-- 1) List all user tables and views by schema with row counts (approximate)
SELECT s.name AS schema_name,
       o.name AS object_name,
       o.type_desc,
       p.row_count
FROM sys.objects o
JOIN sys.schemas s ON s.schema_id = o.schema_id
OUTER APPLY (
    SELECT SUM(p.rows) AS row_count
    FROM sys.partitions p
    WHERE p.object_id = o.object_id AND p.index_id IN (0,1)
) p
WHERE o.type IN ('U','V')
ORDER BY s.name, o.type_desc, o.name;
GO

-- 2) Dependency graph: what references what
SELECT 
    referencing_schema_name = SCHEMA_NAME(o_ref.schema_id),
    referencing_object_name = o_ref.name,
    referencing_type = o_ref.type_desc,
    referenced_schema_name = d.referenced_schema_name,
    referenced_entity_name = d.referenced_entity_name,
    d.is_ambiguous
FROM sys.sql_expression_dependencies d
JOIN sys.objects o_ref ON o_ref.object_id = d.referencing_id
WHERE o_ref.is_ms_shipped = 0
ORDER BY referencing_schema_name, referencing_object_name;
GO

-- 3) Objects in warehouse schemas grouped
SELECT s.name AS schema_name, o.type_desc, COUNT(*) AS object_count
FROM sys.objects o
JOIN sys.schemas s ON s.schema_id = o.schema_id
WHERE s.name IN ('stg','dim','fact','brg','mart')
  AND o.type IN ('U','V')
GROUP BY s.name, o.type_desc
ORDER BY s.name, o.type_desc;
GO

-- 4) Potential orphans: objects not referenced by any other object (to review)
;WITH refs AS (
    SELECT DISTINCT d.referenced_schema_name, d.referenced_entity_name
    FROM sys.sql_expression_dependencies d
)
SELECT s.name AS schema_name, o.name AS object_name, o.type_desc
FROM sys.objects o
JOIN sys.schemas s ON s.schema_id = o.schema_id
LEFT JOIN refs r ON r.referenced_schema_name = s.name AND r.referenced_entity_name = o.name
WHERE o.type IN ('U','V')
  AND o.is_ms_shipped = 0
  AND r.referenced_entity_name IS NULL
  AND s.name NOT IN ('sys','INFORMATION_SCHEMA')
ORDER BY s.name, o.type_desc, o.name;
GO

-- 5) Quick duplicate check in stg.issues by (source_system, issue_id)
SELECT source_system, issue_id, COUNT(*) AS cnt
FROM stg.issues
GROUP BY source_system, issue_id
HAVING COUNT(*) > 1
ORDER BY cnt DESC;
GO

-- 6) Suggested DROP scripts (commented out) - generate only after review/backup
-- SELECT 'DROP VIEW ' + QUOTENAME(s.name) + '.' + QUOTENAME(o.name) + ';' AS drop_stmt
-- FROM sys.objects o
-- JOIN sys.schemas s ON s.schema_id = o.schema_id
-- WHERE o.type = 'V' AND s.name IN ('stg','dim','fact','brg','mart')
--   AND NOT EXISTS (
--       SELECT 1 FROM sys.sql_expression_dependencies d
--       WHERE d.referenced_schema_name = s.name AND d.referenced_entity_name = o.name
--   );
