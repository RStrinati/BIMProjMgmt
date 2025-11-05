-- Bridge: Review Cycle ↔ Issue
-- Links review cycles to issues that were created/closed/active during the review window

USE ProjectManagement;
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'brg')
BEGIN
    EXEC('CREATE SCHEMA brg AUTHORIZATION dbo;');
END
GO

IF OBJECT_ID('brg.review_issue', 'U') IS NULL
BEGIN
    CREATE TABLE brg.review_issue (
        review_issue_bridge_sk INT IDENTITY PRIMARY KEY,
        review_cycle_sk        INT NOT NULL,
        issue_sk               INT NOT NULL,
        relationship_type      NVARCHAR(50) NOT NULL,  -- 'opened_during', 'closed_during', 'active_during'
        created_at             DATETIME2 DEFAULT SYSUTCDATETIME(),
        CONSTRAINT fk_brg_review_issue_review FOREIGN KEY (review_cycle_sk) REFERENCES dim.review_cycle(review_cycle_sk),
        CONSTRAINT fk_brg_review_issue_issue  FOREIGN KEY (issue_sk) REFERENCES dim.issue(issue_sk)
    );

    CREATE INDEX ix_review_issue_review ON brg.review_issue(review_cycle_sk);
    CREATE INDEX ix_review_issue_issue ON brg.review_issue(issue_sk);
    CREATE INDEX ix_review_issue_type ON brg.review_issue(relationship_type);
END
GO
