USE ProjectManagement;
GO

-- Phase 1 Database Schema Enhancements
-- Enhanced Task Management, Resource Allocation, and Milestone Tracking

-- 1. Enhance existing tasks table with new columns
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tasks') AND name = 'priority')
BEGIN
    ALTER TABLE dbo.tasks ADD
        priority VARCHAR(20) DEFAULT 'Medium',
        estimated_hours DECIMAL(5,2),
        actual_hours DECIMAL(5,2),
        predecessor_task_id INT,
        progress_percentage INT DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
        description NVARCHAR(1000),
        updated_at DATETIME DEFAULT GETDATE();
    
    -- Add foreign key constraint for predecessor tasks
    ALTER TABLE dbo.tasks ADD CONSTRAINT FK_tasks_predecessor
        FOREIGN KEY (predecessor_task_id) REFERENCES dbo.tasks(task_id);
END

-- 2. Create milestones table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'milestones' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.milestones (
        milestone_id INT IDENTITY(1,1) PRIMARY KEY,
        project_id INT NOT NULL,
        milestone_name NVARCHAR(255) NOT NULL,
        target_date DATE NOT NULL,
        actual_date DATE,
        status NVARCHAR(50) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Achieved', 'Delayed', 'Cancelled')),
        description NVARCHAR(1000),
        created_at DATETIME DEFAULT GETDATE(),
        created_by INT,
        updated_at DATETIME DEFAULT GETDATE(),
        
        CONSTRAINT FK_milestones_project FOREIGN KEY (project_id) REFERENCES dbo.projects(project_id),
        CONSTRAINT FK_milestones_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(user_id)
    );

    -- Create index for better query performance
    CREATE INDEX IX_milestones_project_target ON dbo.milestones(project_id, target_date);
END

-- 3. Enhance users table with capacity and skills information
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.users') AND name = 'hourly_rate')
BEGIN
    ALTER TABLE dbo.users ADD
        hourly_rate DECIMAL(8,2),
        weekly_capacity_hours DECIMAL(4,1) DEFAULT 40.0,
        skills NVARCHAR(500),
        role_level NVARCHAR(50) CHECK (role_level IN ('Junior', 'Mid', 'Senior', 'Lead', 'Manager')),
        department NVARCHAR(100),
        hire_date DATE,
        is_active BIT DEFAULT 1;
END

-- 4. Create task_assignments table for better resource tracking
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'task_assignments' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.task_assignments (
        assignment_id INT IDENTITY(1,1) PRIMARY KEY,
        task_id INT NOT NULL,
        user_id INT NOT NULL,
        assignment_date DATETIME DEFAULT GETDATE(),
        allocated_hours DECIMAL(5,2),
        role_in_task NVARCHAR(50), -- 'Primary', 'Support', 'Reviewer'
        is_active BIT DEFAULT 1,
        
        CONSTRAINT FK_task_assignments_task FOREIGN KEY (task_id) REFERENCES dbo.tasks(task_id),
        CONSTRAINT FK_task_assignments_user FOREIGN KEY (user_id) REFERENCES dbo.users(user_id),
        CONSTRAINT UK_task_assignments UNIQUE (task_id, user_id, is_active)
    );
END

-- 5. Create project_templates table for standardized project setup
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'project_templates' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.project_templates (
        template_id INT IDENTITY(1,1) PRIMARY KEY,
        template_name NVARCHAR(255) NOT NULL,
        project_type NVARCHAR(100), -- 'Residential', 'Commercial', 'Infrastructure'
        description NVARCHAR(1000),
        estimated_duration_days INT,
        is_active BIT DEFAULT 1,
        created_at DATETIME DEFAULT GETDATE(),
        created_by INT,
        
        CONSTRAINT FK_project_templates_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(user_id)
    );
END

-- 6. Create template_tasks table for predefined task templates
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'template_tasks' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.template_tasks (
        template_task_id INT IDENTITY(1,1) PRIMARY KEY,
        template_id INT NOT NULL,
        task_name NVARCHAR(255) NOT NULL,
        estimated_hours DECIMAL(5,2),
        priority VARCHAR(20) DEFAULT 'Medium',
        sequence_order INT,
        predecessor_sequence INT, -- Reference to sequence_order of predecessor
        required_role NVARCHAR(50),
        description NVARCHAR(1000),
        
        CONSTRAINT FK_template_tasks_template FOREIGN KEY (template_id) REFERENCES dbo.project_templates(template_id)
    );
END

-- 7. Create task_comments table for collaboration
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'task_comments' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.task_comments (
        comment_id INT IDENTITY(1,1) PRIMARY KEY,
        task_id INT NOT NULL,
        user_id INT NOT NULL,
        comment_text NVARCHAR(2000) NOT NULL,
        created_at DATETIME DEFAULT GETDATE(),
        is_internal BIT DEFAULT 1, -- Internal vs client-visible comments
        
        CONSTRAINT FK_task_comments_task FOREIGN KEY (task_id) REFERENCES dbo.tasks(task_id),
        CONSTRAINT FK_task_comments_user FOREIGN KEY (user_id) REFERENCES dbo.users(user_id)
    );

    CREATE INDEX IX_task_comments_task ON dbo.task_comments(task_id, created_at DESC);
