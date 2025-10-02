-- =====================================================================
-- Issue Analytics System - Category Keywords Seed Data
-- Populates IssueCategoryKeywords for automated categorization
-- =====================================================================

USE ProjectManagement;
GO

PRINT 'Seeding Category Keywords...';
PRINT '';

-- =====================================================================
-- DISCIPLINE KEYWORDS (Level 1)
-- =====================================================================
PRINT 'Creating Discipline Keywords...';

-- Structural
INSERT INTO IssueCategoryKeywords (category_id, keyword, weight)
SELECT category_id, keyword, weight FROM (
    SELECT (SELECT category_id FROM IssueCategories WHERE category_name = 'Structural' AND category_level = 1) as category_id,
    keyword, weight FROM (VALUES
        ('structural', 1.0),
        ('structure', 0.95),
        ('steel', 0.90),
        ('concrete', 0.90),
        ('column', 0.85),
        ('beam', 0.85),
        ('slab', 0.85),
        ('foundation', 0.85),
        ('reinforcement', 0.80),
        ('rebar', 0.80),
        ('footing', 0.80),
        ('load bearing', 0.85),
        ('str', 0.75)
    ) AS Keywords(keyword, weight)
) AS StructuralKeywords;

-- Architectural  
INSERT INTO IssueCategoryKeywords (category_id, keyword, weight)
SELECT category_id, keyword, weight FROM (
    SELECT (SELECT category_id FROM IssueCategories WHERE category_name = 'Architectural' AND category_level = 1) as category_id,
    keyword, weight FROM (VALUES
        ('architectural', 1.0),
        ('architecture', 0.95),
        ('façade', 0.90),
        ('facade', 0.90),
        ('cladding', 0.90),
        ('interior', 0.85),
        ('finish', 0.80),
        ('wall', 0.75),
        ('door', 0.75),
        ('window', 0.75),
        ('ceiling', 0.75),
        ('partition', 0.80),
        ('arch', 0.70)
    ) AS Keywords(keyword, weight)
) AS ArchKeywords;

-- Mechanical (HVAC)
INSERT INTO IssueCategoryKeywords (category_id, keyword, weight)
SELECT category_id, keyword, weight FROM (
    SELECT (SELECT category_id FROM IssueCategories WHERE category_name = 'Mechanical (HVAC)' AND category_level = 1) as category_id,
    keyword, weight FROM (VALUES
        ('mechanical', 1.0),
        ('hvac', 1.0),
        ('ductwork', 0.95),
        ('duct', 0.90),
        ('ventilation', 0.90),
        ('ahu', 0.95),
        ('air handling', 0.95),
        ('chiller', 0.90),
        ('cooling', 0.80),
        ('heating', 0.80),
        ('exhaust', 0.85),
        ('supply air', 0.85),
        ('return air', 0.85),
        ('mech', 0.75)
    ) AS Keywords(keyword, weight)
) AS MechKeywords;

-- Electrical
INSERT INTO IssueCategoryKeywords (category_id, keyword, weight)
SELECT category_id, keyword, weight FROM (
    SELECT (SELECT category_id FROM IssueCategories WHERE category_name = 'Electrical' AND category_level = 1) as category_id,
    keyword, weight FROM (VALUES
        ('electrical', 1.0),
        ('electric', 0.95),
        ('power', 0.90),
        ('lighting', 0.90),
        ('cable', 0.85),
        ('conduit', 0.90),
        ('switchboard', 0.95),
        ('distribution', 0.80),
        ('socket', 0.80),
        ('outlet', 0.80),
        ('transformer', 0.85),
        ('panel', 0.75),
        ('ele', 0.70),
        ('elec', 0.75),
        ('low voltage', 0.85),
        ('cable tray', 0.90)
    ) AS Keywords(keyword, weight)
) AS ElecKeywords;

-- Hydraulic/Plumbing
INSERT INTO IssueCategoryKeywords (category_id, keyword, weight)
SELECT category_id, keyword, weight FROM (
    SELECT (SELECT category_id FROM IssueCategories WHERE category_name = 'Hydraulic/Plumbing' AND category_level = 1) as category_id,
    keyword, weight FROM (VALUES
        ('hydraulic', 1.0),
        ('plumbing', 1.0),
        ('pipework', 0.95),
        ('pipe', 0.85),
        ('drainage', 0.95),
        ('water', 0.85),
        ('sanitary', 0.90),
        ('sewer', 0.90),
        ('waste', 0.85),
        ('pump', 0.80),
        ('valve', 0.75),
        ('hyd', 0.75),
        ('drain', 0.85),
        ('gas', 0.80),
        ('hot water', 0.85),
        ('cold water', 0.85)
    ) AS Keywords(keyword, weight)
) AS HydKeywords;

