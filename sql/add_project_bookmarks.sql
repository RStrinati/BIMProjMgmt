-- Add project_bookmarks table for storing bookmarks per project
CREATE TABLE project_bookmarks (
    bookmark_id INT IDENTITY(1,1) PRIMARY KEY,
    project_id INT NOT NULL,
    title NVARCHAR(255) NOT NULL,
    url NVARCHAR(1024) NOT NULL,
    description NVARCHAR(1024),
    created_at DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT FK_ProjectBookmarks_Project FOREIGN KEY (project_id)
        REFERENCES projects(project_id)
        ON DELETE CASCADE
);

-- Index for fast lookup
CREATE INDEX idx_project_bookmarks_project_id ON project_bookmarks(project_id);
