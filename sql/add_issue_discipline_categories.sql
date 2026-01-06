USE ProjectManagement;
GO

IF NOT EXISTS (
    SELECT 1
    FROM dbo.IssueCategories
    WHERE category_name = 'BIM Manager' AND category_level = 1
)
BEGIN
    INSERT INTO dbo.IssueCategories (category_name, parent_category_id, category_level, description, display_order)
    VALUES ('BIM Manager', NULL, 1, 'BIM management and coordination roles', 95);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM dbo.IssueCategories
    WHERE category_name = 'Landscape' AND category_level = 1
)
BEGIN
    INSERT INTO dbo.IssueCategories (category_name, parent_category_id, category_level, description, display_order)
    VALUES ('Landscape', NULL, 1, 'Landscape and external works discipline', 96);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM dbo.IssueCategories
    WHERE category_name = 'Project Manager 00' AND category_level = 1
)
BEGIN
    INSERT INTO dbo.IssueCategories (category_name, parent_category_id, category_level, description, display_order)
    VALUES ('Project Manager 00', NULL, 1, 'Project management role (raw discipline)', 97);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM dbo.IssueCategories
    WHERE category_name = 'Framing Contractor 00' AND category_level = 1
)
BEGIN
    INSERT INTO dbo.IssueCategories (category_name, parent_category_id, category_level, description, display_order)
    VALUES ('Framing Contractor 00', NULL, 1, 'Framing contractor role (raw discipline)', 98);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM dbo.IssueCategories
    WHERE category_name = 'Steelwork Contractor 00' AND category_level = 1
)
BEGIN
    INSERT INTO dbo.IssueCategories (category_name, parent_category_id, category_level, description, display_order)
    VALUES ('Steelwork Contractor 00', NULL, 1, 'Steelwork contractor role (raw discipline)', 99);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM dbo.IssueCategories
    WHERE category_name = 'Fuel System Contractor 00' AND category_level = 1
)
BEGIN
    INSERT INTO dbo.IssueCategories (category_name, parent_category_id, category_level, description, display_order)
    VALUES ('Fuel System Contractor 00', NULL, 1, 'Fuel system contractor role (raw discipline)', 100);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM dbo.IssueCategories
    WHERE category_name = 'Ceiling Contractor 00' AND category_level = 1
)
BEGIN
    INSERT INTO dbo.IssueCategories (category_name, parent_category_id, category_level, description, display_order)
    VALUES ('Ceiling Contractor 00', NULL, 1, 'Ceiling contractor role (raw discipline)', 101);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM dbo.IssueCategories
    WHERE category_name = 'Main Contractor' AND category_level = 1
)
BEGIN
    INSERT INTO dbo.IssueCategories (category_name, parent_category_id, category_level, description, display_order)
    VALUES ('Main Contractor', NULL, 1, 'Main contractor role (raw discipline)', 102);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM dbo.IssueCategories
    WHERE category_name = 'Hot Aisle Containment Contractor 00' AND category_level = 1
)
BEGIN
    INSERT INTO dbo.IssueCategories (category_name, parent_category_id, category_level, description, display_order)
    VALUES ('Hot Aisle Containment Contractor 00', NULL, 1, 'Hot aisle containment contractor role (raw discipline)', 103);
END
GO