-- Fire Protection
INSERT INTO IssueCategoryKeywords (category_id, keyword, weight)
SELECT category_id, keyword, weight FROM (
    SELECT (SELECT category_id FROM IssueCategories WHERE category_name = 'Fire Protection' AND category_level = 1) as category_id,
    keyword, weight FROM (VALUES
        ('fire protection', 1.0),
        ('fire', 0.90),
        ('sprinkler', 0.95),
        ('hydrant', 0.95),
        ('fire hose', 0.95),
        ('fire alarm', 0.95),
        ('smoke detector', 0.90),
        ('fire suppression', 0.95),
        ('fire rated', 0.85),
        ('fire safety', 0.90),
        ('fire exit', 0.85)
    ) AS Keywords(keyword, weight)
) AS FireKeywords;

-- Civil
INSERT INTO IssueCategoryKeywords (category_id, keyword, weight)
SELECT category_id, keyword, weight FROM (
    SELECT (SELECT category_id FROM IssueCategories WHERE category_name = 'Civil' AND category_level = 1) as category_id,
    keyword, weight FROM (VALUES
        ('civil', 1.0),
        ('siteworks', 0.95),
        ('earthworks', 0.95),
        ('excavation', 0.90),
        ('external drainage', 0.95),
        ('stormwater', 0.90),
        ('pavement', 0.85),
        ('retaining wall', 0.90),
        ('site', 0.70),
        ('grading', 0.85),
        ('survey', 0.75)
    ) AS Keywords(keyword, weight)
) AS CivilKeywords;

PRINT '  ✓ Created discipline keywords';

-- =====================================================================
-- ISSUE TYPE KEYWORDS (Level 2)
-- =====================================================================
PRINT 'Creating Issue Type Keywords...';

-- Clash/Coordination
DECLARE @ClashID INT;
DECLARE clash_cat_cursor CURSOR FOR
    SELECT category_id FROM IssueCategories 
    WHERE category_name = 'Clash/Coordination' AND category_level = 2;

OPEN clash_cat_cursor;
FETCH NEXT FROM clash_cat_cursor INTO @ClashID;

WHILE @@FETCH_STATUS = 0
BEGIN
    INSERT INTO IssueCategoryKeywords (category_id, keyword, weight) VALUES
        (@ClashID, 'clash', 0.95),
        (@ClashID, 'conflict', 0.90),
        (@ClashID, 'overlap', 0.90),
        (@ClashID, 'interference', 0.85),
        (@ClashID, 'coordination', 0.85),
        (@ClashID, 'clashing', 0.90),
        (@ClashID, 'clearance', 0.85),
        (@ClashID, 'space', 0.70);
    
    FETCH NEXT FROM clash_cat_cursor INTO @ClashID;
END;

CLOSE clash_cat_cursor;
DEALLOCATE clash_cat_cursor;

-- Design Issue
DECLARE @DesignID INT;
DECLARE design_cat_cursor CURSOR FOR
    SELECT category_id FROM IssueCategories 
    WHERE category_name = 'Design Issue' AND category_level = 2;

OPEN design_cat_cursor;
FETCH NEXT FROM design_cat_cursor INTO @DesignID;

WHILE @@FETCH_STATUS = 0
BEGIN
    INSERT INTO IssueCategoryKeywords (category_id, keyword, weight) VALUES
        (@DesignID, 'design', 0.90),
        (@DesignID, 'error', 0.85),
        (@DesignID, 'incorrect', 0.85),
        (@DesignID, 'mistake', 0.85),
        (@DesignID, 'wrong', 0.80),
        (@DesignID, 'incomplete', 0.85),
        (@DesignID, 'missing', 0.80),
        (@DesignID, 'change', 0.75),
        (@DesignID, 'revision', 0.75),
        (@DesignID, 'redesign', 0.85);
    
    FETCH NEXT FROM design_cat_cursor INTO @DesignID;
END;

