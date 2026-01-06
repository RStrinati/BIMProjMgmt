/*
    Seed issue category lookup from ProjectManagement IssueCategories.
*/

USE ProjectManagement;
GO

INSERT INTO stg.issue_categories (
    category_id,
    category_name,
    parent_category_id,
    category_level,
    description,
    record_source
)
SELECT
    ic.category_id,
    ic.category_name,
    ic.parent_category_id,
    ic.category_level,
    ic.description,
    'seed_issue_categories_from_pm.sql'
FROM dbo.IssueCategories ic;

PRINT 'Seeded stg.issue_categories from dbo.IssueCategories';
GO
