-- Bid management schema migration (idempotent).

IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'Bids'
)
BEGIN
    CREATE TABLE dbo.Bids (
        bid_id INT IDENTITY(1,1) PRIMARY KEY,
        project_id INT NULL,
        client_id INT NULL,
        bid_name NVARCHAR(255) NOT NULL,
        bid_type NVARCHAR(30) NOT NULL,
        status NVARCHAR(30) NOT NULL,
        probability INT NULL,
        owner_user_id INT NULL,
        currency_code NVARCHAR(10) NOT NULL CONSTRAINT DF_Bids_currency_code DEFAULT ('AUD'),
        stage_framework NVARCHAR(50) NOT NULL,
        validity_days INT NULL,
        gst_included BIT NOT NULL CONSTRAINT DF_Bids_gst_included DEFAULT (1),
        pi_notes NVARCHAR(MAX) NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_Bids_created_at DEFAULT (SYSDATETIME()),
        updated_at DATETIME2 NOT NULL CONSTRAINT DF_Bids_updated_at DEFAULT (SYSDATETIME()),
        CONSTRAINT FK_Bids_Project FOREIGN KEY (project_id) REFERENCES dbo.projects(project_id),
        CONSTRAINT FK_Bids_Client FOREIGN KEY (client_id) REFERENCES dbo.clients(client_id),
        CONSTRAINT FK_Bids_Owner FOREIGN KEY (owner_user_id) REFERENCES dbo.users(user_id),
        CONSTRAINT CK_Bids_Type CHECK (bid_type IN ('PROPOSAL', 'FEE_UPDATE', 'VARIATION')),
        CONSTRAINT CK_Bids_Status CHECK (status IN ('DRAFT', 'SUBMITTED', 'AWARDED', 'LOST', 'ARCHIVED'))
    );
END;

IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'BidSections'
)
BEGIN
    CREATE TABLE dbo.BidSections (
        bid_section_id INT IDENTITY(1,1) PRIMARY KEY,
        bid_id INT NOT NULL,
        section_key NVARCHAR(80) NOT NULL,
        content_json NVARCHAR(MAX) NULL,
        sort_order INT NOT NULL CONSTRAINT DF_BidSections_sort_order DEFAULT (0),
        CONSTRAINT FK_BidSections_Bid FOREIGN KEY (bid_id) REFERENCES dbo.Bids(bid_id)
    );
END;

IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'BidScopeItems'
)
BEGIN
    CREATE TABLE dbo.BidScopeItems (
        scope_item_id INT IDENTITY(1,1) PRIMARY KEY,
        bid_id INT NOT NULL,
        service_code NVARCHAR(50) NULL,
        title NVARCHAR(255) NOT NULL,
        description NVARCHAR(MAX) NULL,
        stage_name NVARCHAR(200) NULL,
        deliverables_json NVARCHAR(MAX) NULL,
        included_qty DECIMAL(18,2) NULL,
        unit NVARCHAR(50) NULL,
        unit_rate DECIMAL(18,2) NULL,
        lump_sum DECIMAL(18,2) NULL,
        is_optional BIT NOT NULL CONSTRAINT DF_BidScopeItems_is_optional DEFAULT (0),
        option_group NVARCHAR(200) NULL,
        sort_order INT NOT NULL CONSTRAINT DF_BidScopeItems_sort_order DEFAULT (0),
        CONSTRAINT FK_BidScopeItems_Bid FOREIGN KEY (bid_id) REFERENCES dbo.Bids(bid_id)
    );
END;

IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'BidProgramStages'
)
BEGIN
    CREATE TABLE dbo.BidProgramStages (
        program_stage_id INT IDENTITY(1,1) PRIMARY KEY,
        bid_id INT NOT NULL,
        stage_name NVARCHAR(200) NOT NULL,
        planned_start DATE NULL,
        planned_end DATE NULL,
        cadence NVARCHAR(50) NULL,
        cycles_planned INT NULL,
        sort_order INT NOT NULL CONSTRAINT DF_BidProgramStages_sort_order DEFAULT (0),
        CONSTRAINT FK_BidProgramStages_Bid FOREIGN KEY (bid_id) REFERENCES dbo.Bids(bid_id)
    );
END;

IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'BidBillingSchedule'
)
BEGIN
    CREATE TABLE dbo.BidBillingSchedule (
        billing_line_id INT IDENTITY(1,1) PRIMARY KEY,
        bid_id INT NOT NULL,
        period_start DATE NOT NULL,
        period_end DATE NOT NULL,
        amount DECIMAL(18,2) NOT NULL,
        notes NVARCHAR(500) NULL,
        sort_order INT NOT NULL CONSTRAINT DF_BidBillingSchedule_sort_order DEFAULT (0),
        CONSTRAINT FK_BidBillingSchedule_Bid FOREIGN KEY (bid_id) REFERENCES dbo.Bids(bid_id)
    );
END;

IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'BidAwardSummary'
)
BEGIN
    CREATE TABLE dbo.BidAwardSummary (
        award_id INT IDENTITY(1,1) PRIMARY KEY,
        bid_id INT NOT NULL,
        project_id INT NOT NULL,
        created_services INT NOT NULL,
        created_reviews INT NOT NULL,
        created_claims INT NOT NULL,
        service_ids_json NVARCHAR(MAX) NULL,
        review_ids_json NVARCHAR(MAX) NULL,
        claim_ids_json NVARCHAR(MAX) NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_BidAwardSummary_created_at DEFAULT (SYSDATETIME()),
        updated_at DATETIME2 NOT NULL CONSTRAINT DF_BidAwardSummary_updated_at DEFAULT (SYSDATETIME()),
        CONSTRAINT UQ_BidAwardSummary_bid UNIQUE (bid_id),
        CONSTRAINT FK_BidAwardSummary_Bid FOREIGN KEY (bid_id) REFERENCES dbo.Bids(bid_id),
        CONSTRAINT FK_BidAwardSummary_Project FOREIGN KEY (project_id) REFERENCES dbo.projects(project_id)
    );
END;

IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'BidVariations'
)
BEGIN
    CREATE TABLE dbo.BidVariations (
        variation_id INT IDENTITY(1,1) PRIMARY KEY,
        project_id INT NOT NULL,
        bid_id INT NULL,
        title NVARCHAR(255) NOT NULL,
        description NVARCHAR(MAX) NULL,
        baseline_contract_value DECIMAL(18,2) NULL,
        remaining_value DECIMAL(18,2) NULL,
        proposed_change_value DECIMAL(18,2) NOT NULL,
        status NVARCHAR(30) NOT NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_BidVariations_created_at DEFAULT (SYSDATETIME()),
        updated_at DATETIME2 NOT NULL CONSTRAINT DF_BidVariations_updated_at DEFAULT (SYSDATETIME()),
        CONSTRAINT FK_BidVariations_Project FOREIGN KEY (project_id) REFERENCES dbo.projects(project_id),
        CONSTRAINT FK_BidVariations_Bid FOREIGN KEY (bid_id) REFERENCES dbo.Bids(bid_id),
        CONSTRAINT CK_BidVariations_Status CHECK (status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED'))
    );
END;