CLOSE design_cat_cursor;
DEALLOCATE design_cat_cursor;

-- Information Issue
DECLARE @InfoID INT;
DECLARE info_cat_cursor CURSOR FOR
    SELECT category_id FROM IssueCategories 
    WHERE category_name = 'Information Issue' AND category_level = 2;

OPEN info_cat_cursor;
FETCH NEXT FROM info_cat_cursor INTO @InfoID;

WHILE @@FETCH_STATUS = 0
BEGIN
    INSERT INTO IssueCategoryKeywords (category_id, keyword, weight) VALUES
        (@InfoID, 'rfi', 0.95),
        (@InfoID, 'request for information', 0.95),
        (@InfoID, 'missing information', 0.90),
        (@InfoID, 'clarification', 0.90),
        (@InfoID, 'clarify', 0.85),
        (@InfoID, 'unclear', 0.85),
        (@InfoID, 'confirm', 0.75),
        (@InfoID, 'specification', 0.75),
        (@InfoID, 'detail', 0.70);
    
    FETCH NEXT FROM info_cat_cursor INTO @InfoID;
END;

CLOSE info_cat_cursor;
DEALLOCATE info_cat_cursor;

-- Code Compliance
DECLARE @CodeID INT;
DECLARE code_cat_cursor CURSOR FOR
    SELECT category_id FROM IssueCategories 
    WHERE category_name = 'Code Compliance' AND category_level = 2;

OPEN code_cat_cursor;
FETCH NEXT FROM code_cat_cursor INTO @CodeID;

WHILE @@FETCH_STATUS = 0
BEGIN
    INSERT INTO IssueCategoryKeywords (category_id, keyword, weight) VALUES
        (@CodeID, 'code', 0.90),
        (@CodeID, 'compliance', 0.90),
        (@CodeID, 'standard', 0.85),
        (@CodeID, 'regulation', 0.90),
        (@CodeID, 'non-compliant', 0.95),
        (@CodeID, 'violation', 0.90),
        (@CodeID, 'requirement', 0.75),
        (@CodeID, 'bca', 0.95),
        (@CodeID, 'as/nzs', 0.90),
        (@CodeID, 'authority', 0.80);
    
    FETCH NEXT FROM code_cat_cursor INTO @CodeID;
END;

CLOSE code_cat_cursor;
DEALLOCATE code_cat_cursor;

-- Constructability
DECLARE @ConstID INT;
DECLARE const_cat_cursor CURSOR FOR
    SELECT category_id FROM IssueCategories 
    WHERE category_name = 'Constructability' AND category_level = 2;

OPEN const_cat_cursor;
FETCH NEXT FROM const_cat_cursor INTO @ConstID;

WHILE @@FETCH_STATUS = 0
BEGIN
    INSERT INTO IssueCategoryKeywords (category_id, keyword, weight) VALUES
        (@ConstID, 'constructability', 0.95),
        (@ConstID, 'cannot build', 0.95),
        (@ConstID, 'cannot install', 0.95),
        (@ConstID, 'installation', 0.80),
        (@ConstID, 'access', 0.80),
        (@ConstID, 'difficult', 0.75),
        (@ConstID, 'impossible', 0.90),
        (@ConstID, 'sequence', 0.80),
        (@ConstID, 'tolerance', 0.80);
    
    FETCH NEXT FROM const_cat_cursor INTO @ConstID;
END;

CLOSE const_cat_cursor;
DEALLOCATE const_cat_cursor;

-- Quality Issue
DECLARE @QualityID INT;
DECLARE quality_cat_cursor CURSOR FOR
    SELECT category_id FROM IssueCategories 
    WHERE category_name = 'Quality Issue' AND category_level = 2;

OPEN quality_cat_cursor;
FETCH NEXT FROM quality_cat_cursor INTO @QualityID;

WHILE @@FETCH_STATUS = 0
BEGIN
    INSERT INTO IssueCategoryKeywords (category_id, keyword, weight) VALUES
        (@QualityID, 'quality', 0.90),
        (@QualityID, 'defect', 0.90),
        (@QualityID, 'workmanship', 0.90),
        (@QualityID, 'poor quality', 0.95),
        (@QualityID, 'material', 0.75),
        (@QualityID, 'damage', 0.80),
        (@QualityID, 'inspection', 0.75),
        (@QualityID, 'failed', 0.80);
    
    FETCH NEXT FROM quality_cat_cursor INTO @QualityID;
