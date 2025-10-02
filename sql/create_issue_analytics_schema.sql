-- =====================================================================
-- Issue Analytics System - Database Schema
-- Creates tables, views, and indexes for issue analysis and categorization
-- =====================================================================

USE ProjectManagement;
GO

-- =====================================================================
-- TABLE: IssueCategories
-- Hierarchical taxonomy for issue classification
-- =====================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'IssueCategories')
BEGIN
    CREATE TABLE IssueCategories (
        category_id INT IDENTITY(1,1) PRIMARY KEY,
        category_name NVARCHAR(100) NOT NULL,
        parent_category_id INT NULL,
        category_level INT NOT NULL, -- 1: Discipline, 2: Type, 3: Sub-type
        description NVARCHAR(500),
        display_order INT DEFAULT 0,
        is_active BIT DEFAULT 1,
        created_at DATETIME2 DEFAULT GETDATE(),
        updated_at DATETIME2 DEFAULT GETDATE(),
        FOREIGN KEY (parent_category_id) REFERENCES IssueCategories(category_id),
        CONSTRAINT chk_category_level CHECK (category_level BETWEEN 1 AND 3)
    );
    
    PRINT '✓ Created table: IssueCategories';
END
ELSE
    PRINT '→ Table already exists: IssueCategories';
GO

-- =====================================================================
-- TABLE: IssueCategoryKeywords
-- Keyword mapping for automated categorization
-- =====================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'IssueCategoryKeywords')
BEGIN
    CREATE TABLE IssueCategoryKeywords (
        keyword_id INT IDENTITY(1,1) PRIMARY KEY,
        category_id INT NOT NULL,
        keyword NVARCHAR(100) NOT NULL,
        weight DECIMAL(3,2) DEFAULT 1.0, -- For relevance scoring (0.0 to 1.0)
        is_active BIT DEFAULT 1,
        created_at DATETIME2 DEFAULT GETDATE(),
        FOREIGN KEY (category_id) REFERENCES IssueCategories(category_id),
        CONSTRAINT chk_keyword_weight CHECK (weight BETWEEN 0.0 AND 1.0),
        CONSTRAINT uq_category_keyword UNIQUE (category_id, keyword)
    );
    
    CREATE INDEX idx_keywords_category ON IssueCategoryKeywords(category_id);
    CREATE INDEX idx_keywords_active ON IssueCategoryKeywords(is_active) WHERE is_active = 1;
    
    PRINT '✓ Created table: IssueCategoryKeywords';
END
ELSE
    PRINT '→ Table already exists: IssueCategoryKeywords';
GO

