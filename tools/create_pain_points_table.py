"""
Create missing IssuePainPoints table
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db

conn = connect_to_db('ProjectManagement')
if not conn:
    print("❌ Database connection failed")
    exit(1)

try:
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'IssuePainPoints'
    """)
    
    exists = cursor.fetchone()[0] > 0
    
    if exists:
        print("✓ IssuePainPoints table already exists")
    else:
        # Create table
        cursor.execute("""
            CREATE TABLE IssuePainPoints (
                pain_point_id INT IDENTITY(1,1) PRIMARY KEY,
                client_id INT NULL,
                project_type_id INT NULL,
                category_id INT NOT NULL,
                period_start DATE NOT NULL,
                period_end DATE NOT NULL,
                total_issues INT NOT NULL DEFAULT 0,
                open_issues INT NOT NULL DEFAULT 0,
                closed_issues INT NOT NULL DEFAULT 0,
                avg_resolution_days DECIMAL(6,2),
                median_resolution_days INT,
                max_resolution_days INT,
                critical_count INT DEFAULT 0,
                high_priority_count INT DEFAULT 0,
                recurring_issue_count INT DEFAULT 0,
                issues_this_period INT DEFAULT 0,
                issues_prev_period INT DEFAULT 0,
                trend_direction NVARCHAR(20),
                common_keywords NVARCHAR(MAX),
                sample_issue_ids NVARCHAR(MAX),
                calculated_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (client_id) REFERENCES clients(client_id),
                FOREIGN KEY (category_id) REFERENCES IssueCategories(category_id),
                CONSTRAINT chk_period_dates CHECK (period_end >= period_start)
            )
        """)
        
        conn.commit()
        print("✓ IssuePainPoints table created successfully")
    
except Exception as e:
    print(f"❌ Error: {e}")

finally:
    conn.close()