END;

CLOSE quality_cat_cursor;
DEALLOCATE quality_cat_cursor;

PRINT '  ✓ Created issue type keywords';

-- =====================================================================
-- SUB-TYPE KEYWORDS (Level 3)
-- =====================================================================
PRINT 'Creating Sub-Type Keywords...';

-- Clearance Issue
DECLARE @ClearanceID INT;
DECLARE clearance_cursor CURSOR FOR
    SELECT category_id FROM IssueCategories 
    WHERE category_name = 'Clearance Issue' AND category_level = 3;

OPEN clearance_cursor;
FETCH NEXT FROM clearance_cursor INTO @ClearanceID;

WHILE @@FETCH_STATUS = 0
BEGIN
    INSERT INTO IssueCategoryKeywords (category_id, keyword, weight) VALUES
        (@ClearanceID, 'clearance', 0.95),
        (@ClearanceID, '<300mm', 1.0),
        (@ClearanceID, '< 300mm', 1.0),
        (@ClearanceID, 'insufficient space', 0.90),
        (@ClearanceID, 'too close', 0.90),
        (@ClearanceID, 'tight', 0.80),
        (@ClearanceID, 'minimum clearance', 0.95);
    
    FETCH NEXT FROM clearance_cursor INTO @ClearanceID;
END;

CLOSE clearance_cursor;
DEALLOCATE clearance_cursor;

-- Penetration Conflict
DECLARE @PenoID INT;
DECLARE peno_cursor CURSOR FOR
    SELECT category_id FROM IssueCategories 
    WHERE category_name = 'Penetration Conflict' AND category_level = 3;

OPEN peno_cursor;
FETCH NEXT FROM peno_cursor INTO @PenoID;

WHILE @@FETCH_STATUS = 0
BEGIN
    INSERT INTO IssueCategoryKeywords (category_id, keyword, weight) VALUES
        (@PenoID, 'peno', 0.95),
        (@PenoID, 'penetration', 0.95),
        (@PenoID, 'core', 0.80),
        (@PenoID, 'hole', 0.75),
        (@PenoID, 'sleeve', 0.85),
        (@PenoID, 'pass-through', 0.85),
        (@PenoID, 'opening', 0.70),
        (@PenoID, 'misalignment', 0.85);
    
    FETCH NEXT FROM peno_cursor INTO @PenoID;
END;

CLOSE peno_cursor;
DEALLOCATE peno_cursor;

PRINT '  ✓ Created sub-type keywords';

-- =====================================================================
-- URGENCY & PRIORITY KEYWORDS (for scoring)
-- =====================================================================
PRINT 'Adding urgency/priority keywords...';

-- Note: These are used for urgency scoring, not categorization
-- Will be referenced in the text processing service

PRINT '  ✓ Urgency keywords will be handled in text processing service';

-- =====================================================================
-- Verification
-- =====================================================================
PRINT '';
PRINT '============================================================';
PRINT 'Keyword Seeding Complete - Verification:';
PRINT '============================================================';

SELECT 
    ic.category_level,
    ic.category_name,
    COUNT(ick.keyword_id) as keyword_count,
    AVG(ick.weight) as avg_weight
FROM IssueCategories ic
LEFT JOIN IssueCategoryKeywords ick ON ic.category_id = ick.category_id
WHERE ic.is_active = 1 AND (ick.is_active = 1 OR ick.is_active IS NULL)
GROUP BY ic.category_level, ic.category_name, ic.display_order
HAVING COUNT(ick.keyword_id) > 0
ORDER BY ic.category_level, ic.display_order;

PRINT '';
PRINT 'Total Keywords: ';
SELECT COUNT(*) as total_keywords FROM IssueCategoryKeywords WHERE is_active = 1;

PRINT '';
PRINT 'Sample Keywords for Hydraulic/Plumbing:';
SELECT 
    ic.category_name,
    ick.keyword,
    ick.weight
FROM IssueCategoryKeywords ick
JOIN IssueCategories ic ON ick.category_id = ic.category_id
WHERE ic.category_name = 'Hydraulic/Plumbing' AND ic.category_level = 1
ORDER BY ick.weight DESC;

PRINT '';
PRINT '============================================================';
PRINT 'Next Step: Run services/issue_text_processor.py';
PRINT '============================================================';
GO
