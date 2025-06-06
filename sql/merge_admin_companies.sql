WITH src_deduped AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY id ORDER BY created_at DESC) AS rn
    FROM staging.admin_companies
    WHERE id IS NOT NULL
)

MERGE INTO dbo.admin_companies AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.id = src.id

WHEN MATCHED THEN
    UPDATE SET
        bim360_account_id = src.bim360_account_id,
        name = src.name,
        trade = src.trade,
        category = src.category,
        address_line1 = src.address_line1,
        address_line2 = src.address_line2,
        city = src.city,
        state_or_province = src.state_or_province,
        postal_code = src.postal_code,
        country = src.country,
        phone = src.phone,
        website_url = src.website_url,
        description = src.description,
        erp_id = src.erp_id,
        tax_id = src.tax_id,
        status = src.status,
        created_at = src.created_at,
        project_size = src.project_size,
        user_size = src.user_size,
        custom_properties = src.custom_properties

WHEN NOT MATCHED THEN
    INSERT (
        id, bim360_account_id, name, trade, category, address_line1, address_line2,
        city, state_or_province, postal_code, country, phone, website_url, description,
        erp_id, tax_id, status, created_at, project_size, user_size, custom_properties
    )
    VALUES (
        src.id, src.bim360_account_id, src.name, src.trade, src.category, src.address_line1, src.address_line2,
        src.city, src.state_or_province, src.postal_code, src.country, src.phone, src.website_url, src.description,
        src.erp_id, src.tax_id, src.status, src.created_at, src.project_size, src.user_size, src.custom_properties
    );
