-- MERGE for issues_custom_attribute_list_values
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY attribute_mappings_id
        ORDER BY created_at DESC
    ) AS rn
    FROM staging.issues_custom_attribute_list_values
    WHERE attribute_mappings_id IS NOT NULL
)
MERGE INTO dbo.issues_custom_attribute_list_values AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.attribute_mappings_id = src.attribute_mappings_id
WHEN MATCHED THEN
    UPDATE SET
        list_id = src.list_id,
        list_value = src.list_value,
        created_at = src.created_at
WHEN NOT MATCHED THEN
    INSERT (attribute_mappings_id, list_id, list_value, created_at)
    VALUES (src.attribute_mappings_id, src.list_id, src.list_value, src.created_at);
