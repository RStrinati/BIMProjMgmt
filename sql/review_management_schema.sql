-- Review Management System - SQL Schema
-- Comprehensive scope → schedule → progress → billing workflow

-- 3.1 Projects (enhanced)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Projects')
BEGIN
    CREATE TABLE dbo.Projects (
        project_id        INT IDENTITY PRIMARY KEY,
        name              NVARCHAR(200) NOT NULL,
        client            NVARCHAR(200) NULL,
        start_date        DATE NULL,
        end_date          DATE NULL,
        programme_ref     NVARCHAR(100) NULL,
        created_at        DATETIME2 DEFAULT SYSDATETIME()
    );
END;

IF COL_LENGTH('dbo.Projects', 'name') IS NULL
BEGIN
    ALTER TABLE dbo.Projects
    ADD name NVARCHAR(200) NULL;
END;

IF OBJECT_ID('dbo.ServiceTemplates','U') IS NULL
BEGIN
    CREATE TABLE dbo.ServiceTemplates (
        template_id       INT IDENTITY PRIMARY KEY,
        name              NVARCHAR(200) NOT NULL,   -- e.g. "SINSW ??" MPHS"
        sector            NVARCHAR(100) NULL,       -- e.g. "Education", "AWS", "Data Centre"
        notes             NVARCHAR(MAX) NULL,
        created_at        DATETIME2 DEFAULT SYSDATETIME()
    );
END
ELSE
BEGIN
    IF COL_LENGTH('dbo.ServiceTemplates', 'template_id') IS NULL
    BEGIN
        DECLARE @created_template_seq BIT = 0;

        ALTER TABLE dbo.ServiceTemplates
        ADD template_id INT NULL;

        IF OBJECT_ID('dbo.seq_ServiceTemplates_template_id','SO') IS NULL
        BEGIN
            EXEC('CREATE SEQUENCE dbo.seq_ServiceTemplates_template_id AS INT START WITH 1 INCREMENT BY 1;');
            SET @created_template_seq = 1;
        END;

        EXEC('UPDATE dbo.ServiceTemplates SET template_id = NEXT VALUE FOR dbo.seq_ServiceTemplates_template_id WHERE template_id IS NULL;');

        ALTER TABLE dbo.ServiceTemplates
        ALTER COLUMN template_id INT NOT NULL;

        IF @created_template_seq = 1
        BEGIN
            EXEC('DROP SEQUENCE dbo.seq_ServiceTemplates_template_id;');
        END;
    END;
    IF COL_LENGTH('dbo.ServiceTemplates', 'template_id') IS NOT NULL
    BEGIN
        DECLARE @existing_pk SYSNAME;
        DECLARE @pk_template_cols INT = 0;
        DECLARE @pk_total_cols INT = 0;
        DECLARE @pk_is_template_id BIT = 0;

        SELECT TOP (1)
            @existing_pk = kc.name,
            @pk_template_cols = SUM(CASE WHEN c.name = 'template_id' THEN 1 ELSE 0 END),
            @pk_total_cols    = COUNT(*)
        FROM sys.key_constraints kc
        JOIN sys.index_columns ic
            ON ic.object_id = kc.parent_object_id
           AND ic.index_id = kc.unique_index_id
        JOIN sys.columns c
            ON c.object_id = ic.object_id
           AND c.column_id = ic.column_id
        WHERE kc.parent_object_id = OBJECT_ID('dbo.ServiceTemplates')
          AND kc.[type] = 'PK'
        GROUP BY kc.name
        ORDER BY kc.name;

        IF @pk_template_cols = 1 AND @pk_total_cols = 1
        BEGIN
            SET @pk_is_template_id = 1;
        END;

        IF @existing_pk IS NOT NULL AND @pk_is_template_id = 0
        BEGIN
            DECLARE @sql_drop_pk NVARCHAR(MAX) = N'ALTER TABLE dbo.ServiceTemplates DROP CONSTRAINT '
                                                + QUOTENAME(@existing_pk) + N';';
            EXEC(@sql_drop_pk);
        END;

        IF @pk_is_template_id = 0
        BEGIN
            ALTER TABLE dbo.ServiceTemplates
            ADD CONSTRAINT PK_ServiceTemplates PRIMARY KEY (template_id);
        END;
    END;
