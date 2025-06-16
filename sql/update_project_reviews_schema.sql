IF NOT EXISTS (SELECT * FROM sys.columns WHERE Name = 'scoped_reviews' AND Object_ID = OBJECT_ID('project_reviews'))
    ALTER TABLE project_reviews ADD scoped_reviews INT DEFAULT 0;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE Name = 'completed_reviews' AND Object_ID = OBJECT_ID('project_reviews'))
    ALTER TABLE project_reviews ADD completed_reviews INT DEFAULT 0;
GO
IF NOT EXISTS (SELECT * FROM sys.columns WHERE Name = 'last_updated' AND Object_ID = OBJECT_ID('project_reviews'))
    ALTER TABLE project_reviews ADD last_updated DATETIME NULL;
GO
