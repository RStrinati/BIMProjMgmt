-- =====================================================================
-- Issue Analytics System - Category Taxonomy Seed Data
-- Populates IssueCategories with initial discipline, type, and sub-type taxonomy
-- =====================================================================

USE ProjectManagement;
GO

PRINT 'Seeding Issue Categories...';
PRINT '';

-- =====================================================================
-- LEVEL 1: DISCIPLINES (Parent Categories)
-- =====================================================================
PRINT 'Creating Level 1 - Disciplines...';

INSERT INTO IssueCategories (category_name, parent_category_id, category_level, description, display_order)
VALUES 
    ('Structural', NULL, 1, 'Steel, concrete, foundations, load-bearing elements', 10),
    ('Architectural', NULL, 1, 'Façade, interiors, finishes, cladding', 20),
    ('Mechanical (HVAC)', NULL, 1, 'Ductwork, AHUs, chillers, ventilation', 30),
    ('Electrical', NULL, 1, 'Power, lighting, low voltage systems', 40),
    ('Hydraulic/Plumbing', NULL, 1, 'Water, drainage, gas, sanitary systems', 50),
    ('Fire Protection', NULL, 1, 'Sprinklers, fire systems, fire safety', 60),
    ('Civil', NULL, 1, 'Siteworks, earthworks, external drainage', 70),
    ('Multi-Discipline', NULL, 1, 'Issues affecting multiple disciplines', 80),
    ('Other/General', NULL, 1, 'General or uncategorized issues', 90);

PRINT '  ✓ Created 9 discipline categories';

-- =====================================================================
-- LEVEL 2: ISSUE TYPES (Children of Disciplines)
-- =====================================================================
PRINT 'Creating Level 2 - Issue Types...';

DECLARE @StructuralID INT = (SELECT category_id FROM IssueCategories WHERE category_name = 'Structural' AND category_level = 1);
DECLARE @ArchID INT = (SELECT category_id FROM IssueCategories WHERE category_name = 'Architectural' AND category_level = 1);
DECLARE @MechID INT = (SELECT category_id FROM IssueCategories WHERE category_name = 'Mechanical (HVAC)' AND category_level = 1);
DECLARE @ElecID INT = (SELECT category_id FROM IssueCategories WHERE category_name = 'Electrical' AND category_level = 1);
DECLARE @HydID INT = (SELECT category_id FROM IssueCategories WHERE category_name = 'Hydraulic/Plumbing' AND category_level = 1);
DECLARE @FireID INT = (SELECT category_id FROM IssueCategories WHERE category_name = 'Fire Protection' AND category_level = 1);
DECLARE @CivilID INT = (SELECT category_id FROM IssueCategories WHERE category_name = 'Civil' AND category_level = 1);
DECLARE @MultiID INT = (SELECT category_id FROM IssueCategories WHERE category_name = 'Multi-Discipline' AND category_level = 1);

-- Universal Issue Types (apply to all disciplines)
DECLARE @DisciplineID INT;
DECLARE discipline_cursor CURSOR FOR 
    SELECT category_id FROM IssueCategories WHERE category_level = 1 AND category_name != 'Other/General';

OPEN discipline_cursor;
FETCH NEXT FROM discipline_cursor INTO @DisciplineID;

WHILE @@FETCH_STATUS = 0
BEGIN
    INSERT INTO IssueCategories (category_name, parent_category_id, category_level, description, display_order)
    VALUES 
        ('Clash/Coordination', @DisciplineID, 2, 'Physical clashes, coordination issues', 10),
        ('Design Issue', @DisciplineID, 2, 'Design errors, incomplete design, design changes', 20),
        ('Information Issue', @DisciplineID, 2, 'Missing information, RFI required, clarifications', 30),
        ('Code Compliance', @DisciplineID, 2, 'Building code violations, standard non-compliance', 40),
        ('Constructability', @DisciplineID, 2, 'Cannot build as designed, installation difficulties', 50),
        ('Quality Issue', @DisciplineID, 2, 'Material defects, workmanship concerns', 60);
    
    FETCH NEXT FROM discipline_cursor INTO @DisciplineID;
END;

CLOSE discipline_cursor;
DEALLOCATE discipline_cursor;

PRINT '  ✓ Created 48 issue type categories (6 types x 8 disciplines)';

-- =====================================================================
-- LEVEL 3: SUB-TYPES (Specific issue details)
-- =====================================================================
PRINT 'Creating Level 3 - Sub-Types...';

-- Clash/Coordination Sub-types
DECLARE @ClashTypeID INT;
DECLARE clash_cursor CURSOR FOR 
    SELECT category_id FROM IssueCategories 
    WHERE category_name = 'Clash/Coordination' AND category_level = 2;

OPEN clash_cursor;
FETCH NEXT FROM clash_cursor INTO @ClashTypeID;

WHILE @@FETCH_STATUS = 0
BEGIN
    INSERT INTO IssueCategories (category_name, parent_category_id, category_level, description, display_order)
    VALUES 
        ('Hard Clash', @ClashTypeID, 3, 'Physical overlap of elements', 10),
        ('Clearance Issue', @ClashTypeID, 3, 'Insufficient clearance (<300mm)', 20),
        ('Penetration Conflict', @ClashTypeID, 3, 'Penetration alignment or sizing issues', 30),
        ('Access Conflict', @ClashTypeID, 3, 'Blocked access for installation or maintenance', 40),
        ('Service Routing', @ClashTypeID, 3, 'Service path conflicts or optimization', 50);
    
    FETCH NEXT FROM clash_cursor INTO @ClashTypeID;