-- =====================================================================
-- TABLE: ProcessedIssues
-- Stores categorized and analyzed issues
-- =====================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ProcessedIssues')
BEGIN
    CREATE TABLE ProcessedIssues (
        processed_issue_id INT IDENTITY(1,1) PRIMARY KEY,
        
        -- Source identification
        source NVARCHAR(50) NOT NULL, -- 'ACC' or 'Revizto'
        source_issue_id NVARCHAR(255) NOT NULL,
        project_id INT NOT NULL,
        
        -- Issue content
        title NVARCHAR(500),
        description NVARCHAR(MAX),
        status NVARCHAR(50),
        priority NVARCHAR(50),
        assignee NVARCHAR(255),
        author NVARCHAR(255),
        
        -- Dates
        created_at DATETIME2,
        closed_at DATETIME2,
        last_activity_date DATETIME2,
        
        -- Categorization
        primary_category_id INT,
        secondary_category_id INT,
        discipline_category_id INT,
        categorization_confidence DECIMAL(3,2), -- 0.0 to 1.0
        
        -- Text Analysis
        sentiment_score DECIMAL(3,2), -- -1.0 to +1.0
        urgency_score DECIMAL(3,2), -- 0.0 to 1.0
        complexity_score DECIMAL(3,2), -- 0.0 to 1.0
        extracted_keywords NVARCHAR(MAX), -- JSON array
        
        -- Metrics
        resolution_days INT,
        comment_count INT DEFAULT 0,
        is_recurring BIT DEFAULT 0,
        recurring_cluster_id INT NULL,
        
        -- Processing metadata
        processed_at DATETIME2 DEFAULT GETDATE(),
        processing_version NVARCHAR(20) DEFAULT '1.0',
        needs_review BIT DEFAULT 0, -- Flag for manual review
        
        FOREIGN KEY (project_id) REFERENCES projects(project_id),
        FOREIGN KEY (primary_category_id) REFERENCES IssueCategories(category_id),
        FOREIGN KEY (secondary_category_id) REFERENCES IssueCategories(category_id),
        FOREIGN KEY (discipline_category_id) REFERENCES IssueCategories(category_id),
        
        CONSTRAINT uq_source_issue UNIQUE (source, source_issue_id),
        CONSTRAINT chk_sentiment_range CHECK (sentiment_score BETWEEN -1.0 AND 1.0),
        CONSTRAINT chk_urgency_range CHECK (urgency_score BETWEEN 0.0 AND 1.0),
        CONSTRAINT chk_complexity_range CHECK (complexity_score BETWEEN 0.0 AND 1.0),
        CONSTRAINT chk_confidence_range CHECK (categorization_confidence BETWEEN 0.0 AND 1.0)
    );
    
    -- Performance indexes
    CREATE INDEX idx_processed_issues_project ON ProcessedIssues(project_id);
    CREATE INDEX idx_processed_issues_status ON ProcessedIssues(status);
    CREATE INDEX idx_processed_issues_dates ON ProcessedIssues(created_at, closed_at);
    CREATE INDEX idx_processed_issues_primary_cat ON ProcessedIssues(primary_category_id);
    CREATE INDEX idx_processed_issues_discipline ON ProcessedIssues(discipline_category_id);
    CREATE INDEX idx_processed_issues_project_status ON ProcessedIssues(project_id, status) 
        INCLUDE (primary_category_id, urgency_score);
    CREATE INDEX idx_processed_issues_recurring ON ProcessedIssues(is_recurring, recurring_cluster_id) 
        WHERE is_recurring = 1;
    
    PRINT '✓ Created table: ProcessedIssues';
END
ELSE
    PRINT '→ Table already exists: ProcessedIssues';
GO

-- =====================================================================
-- TABLE: IssuePainPoints
-- Aggregated pain point analysis by client/project type
-- =====================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'IssuePainPoints')
BEGIN
    CREATE TABLE IssuePainPoints (
        pain_point_id INT IDENTITY(1,1) PRIMARY KEY,
        
        -- Segmentation
        client_id INT NULL,
        project_type_id INT NULL,
        category_id INT NOT NULL,
        
        -- Time window
        period_start DATE NOT NULL,
        period_end DATE NOT NULL,
        
        -- Metrics
        total_issues INT NOT NULL DEFAULT 0,
        open_issues INT NOT NULL DEFAULT 0,
        closed_issues INT NOT NULL DEFAULT 0,
        
        -- Performance indicators
        avg_resolution_days DECIMAL(6,2),
        median_resolution_days INT,
        max_resolution_days INT,
        
        -- Severity
        critical_count INT DEFAULT 0,
        high_priority_count INT DEFAULT 0,
        recurring_issue_count INT DEFAULT 0,
        
        -- Trend indicators
        issues_this_period INT DEFAULT 0,
        issues_prev_period INT DEFAULT 0,
        trend_direction NVARCHAR(20), -- 'increasing', 'decreasing', 'stable'
        
        -- Insights
        common_keywords NVARCHAR(MAX), -- JSON array
        sample_issue_ids NVARCHAR(MAX), -- JSON array of representative issues
        
        -- Metadata
        calculated_at DATETIME2 DEFAULT GETDATE(),
        
        FOREIGN KEY (client_id) REFERENCES clients(client_id),
        FOREIGN KEY (project_type_id) REFERENCES project_types(project_type_id),
        FOREIGN KEY (category_id) REFERENCES IssueCategories(category_id),
        
        CONSTRAINT chk_period_dates CHECK (period_end >= period_start)
    );
    
    CREATE INDEX idx_pain_points_client ON IssuePainPoints(client_id);
    CREATE INDEX idx_pain_points_type ON IssuePainPoints(project_type_id);
    CREATE INDEX idx_pain_points_category ON IssuePainPoints(category_id);
    CREATE INDEX idx_pain_points_period ON IssuePainPoints(period_start, period_end);
    
    PRINT '✓ Created table: IssuePainPoints';