END;

-- Ensure template_id is a primary key (or unique) so it can be referenced by foreign keys
IF OBJECT_ID('dbo.ServiceTemplates','U') IS NOT NULL
BEGIN
    IF COL_LENGTH('dbo.ServiceTemplates','template_id') IS NOT NULL
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM sys.indexes i
            JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE i.is_primary_key = 1
              AND i.object_id = OBJECT_ID('dbo.ServiceTemplates')
              AND c.name = 'template_id'
        )
        BEGIN
            ALTER TABLE dbo.ServiceTemplates
            ADD CONSTRAINT PK_ServiceTemplates PRIMARY KEY (template_id);
        END;
    END;
END;

IF OBJECT_ID('dbo.ServiceTemplateItems','U') IS NULL
BEGIN
    CREATE TABLE dbo.ServiceTemplateItems (
        template_item_id  INT IDENTITY PRIMARY KEY,
        template_id       INT NOT NULL,
        phase             NVARCHAR(100) NOT NULL,       -- e.g. "Phase 4/5 ??" Digital Production"
        service_code      NVARCHAR(50) NOT NULL,        -- INIT / PROD / AUDIT / HANDOVER
        service_name      NVARCHAR(200) NOT NULL,       -- e.g. "BIM Coordination Review Cycles"
        unit_type         NVARCHAR(50) NOT NULL,        -- review / audit / lump_sum / license
        default_units     DECIMAL(10,2) NULL,           -- e.g. 12
        unit_rate         DECIMAL(18,2) NULL,
        lump_sum_fee      DECIMAL(18,2) NULL,
        bill_rule         NVARCHAR(50) NOT NULL,        -- on_setup / per_unit_complete / on_report_issue / fixed_schedule
        notes             NVARCHAR(MAX) NULL
    );
END;

-- Add the foreign key after table creation to ensure the referenced key exists
IF OBJECT_ID('dbo.ServiceTemplateItems','U') IS NOT NULL
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM sys.foreign_keys fk
        JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
        WHERE fk.parent_object_id = OBJECT_ID('dbo.ServiceTemplateItems')
          AND fkc.referenced_object_id = OBJECT_ID('dbo.ServiceTemplates')
          AND COL_NAME(fkc.parent_object_id, fkc.parent_column_id) = 'template_id'
    )
    BEGIN
        ALTER TABLE dbo.ServiceTemplateItems
        ADD CONSTRAINT FK_ServiceTemplateItems_TemplateId FOREIGN KEY (template_id)
            REFERENCES dbo.ServiceTemplates (template_id) ON DELETE CASCADE;
    END;
END;
-- 3.3 Project Services (agreed scope from proposal, shows in left grid)
IF OBJECT_ID('dbo.ProjectServices','U') IS NULL
BEGIN
    CREATE TABLE dbo.ProjectServices (
        service_id        INT IDENTITY PRIMARY KEY,
        project_id        INT NOT NULL REFERENCES dbo.Projects(project_id) ON DELETE CASCADE,
        phase             NVARCHAR(100) NOT NULL,
        service_code      NVARCHAR(50) NOT NULL,     -- INIT / PROD / AUDIT / HANDOVER
        service_name      NVARCHAR(200) NOT NULL,
        unit_type         NVARCHAR(50) NOT NULL,     -- review / audit / lump_sum / license
        unit_qty          DECIMAL(10,2) NULL,
        unit_rate         DECIMAL(18,2) NULL,
        lump_sum_fee      DECIMAL(18,2) NULL,
        agreed_fee        DECIMAL(18,2) NOT NULL,    -- computed or direct
        bill_rule         NVARCHAR(50) NOT NULL,
        status            NVARCHAR(30) NOT NULL DEFAULT 'not_started',
        variation_flag    BIT NOT NULL DEFAULT 0,
        notes             NVARCHAR(MAX) NULL,
        progress_pct      DECIMAL(9,4) NOT NULL DEFAULT 0, -- system-calculated
        claimed_to_date   DECIMAL(18,2) NOT NULL DEFAULT 0,
        remaining_amount  AS (agreed_fee - claimed_to_date) PERSISTED
    );
