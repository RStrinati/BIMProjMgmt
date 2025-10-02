-- MERGE acc_data_schema.staging.issues_custom_attributes -> acc_data_schema.dbo.issues_custom_attributes
-- Grain: (issue_id, attribute_mapping_id, mapped_item_type)

SET XACT_ABORT ON;
BEGIN TRAN;

;WITH src_raw AS (
    SELECT 
        TRY_CONVERT(uniqueidentifier, NULLIF(LTRIM(RTRIM(s.issue_id)), ''))            AS issue_id_guid,
        TRY_CONVERT(uniqueidentifier, NULLIF(LTRIM(RTRIM(s.bim360_account_id)), ''))   AS bim360_account_id_guid,
        TRY_CONVERT(uniqueidentifier, NULLIF(LTRIM(RTRIM(s.bim360_project_id)), ''))   AS bim360_project_id_guid,
        s.mapped_item_type,
        TRY_CONVERT(uniqueidentifier, NULLIF(LTRIM(RTRIM(s.attribute_mapping_id)), '')) AS attribute_mapping_id_guid,
        s.attribute_title,
        s.attribute_description,
        s.attribute_data_type,
        CASE 
            WHEN TRY_CONVERT(bit, s.is_required) IS NOT NULL THEN TRY_CONVERT(bit, s.is_required)
            WHEN s.is_required IN ('true','TRUE','yes','YES','1','t','T') THEN 1
            WHEN s.is_required IN ('false','FALSE','no','NO','0','f','F') THEN 0
            ELSE NULL
        END                                                                             AS is_required_bit,
        s.attribute_value
    FROM acc_data_schema.staging.issues_custom_attributes s
),
src_valid AS (
    -- keep only rows with valid GUIDs for the key columns
    SELECT *
    FROM src_raw
    WHERE issue_id_guid IS NOT NULL
      AND attribute_mapping_id_guid IS NOT NULL
),
src_deduped AS (
    -- one row per (issue, attribute, type); no created_at available in staging
    SELECT *
    FROM (
        SELECT r.*,
               ROW_NUMBER() OVER (
                   PARTITION BY r.issue_id_guid, r.attribute_mapping_id_guid, r.mapped_item_type
                   ORDER BY COALESCE(r.attribute_value,'') DESC,
                            COALESCE(r.attribute_title,'') DESC
               ) AS rn
        FROM src_valid r
    ) x
    WHERE rn = 1
)

MERGE acc_data_schema.dbo.issues_custom_attributes AS tgt
USING src_deduped AS src
   ON  tgt.issue_id            = src.issue_id_guid
   AND tgt.attribute_mapping_id = src.attribute_mapping_id_guid
   AND ISNULL(tgt.mapped_item_type,'') = ISNULL(src.mapped_item_type,'')
WHEN MATCHED THEN
  UPDATE SET
      tgt.bim360_account_id     = src.bim360_account_id_guid,
      tgt.bim360_project_id     = src.bim360_project_id_guid,
      tgt.mapped_item_type      = src.mapped_item_type,
      tgt.attribute_title       = src.attribute_title,
      tgt.attribute_description = src.attribute_description,
      tgt.attribute_data_type   = src.attribute_data_type,
      tgt.is_required           = src.is_required_bit,
      tgt.attribute_value       = src.attribute_value,
      -- staging has no created_at; preserve existing or stamp if null
      tgt.created_at            = ISNULL(tgt.created_at, SYSUTCDATETIME())
WHEN NOT MATCHED BY TARGET THEN
  INSERT (
      issue_id,
      bim360_account_id,
      bim360_project_id,
      mapped_item_type,
      attribute_mapping_id,
      attribute_title,
      attribute_description,
      attribute_data_type,
      is_required,
      attribute_value,
      created_at
  )
  VALUES (
      src.issue_id_guid,
      src.bim360_account_id_guid,
      src.bim360_project_id_guid,
      src.mapped_item_type,
      src.attribute_mapping_id_guid,
      src.attribute_title,
      src.attribute_description,
      src.attribute_data_type,
      src.is_required_bit,
      src.attribute_value,
      SYSUTCDATETIME()
  );

COMMIT;

-- Optional (run once) to enforce the correct grain:
-- CREATE UNIQUE INDEX UX_issues_custom_attributes
--   ON acc_data_schema.dbo.issues_custom_attributes(issue_id, attribute_mapping_id, mapped_item_type);
