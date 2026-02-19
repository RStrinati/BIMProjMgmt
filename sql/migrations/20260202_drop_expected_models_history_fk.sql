-- Drop FK from ExpectedModelsHistory -> ExpectedModels to allow deletes while retaining audit history
USE ProjectManagement;
GO

DECLARE @fk_name NVARCHAR(255);

SELECT TOP 1 @fk_name = fk.name
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
JOIN sys.tables t_parent ON fk.parent_object_id = t_parent.object_id
JOIN sys.tables t_ref ON fk.referenced_object_id = t_ref.object_id
WHERE t_parent.name = 'ExpectedModelsHistory'
  AND t_ref.name = 'ExpectedModels';

IF @fk_name IS NOT NULL
BEGIN
    EXEC('ALTER TABLE dbo.ExpectedModelsHistory DROP CONSTRAINT [' + @fk_name + ']');
    PRINT 'Dropped FK ' + @fk_name + ' from ExpectedModelsHistory';
END
ELSE
BEGIN
    PRINT 'No FK found from ExpectedModelsHistory to ExpectedModels';
END
GO