END;

-- 3.4 Review cycles (right scheduler)
IF OBJECT_ID('dbo.ServiceReviews','U') IS NULL
BEGIN
    CREATE TABLE dbo.ServiceReviews (
        review_id         INT IDENTITY PRIMARY KEY,
        service_id        INT NOT NULL REFERENCES dbo.ProjectServices(service_id) ON DELETE CASCADE,
        cycle_no          INT NOT NULL,                 -- 1..N
        planned_date      DATE NOT NULL,
        due_date          DATE NULL,
        disciplines       NVARCHAR(200) NULL,           -- tags: "All", "Arch,Str"
        deliverables      NVARCHAR(200) NULL,           -- "progress_report,issues"
        status            NVARCHAR(30) NOT NULL DEFAULT 'planned',
        weight_factor     DECIMAL(9,4) NOT NULL DEFAULT 1.0000,  -- for uneven cycles
        invoice_reference NVARCHAR(200) NULL,           -- invoice number or shared folder link
        evidence_links    NVARCHAR(MAX) NULL,           -- URLs to Revizto/ACC/reports
        actual_issued_at  DATETIME2 NULL,
        source_phase      NVARCHAR(200) NULL,
        billing_phase     NVARCHAR(200) NULL,
        billing_rate      DECIMAL(18,2) NULL,
        billing_amount    DECIMAL(18,2) NULL
    );
END;

-- 3.5 Deliverables per service (audits, PC reports, as-built reviews)
IF OBJECT_ID('dbo.ServiceDeliverables','U') IS NULL
BEGIN
    CREATE TABLE dbo.ServiceDeliverables (
        deliverable_id    INT IDENTITY PRIMARY KEY,
        service_id        INT NOT NULL REFERENCES dbo.ProjectServices(service_id) ON DELETE CASCADE,
        deliverable_type  NVARCHAR(50) NOT NULL,        -- audit_report / pc_report / asbuilt_review
        planned_date      DATE NULL,
        issued_date       DATE NULL,
        status            NVARCHAR(30) NOT NULL DEFAULT 'planned',
        bill_trigger      BIT NOT NULL DEFAULT 0,
        evidence_link     NVARCHAR(MAX) NULL
    );
END;

-- 3.6 Variations
IF OBJECT_ID('dbo.Variations','U') IS NULL
BEGIN
    CREATE TABLE dbo.Variations (
        variation_id      INT IDENTITY PRIMARY KEY,
        project_id        INT NOT NULL REFERENCES dbo.Projects(project_id) ON DELETE CASCADE,
        linked_service_id INT NULL REFERENCES dbo.ProjectServices(service_id),
        description       NVARCHAR(500) NOT NULL,
        unit_qty          DECIMAL(10,2) NULL,
        unit_rate         DECIMAL(18,2) NULL,
        lump_sum_fee      DECIMAL(18,2) NULL,
        approved_date     DATE NULL,
        status            NVARCHAR(30) NOT NULL DEFAULT 'proposed'
    );
END;

-- 3.7 Billing claims (month-end)
IF OBJECT_ID('dbo.BillingClaims','U') IS NULL
BEGIN
    CREATE TABLE dbo.BillingClaims (
        claim_id          INT IDENTITY PRIMARY KEY,
        project_id        INT NOT NULL REFERENCES dbo.Projects(project_id) ON DELETE CASCADE,
        period_start      DATE NOT NULL,
        period_end        DATE NOT NULL,
        po_ref            NVARCHAR(100) NULL,
        invoice_ref       NVARCHAR(100) NULL,          -- set when issued
        status            NVARCHAR(30) NOT NULL DEFAULT 'draft',
        created_at        DATETIME2 DEFAULT SYSDATETIME()
    );
END;

