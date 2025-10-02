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

-- 3.2 Service Templates (library)
CREATE TABLE dbo.ServiceTemplates (
    template_id       INT IDENTITY PRIMARY KEY,
    name              NVARCHAR(200) NOT NULL,   -- e.g. "SINSW – MPHS"
    sector            NVARCHAR(100) NULL,       -- e.g. "Education", "AWS", "Data Centre"
    notes             NVARCHAR(MAX) NULL,
    created_at        DATETIME2 DEFAULT SYSDATETIME()
);

CREATE TABLE dbo.ServiceTemplateItems (
    template_item_id  INT IDENTITY PRIMARY KEY,
    template_id       INT NOT NULL REFERENCES dbo.ServiceTemplates(template_id) ON DELETE CASCADE,
    phase             NVARCHAR(100) NOT NULL,       -- e.g. "Phase 4/5 – Digital Production"
    service_code      NVARCHAR(50) NOT NULL,        -- INIT / PROD / AUDIT / HANDOVER
    service_name      NVARCHAR(200) NOT NULL,       -- e.g. "BIM Coordination Review Cycles"
    unit_type         NVARCHAR(50) NOT NULL,        -- review / audit / lump_sum / license
    default_units     DECIMAL(10,2) NULL,           -- e.g. 12
    unit_rate         DECIMAL(18,2) NULL,
    lump_sum_fee      DECIMAL(18,2) NULL,
    bill_rule         NVARCHAR(50) NOT NULL,        -- on_setup / per_unit_complete / on_report_issue / fixed_schedule
    notes             NVARCHAR(MAX) NULL
);

-- 3.3 Project Services (agreed scope from proposal, shows in left grid)
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

-- 3.4 Review cycles (right scheduler)
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
    evidence_links    NVARCHAR(MAX) NULL,           -- URLs to Revizto/ACC/reports
    actual_issued_at  DATETIME2 NULL
);

-- 3.5 Deliverables per service (audits, PC reports, as-built reviews)
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

-- 3.6 Variations
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

-- 3.7 Billing claims (month-end)
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

-- Helpful indexes
CREATE INDEX IX_ProjectServices_ProjectPhase ON dbo.ProjectServices(project_id, phase);
CREATE INDEX IX_ServiceReviews_ServiceDate   ON dbo.ServiceReviews(service_id, planned_date);
CREATE INDEX IX_BillingLines_ClaimService    ON dbo.BillingClaimLines(claim_id, service_id);

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