END
ELSE
    PRINT '→ Table already exists: IssuePainPoints';
GO

-- =====================================================================
-- TABLE: IssueComments
-- Extracted comments for deeper analysis
-- =====================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'IssueComments')
BEGIN
    CREATE TABLE IssueComments (
        comment_id INT IDENTITY(1,1) PRIMARY KEY,
        processed_issue_id INT NOT NULL,
        
        comment_text NVARCHAR(MAX),
        comment_by NVARCHAR(255),
        comment_at DATETIME2,
        
        -- Analysis
        sentiment_score DECIMAL(3,2),
        is_resolution BIT DEFAULT 0, -- Indicates resolution comment
        contains_action_item BIT DEFAULT 0,
        
        -- Metadata
        extracted_at DATETIME2 DEFAULT GETDATE(),
        
        FOREIGN KEY (processed_issue_id) REFERENCES ProcessedIssues(processed_issue_id) ON DELETE CASCADE,
        CONSTRAINT chk_comment_sentiment CHECK (sentiment_score BETWEEN -1.0 AND 1.0)
    );
    
    CREATE INDEX idx_comments_issue ON IssueComments(processed_issue_id);
    CREATE INDEX idx_comments_date ON IssueComments(comment_at);
    
    PRINT '✓ Created table: IssueComments';
END
ELSE
    PRINT '→ Table already exists: IssueComments';
GO

-- =====================================================================
-- TABLE: IssueProcessingLog
-- Tracks batch processing jobs
-- =====================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'IssueProcessingLog')
BEGIN
    CREATE TABLE IssueProcessingLog (
        log_id INT IDENTITY(1,1) PRIMARY KEY,
        processing_type NVARCHAR(50) NOT NULL, -- 'bulk', 'incremental', 'reprocess'
        start_time DATETIME2 NOT NULL,
        end_time DATETIME2,
        
        issues_processed INT DEFAULT 0,
        issues_categorized INT DEFAULT 0,
        issues_failed INT DEFAULT 0,
        
        status NVARCHAR(50) DEFAULT 'running', -- 'running', 'completed', 'failed'
        error_message NVARCHAR(MAX),
        
        processing_parameters NVARCHAR(MAX), -- JSON config
        created_at DATETIME2 DEFAULT GETDATE()
    );
    
    CREATE INDEX idx_processing_log_date ON IssueProcessingLog(start_time);
    
    PRINT '✓ Created table: IssueProcessingLog';
END
ELSE
    PRINT '→ Table already exists: IssueProcessingLog';
GO

-- =====================================================================
-- VIEW: vw_IssueAnalytics_ByClient
-- Issue analytics aggregated by client
-- =====================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_IssueAnalytics_ByClient')
    DROP VIEW vw_IssueAnalytics_ByClient;
GO