END

-- 8. Insert default project templates
IF NOT EXISTS (SELECT 1 FROM dbo.project_templates)
BEGIN
    INSERT INTO dbo.project_templates (template_name, project_type, description, estimated_duration_days)
    VALUES
        ('Standard Residential Project', 'Residential', 'Standard residential BIM project workflow', 120),
        ('Commercial Office Building', 'Commercial', 'Commercial office building project template', 180),
        ('Infrastructure Project', 'Infrastructure', 'Roads, bridges, and infrastructure projects', 240),
        ('Renovation Project', 'Renovation', 'Building renovation and retrofit projects', 90);

    -- Get the template IDs for inserting tasks
    DECLARE @ResidentialTemplateId INT = (SELECT template_id FROM dbo.project_templates WHERE template_name = 'Standard Residential Project');
    DECLARE @CommercialTemplateId INT = (SELECT template_id FROM dbo.project_templates WHERE template_name = 'Commercial Office Building');

    -- Insert template tasks for Residential Project
    INSERT INTO dbo.template_tasks (template_id, task_name, estimated_hours, priority, sequence_order, predecessor_sequence, required_role, description)
    VALUES
        (@ResidentialTemplateId, 'Project Initiation', 8, 'High', 1, NULL, 'Manager', 'Set up project structure and team'),
        (@ResidentialTemplateId, 'Site Survey', 16, 'High', 2, 1, 'Senior', 'Conduct site measurements and documentation'),
        (@ResidentialTemplateId, 'Concept Design', 40, 'High', 3, 2, 'Lead', 'Create initial design concepts'),
        (@ResidentialTemplateId, 'Design Development', 80, 'High', 4, 3, 'Senior', 'Develop detailed design'),
        (@ResidentialTemplateId, 'BIM Model Creation', 120, 'High', 5, 4, 'Mid', 'Create detailed BIM models'),
        (@ResidentialTemplateId, 'Coordination Review', 24, 'High', 6, 5, 'Lead', 'Review model coordination and clashes'),
        (@ResidentialTemplateId, 'Construction Documentation', 60, 'Medium', 7, 6, 'Senior', 'Prepare construction drawings'),
        (@ResidentialTemplateId, 'Final Review', 16, 'High', 8, 7, 'Manager', 'Final project review and sign-off');
    
    -- Insert template tasks for Commercial Project
    INSERT INTO dbo.template_tasks (template_id, task_name, estimated_hours, priority, sequence_order, predecessor_sequence, required_role, description)
    VALUES
        (@CommercialTemplateId, 'Project Initiation', 16, 'High', 1, NULL, 'Manager', 'Set up commercial project structure'),
        (@CommercialTemplateId, 'Stakeholder Workshop', 8, 'High', 2, 1, 'Manager', 'Conduct stakeholder requirements workshop'),
        (@CommercialTemplateId, 'Site Analysis', 24, 'High', 3, 2, 'Senior', 'Comprehensive site analysis and survey'),
        (@CommercialTemplateId, 'Schematic Design', 80, 'High', 4, 3, 'Lead', 'Create schematic design options'),
        (@CommercialTemplateId, 'Design Development', 160, 'High', 5, 4, 'Senior', 'Develop detailed commercial design'),
        (@CommercialTemplateId, 'MEP Coordination', 40, 'High', 6, 5, 'Lead', 'Coordinate mechanical, electrical, plumbing'),
        (@CommercialTemplateId, 'BIM Model Development', 200, 'High', 7, 6, 'Mid', 'Create comprehensive BIM models'),
        (@CommercialTemplateId, 'Clash Detection', 32, 'High', 8, 7, 'Senior', 'Run clash detection and resolve conflicts'),
        (@CommercialTemplateId, 'Construction Documentation', 120, 'Medium', 9, 8, 'Senior', 'Prepare detailed construction drawings'),
        (@CommercialTemplateId, 'Permit Submission', 24, 'High', 10, 9, 'Lead', 'Prepare and submit permit applications'),
        (@CommercialTemplateId, 'Final Review & Handover', 32, 'High', 11, 10, 'Manager', 'Final review and project handover');
END

-- 9. Create views for enhanced reporting
CREATE OR ALTER VIEW dbo.vw_task_progress AS
SELECT
    t.task_id,
    t.task_name,
    t.project_id,
    p.project_name,
    t.assigned_to,
    u.name as assigned_user_name,
    t.start_date,
    t.end_date,
    t.priority,
    t.estimated_hours,
    t.actual_hours,
    t.progress_percentage,
    t.status,
    t.predecessor_task_id,
    pred.task_name as predecessor_task_name,
    CASE 
        WHEN t.end_date < GETDATE() AND t.progress_percentage < 100 THEN 'Overdue'
        WHEN t.end_date <= DATEADD(day, 3, GETDATE()) AND t.progress_percentage < 100 THEN 'Due Soon'
        WHEN t.progress_percentage = 100 THEN 'Complete'
        ELSE 'On Track'
    END as task_health,
    DATEDIFF(day, GETDATE(), t.end_date) as days_remaining
