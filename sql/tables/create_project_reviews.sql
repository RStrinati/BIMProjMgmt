CREATE TABLE project_reviews (
    review_id INT IDENTITY(1,1) PRIMARY KEY,
    project_id INT NOT NULL,
    cycle_id INT NOT NULL,
    scoped_reviews INT DEFAULT 0,
    completed_reviews INT DEFAULT 0,
    last_updated DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_ProjectReviews_Projects FOREIGN KEY (project_id) REFERENCES Projects(project_id)
);
GO