IF OBJECT_ID('dbo.BillingClaimLines','U') IS NULL
BEGIN
    CREATE TABLE dbo.BillingClaimLines (
        line_id           INT IDENTITY PRIMARY KEY,
        claim_id          INT NOT NULL REFERENCES dbo.BillingClaims(claim_id) ON DELETE CASCADE,
        service_id        INT NOT NULL REFERENCES dbo.ProjectServices(service_id),
        stage_label       NVARCHAR(200) NOT NULL,      -- e.g., "Phase 7 – Digital Production"
        prev_pct          DECIMAL(9,4) NOT NULL,       -- snapshot before this claim
        curr_pct          DECIMAL(9,4) NOT NULL,       -- snapshot at claim time
        delta_pct         AS (CASE WHEN curr_pct >= prev_pct THEN curr_pct - prev_pct ELSE 0 END) PERSISTED,
        amount_this_claim DECIMAL(18,2) NOT NULL,
        note              NVARCHAR(400) NULL
    );
END;

-- Helpful indexes
IF OBJECT_ID(N'dbo.ProjectServices', N'U') IS NOT NULL
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = N'IX_ProjectServices_ProjectPhase'
          AND object_id = OBJECT_ID(N'dbo.ProjectServices', N'U')
    )
    BEGIN
        CREATE INDEX IX_ProjectServices_ProjectPhase
            ON dbo.ProjectServices(project_id, phase);
    END;
END;

IF OBJECT_ID(N'dbo.ServiceReviews', N'U') IS NOT NULL
BEGIN
    DROP INDEX IF EXISTS IX_ServiceReviews_ServiceDate ON dbo.ServiceReviews;

    IF EXISTS (
        SELECT 1
        FROM sys.stats
        WHERE name = N'IX_ServiceReviews_ServiceDate'
          AND object_id = OBJECT_ID(N'dbo.ServiceReviews', N'U')
    )
    BEGIN
        DROP STATISTICS dbo.ServiceReviews.IX_ServiceReviews_ServiceDate;
    END;

    CREATE INDEX IX_ServiceReviews_ServiceDate
        ON dbo.ServiceReviews(service_id, planned_date);
END;

IF OBJECT_ID(N'dbo.BillingClaimLines', N'U') IS NOT NULL
BEGIN
    DROP INDEX IF EXISTS IX_BillingLines_ClaimService ON dbo.BillingClaimLines;

    IF EXISTS (
        SELECT 1
        FROM sys.stats
        WHERE name = N'IX_BillingLines_ClaimService'
          AND object_id = OBJECT_ID(N'dbo.BillingClaimLines', N'U')
    )
    BEGIN
        DROP STATISTICS dbo.BillingClaimLines.IX_BillingLines_ClaimService;
    END;

    CREATE INDEX IX_BillingLines_ClaimService
        ON dbo.BillingClaimLines(claim_id, service_id);
END;


GO



-- 6. Timeline reporting view (derived completion state for UI timeline)
CREATE OR ALTER VIEW dbo.vw_ServiceReviewTimeline
AS
SELECT
    p.project_id,
    p.name                  AS project_name,
    ps.service_id,
    ps.phase                AS service_phase,
    ps.service_code,
    ps.service_name,
    sr.review_id,
    sr.cycle_no,
    sr.planned_date,
    sr.due_date,
    sr.status,
    sr.actual_issued_at,
    CASE
        WHEN sr.status IN ('report_issued','closed')
             OR sr.actual_issued_at IS NOT NULL
             OR (sr.due_date IS NOT NULL AND sr.due_date < CAST(SYSDATETIME() AS DATE))
        THEN 1 ELSE 0
    END AS timeline_is_complete,
    CASE
        WHEN sr.status IN ('report_issued','closed') THEN sr.status
        WHEN sr.actual_issued_at IS NOT NULL THEN 'completed_manual'
        WHEN sr.due_date IS NOT NULL AND sr.due_date < CAST(SYSDATETIME() AS DATE) THEN 'completed_auto'
        WHEN sr.planned_date < CAST(SYSDATETIME() AS DATE) THEN 'overdue'
        ELSE sr.status
    END AS timeline_state,
    CASE
        WHEN sr.actual_issued_at IS NOT NULL THEN sr.actual_issued_at
        WHEN sr.due_date IS NOT NULL THEN CAST(sr.due_date AS DATETIME2)
        ELSE CAST(sr.planned_date AS DATETIME2)
    END AS timeline_sort_key