FROM dbo.tasks t
JOIN dbo.projects p ON t.project_id = p.project_id
LEFT JOIN dbo.users u ON t.assigned_to = u.user_id
LEFT JOIN dbo.tasks pred ON t.predecessor_task_id = pred.task_id;

CREATE OR ALTER VIEW dbo.vw_project_dashboard AS
SELECT
    p.project_id,
    p.project_name,
    p.status as project_status,
    p.priority as project_priority,
    p.start_date,
    p.end_date,
    COUNT(t.task_id) as total_tasks,
    COUNT(CASE WHEN t.status = 'Complete' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.end_date < GETDATE() AND t.progress_percentage < 100 THEN 1 END) as overdue_tasks,
    AVG(CAST(t.progress_percentage as FLOAT)) as avg_progress,
    SUM(t.estimated_hours) as total_estimated_hours,
    SUM(t.actual_hours) as total_actual_hours,
    COUNT(m.milestone_id) as total_milestones,
    COUNT(CASE WHEN m.status = 'Achieved' THEN 1 END) as achieved_milestones,
    COUNT(CASE WHEN m.target_date < GETDATE() AND m.status != 'Achieved' THEN 1 END) as overdue_milestones
FROM dbo.projects p
LEFT JOIN dbo.tasks t ON p.project_id = t.project_id
LEFT JOIN dbo.milestones m ON p.project_id = m.project_id
GROUP BY p.project_id, p.project_name, p.status, p.priority, p.start_date, p.end_date;

CREATE OR ALTER VIEW dbo.vw_resource_utilization AS
SELECT
    u.user_id,
    u.name,
    u.role_level,
    u.weekly_capacity_hours,
    u.department,
    COUNT(ta.assignment_id) as active_assignments,
    SUM(ta.allocated_hours) as allocated_hours_week,
    CASE 
        WHEN u.weekly_capacity_hours > 0 THEN 
            (SUM(ta.allocated_hours) / u.weekly_capacity_hours) * 100 
        ELSE 0 
    END as utilization_percentage,
    CASE 
        WHEN SUM(ta.allocated_hours) > u.weekly_capacity_hours THEN 'Overallocated'
        WHEN SUM(ta.allocated_hours) > (u.weekly_capacity_hours * 0.8) THEN 'High'
        WHEN SUM(ta.allocated_hours) > (u.weekly_capacity_hours * 0.5) THEN 'Medium'
        ELSE 'Low'
    END as workload_status
FROM dbo.users u
LEFT JOIN dbo.task_assignments ta ON u.user_id = ta.user_id AND ta.is_active = 1
LEFT JOIN dbo.tasks t ON ta.task_id = t.task_id AND t.status NOT IN ('Complete', 'Cancelled')
WHERE u.is_active = 1
GROUP BY u.user_id, u.name, u.role_level, u.weekly_capacity_hours, u.department;

-- 10. Create stored procedures for common operations
CREATE OR ALTER PROCEDURE dbo.sp_CreateProjectFromTemplate
    @ProjectName NVARCHAR(255),
    @TemplateId INT,
    @ProjectStartDate DATE,
    @CreatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @NewProjectId INT;
    
    BEGIN TRANSACTION;
    
    TRY
        -- Create the new project
        INSERT INTO dbo.projects (project_name, start_date, status, priority, created_at)
        VALUES (@ProjectName, @ProjectStartDate, 'Planning', 'Medium', GETDATE());

        SET @NewProjectId = SCOPE_IDENTITY();

        -- Create tasks from template
        INSERT INTO dbo.tasks (
            task_name, project_id, start_date, end_date, estimated_hours,
            priority, description, status, created_at
        )
        SELECT
            tt.task_name,
            @NewProjectId,
            DATEADD(day, (tt.sequence_order - 1) * 7, @ProjectStartDate), -- Rough scheduling
            DATEADD(day, (tt.sequence_order - 1) * 7 + CEILING(tt.estimated_hours / 8.0), @ProjectStartDate),
            tt.estimated_hours,
            tt.priority,
            tt.description,
            'Not Started',
            GETDATE()
        FROM dbo.template_tasks tt
        WHERE tt.template_id = @TemplateId
        ORDER BY tt.sequence_order;

        -- Update task dependencies
        UPDATE t
        SET predecessor_task_id = pred.task_id
        FROM dbo.tasks t
        JOIN dbo.template_tasks tt ON t.task_name = tt.task_name
        JOIN dbo.template_tasks pred_tt ON tt.predecessor_sequence = pred_tt.sequence_order
            AND tt.template_id = pred_tt.template_id
        JOIN dbo.tasks pred ON pred.task_name = pred_tt.task_name AND pred.project_id = @NewProjectId
        WHERE t.project_id = @NewProjectId AND tt.template_id = @TemplateId;
        
        COMMIT TRANSACTION;
        
        SELECT @NewProjectId as NewProjectId, 'Project created successfully' as Message;
        
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;

PRINT 'Phase 1 database enhancements completed successfully!';
