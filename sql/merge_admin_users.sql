-- MERGE for admin_users
WITH src_deduped AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY id
        ORDER BY updated_at DESC
    ) AS rn
    FROM staging.admin_users
    WHERE id IS NOT NULL
)
MERGE INTO dbo.admin_users AS tgt
USING (SELECT * FROM src_deduped WHERE rn = 1) AS src
ON tgt.id = src.id
WHEN MATCHED THEN
    UPDATE SET
        autodesk_id = src.autodesk_id,
        bim360_account_id = src.bim360_account_id,
        email = src.email,
        name = src.name,
        first_name = src.first_name,
        last_name = src.last_name,
        job_title = src.job_title,
        phone = src.phone,
        address_line1 = src.address_line1,
        address_line2 = src.address_line2,
        city = src.city,
        state_or_province = src.state_or_province,
        postal_code = src.postal_code,
        country = src.country,
        last_sign_in = src.last_sign_in,
        access_level_account_admin = src.access_level_account_admin,
        access_level_project_admin = src.access_level_project_admin,
        access_level_project_member = src.access_level_project_member,
        access_level_executive = src.access_level_executive,
        default_role_id = src.default_role_id,
        default_company_id = src.default_company_id,
        status = src.status,
        status_reason = src.status_reason,
        created_at = src.created_at,
        updated_at = src.updated_at
WHEN NOT MATCHED THEN
    INSERT (id, autodesk_id, bim360_account_id, email, name, first_name, last_name, job_title,
            phone, address_line1, address_line2, city, state_or_province, postal_code, country, last_sign_in,
            access_level_account_admin, access_level_project_admin, access_level_project_member,
            access_level_executive, default_role_id, default_company_id, status, status_reason,
            created_at, updated_at)
    VALUES (src.id, src.autodesk_id, src.bim360_account_id, src.email, src.name, src.first_name, src.last_name, src.job_title,
            src.phone, src.address_line1, src.address_line2, src.city, src.state_or_province, src.postal_code, src.country, src.last_sign_in,
            src.access_level_account_admin, src.access_level_project_admin, src.access_level_project_member,
            src.access_level_executive, src.default_role_id, src.default_company_id, src.status, src.status_reason,
            src.created_at, src.updated_at);
