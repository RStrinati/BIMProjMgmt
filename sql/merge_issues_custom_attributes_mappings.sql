SET XACT_ABORT ON;
BEGIN TRAN;

;WITH src_raw AS (
    SELECT 
        TRY_CONVERT(uniqueidentifier, NULLIF(LTRIM(RTRIM(s.id)), ''))                   AS id_guid,
        TRY_CONVERT(uniqueidentifier, NULLIF(LTRIM(RTRIM(s.bim360_account_id)), ''))    AS bim360_account_id_guid,
        TRY_CONVERT(uniqueidentifier, NULLIF(LTRIM(RTRIM(s.bim360_project_id)), ''))    AS bim360_project_id_guid,
        s.mapped_item_type,
        TRY_CONVERT(uniqueidentifier, NULLIF(LTRIM(RTRIM(s.mapped_item_id)), ''))       AS mapped_item_id_guid,
        s.title,
        s.description,
        s.data_type,
        TRY_CONVERT(int, s.[order])                                                     AS [order_int],
        CASE 
            WHEN TRY_CONVERT(bit, s.is_required) IS NOT NULL THEN TRY_CONVERT(bit, s.is_required)
            WHEN s.is_required IN ('true','TRUE','yes','YES','1','t','T') THEN 1
            WHEN s.is_required IN ('false','FALSE','no','NO','0','f','F') THEN 0
            ELSE NULL
        END                                                                             AS is_required_bit,
        TRY_CONVERT(datetime2, NULLIF(LTRIM(RTRIM(s.created_at)), ''))                  AS created_at_dt,
        s.created_by,
        TRY_CONVERT(datetime2, NULLIF(LTRIM(RTRIM(s.updated_at)), ''))                  AS updated_at_dt,
        s.updated_by
    FROM acc_data_schema.staging.issues_custom_attributes_mappings s
),
src_valid AS (
    -- keep only rows with valid GUIDs in the key columns
    SELECT *
    FROM src_raw
    WHERE id_guid IS NOT NULL
      AND mapped_item_id_guid IS NOT NULL
      AND bim360_account_id_guid IS NOT NULL
      AND bim360_project_id_guid IS NOT NULL
),
src_deduped AS (
    SELECT *
    FROM (
        SELECT r.*,
               ROW_NUMBER() OVER (
                   PARTITION BY r.id_guid, r.mapped_item_type, r.mapped_item_id_guid
                   ORDER BY COALESCE(r.updated_at_dt, r.created_at_dt) DESC,
                            COALESCE(r.title,'') DESC
               ) AS rn
        FROM src_valid r
    ) x
    WHERE rn = 1
)

MERGE acc_data_schema.dbo.issues_custom_attributes_mappings AS tgt
USING src_deduped AS src
   ON  tgt.id              = src.id_guid
   AND ISNULL(tgt.mapped_item_type,'') = ISNULL(src.mapped_item_type,'')
   AND tgt.mapped_item_id  = src.mapped_item_id_guid
WHEN MATCHED THEN
  UPDATE SET
      tgt.bim360_account_id = src.bim360_account_id_guid,
      tgt.bim360_project_id = src.bim360_project_id_guid,
      tgt.mapped_item_type  = src.mapped_item_type,
      tgt.mapped_item_id    = src.mapped_item_id_guid,
      tgt.title             = src.title,
      tgt.description       = src.description,
      tgt.data_type         = src.data_type,
      tgt.[order]           = src.[order_int],
      tgt.is_required       = src.is_required_bit,
      tgt.created_at        = COALESCE(src.created_at_dt, tgt.created_at),
      tgt.created_by        = COALESCE(src.created_by,   tgt.created_by),
      tgt.updated_at        = COALESCE(src.updated_at_dt, SYSUTCDATETIME()),
      tgt.updated_by        = COALESCE(src.updated_by,   tgt.updated_by)
WHEN NOT MATCHED BY TARGET THEN
  INSERT (
      id, bim360_account_id, bim360_project_id,
      mapped_item_type, mapped_item_id, title, description,
      data_type, [order], is_required,
      created_at, created_by, updated_at, updated_by
  )
  VALUES (
      src.id_guid, src.bim360_account_id_guid, src.bim360_project_id_guid,
      src.mapped_item_type, src.mapped_item_id_guid, src.title, src.description,
      src.data_type, src.[order_int], src.is_required_bit,
      COALESCE(src.created_at_dt, SYSUTCDATETIME()),
      src.created_by,
      COALESCE(src.updated_at_dt, SYSUTCDATETIME()),
      src.updated_by
  );

COMMIT;