CREATE VIEW vw_IssueAnalytics_ByClient AS
SELECT 
    c.client_id,
    c.client_name,
    ic.category_id,
    ic.category_name,
    ic.category_level,
    
    COUNT(pi.processed_issue_id) as total_issues,
    SUM(CASE WHEN pi.status IN ('open', 'in_progress', 'pending') THEN 1 ELSE 0 END) as open_issues,
    SUM(CASE WHEN pi.status IN ('closed', 'resolved', 'completed') THEN 1 ELSE 0 END) as closed_issues,
    
    AVG(pi.resolution_days) as avg_resolution_days,
    AVG(pi.urgency_score) as avg_urgency,
    AVG(pi.complexity_score) as avg_complexity,
    AVG(pi.sentiment_score) as avg_sentiment,
    
    SUM(CASE WHEN pi.is_recurring = 1 THEN 1 ELSE 0 END) as recurring_count,
    
    COUNT(DISTINCT pi.project_id) as project_count,
    
    MIN(pi.created_at) as earliest_issue,
    MAX(pi.created_at) as latest_issue
    
FROM ProcessedIssues pi
JOIN projects p ON pi.project_id = p.project_id
JOIN clients c ON p.client_id = c.client_id
JOIN IssueCategories ic ON pi.primary_category_id = ic.category_id

GROUP BY 
    c.client_id, 
    c.client_name, 
    ic.category_id,
    ic.category_name,
    ic.category_level;
GO

PRINT '✓ Created view: vw_IssueAnalytics_ByClient';
GO

-- =====================================================================
-- VIEW: vw_IssueAnalytics_ByProjectType
-- Issue analytics aggregated by project type
-- =====================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_IssueAnalytics_ByProjectType')
    DROP VIEW vw_IssueAnalytics_ByProjectType;
GO

CREATE VIEW vw_IssueAnalytics_ByProjectType AS
SELECT 
    pt.project_type_id,
    pt.project_type_name,
    ic.category_id,
    ic.category_name,
    ic.category_level,
    
    COUNT(pi.processed_issue_id) as total_issues,
    SUM(CASE WHEN pi.status IN ('open', 'in_progress', 'pending') THEN 1 ELSE 0 END) as open_issues,
    SUM(CASE WHEN pi.status IN ('closed', 'resolved', 'completed') THEN 1 ELSE 0 END) as closed_issues,
    
    AVG(pi.resolution_days) as avg_resolution_days,
    AVG(pi.urgency_score) as avg_urgency,
    AVG(pi.complexity_score) as avg_complexity,
    
    SUM(CASE WHEN pi.is_recurring = 1 THEN 1 ELSE 0 END) as recurring_count,
    
    COUNT(DISTINCT pi.project_id) as project_count
    
FROM ProcessedIssues pi
JOIN projects p ON pi.project_id = p.project_id
LEFT JOIN project_types pt ON p.type_id = pt.project_type_id
JOIN IssueCategories ic ON pi.primary_category_id = ic.category_id

GROUP BY 
    pt.project_type_id,
    pt.project_type_name,
    ic.category_id,
    ic.category_name,
    ic.category_level;
GO

PRINT '✓ Created view: vw_IssueAnalytics_ByProjectType';
GO

-- =====================================================================
-- VIEW: vw_IssueAnalytics_ByDiscipline
-- Issue analytics aggregated by discipline
-- =====================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_IssueAnalytics_ByDiscipline')
    DROP VIEW vw_IssueAnalytics_ByDiscipline;
GO

CREATE VIEW vw_IssueAnalytics_ByDiscipline AS
SELECT 
    ic.category_id as discipline_id,
    ic.category_name as discipline_name,
    
    COUNT(pi.processed_issue_id) as total_issues,
    SUM(CASE WHEN pi.status IN ('open', 'in_progress', 'pending') THEN 1 ELSE 0 END) as open_issues,
    
    AVG(pi.resolution_days) as avg_resolution_days,
    AVG(pi.urgency_score) as avg_urgency,
    AVG(pi.complexity_score) as avg_complexity,
    
    COUNT(DISTINCT pi.project_id) as project_count,
    COUNT(DISTINCT p.client_id) as client_count
    
FROM ProcessedIssues pi
JOIN projects p ON pi.project_id = p.project_id
JOIN IssueCategories ic ON pi.discipline_category_id = ic.category_id

WHERE ic.category_level = 1 -- Disciplines only