END;

CLOSE clash_cursor;
DEALLOCATE clash_cursor;

PRINT '  ✓ Created clash/coordination sub-types';

-- Design Issue Sub-types
DECLARE @DesignTypeID INT;
DECLARE design_cursor CURSOR FOR 
    SELECT category_id FROM IssueCategories 
    WHERE category_name = 'Design Issue' AND category_level = 2;

OPEN design_cursor;
FETCH NEXT FROM design_cursor INTO @DesignTypeID;

WHILE @@FETCH_STATUS = 0
BEGIN
    INSERT INTO IssueCategories (category_name, parent_category_id, category_level, description, display_order)
    VALUES 
        ('Design Error', @DesignTypeID, 3, 'Incorrect design or calculation', 10),
        ('Incomplete Design', @DesignTypeID, 3, 'Missing design elements or details', 20),
        ('Design Change', @DesignTypeID, 3, 'Requested or required design modification', 30),
        ('Design Optimization', @DesignTypeID, 3, 'Suggested improvements or value engineering', 40);
    
    FETCH NEXT FROM design_cursor INTO @DesignTypeID;
END;

CLOSE design_cursor;
DEALLOCATE design_cursor;

PRINT '  ✓ Created design issue sub-types';

-- Information Issue Sub-types
DECLARE @InfoTypeID INT;
DECLARE info_cursor CURSOR FOR 
    SELECT category_id FROM IssueCategories 
    WHERE category_name = 'Information Issue' AND category_level = 2;

OPEN info_cursor;
FETCH NEXT FROM info_cursor INTO @InfoTypeID;

WHILE @@FETCH_STATUS = 0
BEGIN
    INSERT INTO IssueCategories (category_name, parent_category_id, category_level, description, display_order)
    VALUES 
        ('Missing Information', @InfoTypeID, 3, 'Required information not provided', 10),
        ('RFI', @InfoTypeID, 3, 'Request for information', 20),
        ('Clarification', @InfoTypeID, 3, 'Specification or drawing clarification needed', 30),
        ('Documentation', @InfoTypeID, 3, 'Missing or incomplete documentation', 40);
    
    FETCH NEXT FROM info_cursor INTO @InfoTypeID;
END;

CLOSE info_cursor;
DEALLOCATE info_cursor;

PRINT '  ✓ Created information issue sub-types';

-- Constructability Sub-types
DECLARE @ConstTypeID INT;
DECLARE const_cursor CURSOR FOR 
    SELECT category_id FROM IssueCategories 
    WHERE category_name = 'Constructability' AND category_level = 2;

OPEN const_cursor;
FETCH NEXT FROM const_cursor INTO @ConstTypeID;

WHILE @@FETCH_STATUS = 0
BEGIN
    INSERT INTO IssueCategories (category_name, parent_category_id, category_level, description, display_order)
    VALUES 
        ('Installation Difficulty', @ConstTypeID, 3, 'Cannot install as designed', 10),
        ('Sequencing Issue', @ConstTypeID, 3, 'Construction sequence conflicts', 20),
        ('Access Issue', @ConstTypeID, 3, 'Cannot access installation location', 30),
        ('Tolerance Issue', @ConstTypeID, 3, 'Tight tolerances difficult to achieve', 40);
    
    FETCH NEXT FROM const_cursor INTO @ConstTypeID;
END;

CLOSE const_cursor;
DEALLOCATE const_cursor;

PRINT '  ✓ Created constructability sub-types';

-- =====================================================================
-- Verification
-- =====================================================================
PRINT '';
PRINT '============================================================';
PRINT 'Category Seeding Complete - Verification:';
PRINT '============================================================';

SELECT 
    category_level,
    COUNT(*) as category_count,
    CASE category_level
        WHEN 1 THEN 'Disciplines'
        WHEN 2 THEN 'Issue Types'
        WHEN 3 THEN 'Sub-Types'
    END as level_name
FROM IssueCategories
GROUP BY category_level
ORDER BY category_level;

PRINT '';
PRINT 'Sample Hierarchy (Hydraulic/Plumbing):';
SELECT 
    REPLICATE('  ', category_level - 1) + category_name as category_hierarchy,
    category_level,
    description
FROM IssueCategories
WHERE category_id IN (
    SELECT category_id FROM IssueCategories WHERE category_name = 'Hydraulic/Plumbing'
    UNION
    SELECT category_id FROM IssueCategories WHERE parent_category_id IN (
        SELECT category_id FROM IssueCategories WHERE category_name = 'Hydraulic/Plumbing'
    )
    UNION
    SELECT ic3.category_id FROM IssueCategories ic3
    JOIN IssueCategories ic2 ON ic3.parent_category_id = ic2.category_id
    WHERE ic2.parent_category_id IN (
        SELECT category_id FROM IssueCategories WHERE category_name = 'Hydraulic/Plumbing'
    )
)
ORDER BY category_level, display_order;

PRINT '';
PRINT '============================================================';
PRINT 'Next Step: Run sql/seed_category_keywords.sql';
PRINT '============================================================';
GO