FROM dbo.ServiceReviews sr
JOIN dbo.ProjectServices ps ON ps.service_id = sr.service_id
JOIN dbo.Projects p         ON p.project_id  = ps.project_id;

-- Functions and stored procedures
GO

-- 7.1 Recompute service progress (unitised)
CREATE OR ALTER FUNCTION dbo.fn_ServiceProgressPct(@service_id INT)
RETURNS DECIMAL(9,4)
AS
BEGIN
    DECLARE @num DECIMAL(18,6) = (
        SELECT COALESCE(SUM(weight_factor),0)
        FROM dbo.ServiceReviews
        WHERE service_id = @service_id
          AND status IN ('report_issued','closed')
    );
    DECLARE @den DECIMAL(18,6) = (
        SELECT COALESCE(SUM(weight_factor),0)
        FROM dbo.ServiceReviews
        WHERE service_id = @service_id
    );
    RETURN CASE WHEN @den = 0 THEN 0 ELSE CAST((@num/@den)*100.0 AS DECIMAL(9,4)) END;
END;
GO

-- 7.2 Apply to service on write (trigger)
CREATE OR ALTER TRIGGER dbo.trg_ServiceReviews_Progress
ON dbo.ServiceReviews
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    ;WITH S AS (
        SELECT DISTINCT service_id FROM inserted
        UNION
        SELECT DISTINCT service_id FROM deleted
    )
    UPDATE ps
    SET progress_pct =
        CASE 
            WHEN ps.unit_type = 'review'     THEN dbo.fn_ServiceProgressPct(ps.service_id)
            WHEN ps.unit_type = 'audit'      THEN CASE WHEN EXISTS (
                    SELECT 1 FROM dbo.ServiceDeliverables d 
                    WHERE d.service_id = ps.service_id AND d.status='issued'
                ) THEN 100 ELSE 0 END
            WHEN ps.unit_type = 'lump_sum'   THEN ps.progress_pct -- set via UI toggle or setup-tasks trigger
            ELSE ps.progress_pct
        END
    FROM dbo.ProjectServices ps
    JOIN S ON S.service_id = ps.service_id;
END;
GO

-- 7.3 Generate claim (stored proc)
CREATE OR ALTER PROCEDURE dbo.sp_GenerateClaim
    @project_id INT,
    @period_start DATE,
    @period_end   DATE,
    @po_ref NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.BillingClaims(project_id, period_start, period_end, po_ref)
    VALUES (@project_id, @period_start, @period_end, @po_ref);

    DECLARE @claim_id INT = SCOPE_IDENTITY();

    ;WITH P AS (
        SELECT ps.service_id, ps.phase,
               ps.agreed_fee, ps.progress_pct AS curr_pct,
               COALESCE((
                 SELECT TOP 1 l.curr_pct
                 FROM dbo.BillingClaims c
                 JOIN dbo.BillingClaimLines l ON l.claim_id = c.claim_id AND l.service_id = ps.service_id
                 WHERE c.project_id = @project_id
                 ORDER BY c.created_at DESC
               ), 0) AS prev_pct
        FROM dbo.ProjectServices ps
        WHERE ps.project_id = @project_id
    )
    INSERT INTO dbo.BillingClaimLines (claim_id, service_id, stage_label, prev_pct, curr_pct, amount_this_claim, note)
    SELECT
        @claim_id, service_id, phase, prev_pct, curr_pct,
        CAST(agreed_fee * CASE WHEN curr_pct > prev_pct THEN (curr_pct - prev_pct)/100.0 ELSE 0 END AS DECIMAL(18,2)) AS amount_this_claim,
        NULL
    FROM P;

    SELECT * FROM dbo.BillingClaims WHERE claim_id = @claim_id;
    SELECT * FROM dbo.BillingClaimLines WHERE claim_id = @claim_id;
END;
GO