GROUP BY 
    ic.category_id,
    ic.category_name;
GO

PRINT '✓ Created view: vw_IssueAnalytics_ByDiscipline';
GO

-- =====================================================================
-- VIEW: vw_TopPainPoints
-- Top pain points across all projects
-- =====================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_TopPainPoints')
    DROP VIEW vw_TopPainPoints;
GO

CREATE VIEW vw_TopPainPoints AS
SELECT TOP 50
    ic.category_name,
    ic.category_level,
    c.client_name,
    pt.project_type_name,
    
    ipp.total_issues,
    ipp.open_issues,
    ipp.avg_resolution_days,
    ipp.recurring_issue_count,
    ipp.trend_direction,
    
    ipp.period_start,
    ipp.period_end,
    ipp.calculated_at
    
FROM IssuePainPoints ipp
JOIN IssueCategories ic ON ipp.category_id = ic.category_id
LEFT JOIN clients c ON ipp.client_id = c.client_id
LEFT JOIN project_types pt ON ipp.project_type_id = pt.project_type_id

WHERE ipp.period_end >= DATEADD(MONTH, -6, GETDATE()) -- Last 6 months

ORDER BY 
    ipp.total_issues DESC,
    ipp.avg_resolution_days DESC;
GO

PRINT '✓ Created view: vw_TopPainPoints';
GO

-- =====================================================================
-- VIEW: vw_RecurringIssues
-- Identifies recurring issues across projects
-- =====================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_RecurringIssues')
    DROP VIEW vw_RecurringIssues;
GO

CREATE VIEW vw_RecurringIssues AS
SELECT 
    pi.recurring_cluster_id,
    ic.category_name as primary_category,
    
    COUNT(pi.processed_issue_id) as occurrence_count,
    COUNT(DISTINCT pi.project_id) as project_count,
    COUNT(DISTINCT p.client_id) as client_count,
    
    STRING_AGG(CAST(pi.title AS NVARCHAR(MAX)), ' | ') as sample_titles,
    
    AVG(pi.urgency_score) as avg_urgency,
    AVG(pi.resolution_days) as avg_resolution_days,
    
    MIN(pi.created_at) as first_occurrence,
    MAX(pi.created_at) as last_occurrence
    
FROM ProcessedIssues pi
JOIN projects p ON pi.project_id = p.project_id
JOIN IssueCategories ic ON pi.primary_category_id = ic.category_id

WHERE pi.is_recurring = 1 AND pi.recurring_cluster_id IS NOT NULL

GROUP BY 
    pi.recurring_cluster_id,
    ic.category_name

HAVING COUNT(pi.processed_issue_id) >= 3

ORDER BY occurrence_count DESC;
GO

PRINT '✓ Created view: vw_RecurringIssues';
GO

-- =====================================================================
-- Summary
-- =====================================================================
PRINT '';
PRINT '============================================================';
PRINT 'Issue Analytics Schema Creation Complete';
PRINT '============================================================';
PRINT 'Tables Created: 6';
PRINT '  - IssueCategories';
PRINT '  - IssueCategoryKeywords';
PRINT '  - ProcessedIssues';
PRINT '  - IssuePainPoints';
PRINT '  - IssueComments';
PRINT '  - IssueProcessingLog';
PRINT '';
PRINT 'Views Created: 5';
PRINT '  - vw_IssueAnalytics_ByClient';
PRINT '  - vw_IssueAnalytics_ByProjectType';
PRINT '  - vw_IssueAnalytics_ByDiscipline';
PRINT '  - vw_TopPainPoints';
PRINT '  - vw_RecurringIssues';
PRINT '============================================================';
PRINT '';
PRINT 'Next Steps:';
PRINT '1. Run: sql/seed_issue_categories.sql';
PRINT '2. Run: sql/seed_category_keywords.sql';
PRINT '3. Verify: SELECT * FROM IssueCategories;';
PRINT '============================================================';
GO
