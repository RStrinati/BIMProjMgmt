# 🗄️ SQL Server Database Integration Guide

## Overview
The Revizto Data Exporter writes all project management data directly to a **Microsoft SQL Server database**, making it perfect for business intelligence, reporting, and integration with other enterprise systems.

## 📊 Database Schema

### Core Tables Created:
1. **`tblUserLicenses`** - Revizto license and subscription information
2. **`tblLicenseMembers`** - Team members, permissions, and access levels
3. **`tblReviztoProjects`** - Project metadata, settings, and configurations  
4. **`tblReviztoProjectIssues`** - All issues, tasks, problems, and their status
5. **`tblReviztoIssueComments`** - Comments, discussions, and collaboration data

### Table Structure Benefits:
- **Normalized Data**: Efficient queries and joins between related entities
- **JSON Columns**: Complete original API data preserved for flexibility
- **GUIDs**: Consistent with Revizto's UUID system for reliable relationships
- **Timestamps**: Full audit trail of when data was created/modified

## 🚀 Quick Database Setup

### Step 1: Install SQL Server
```sql
-- Download SQL Server Express (free) or use existing SQL Server instance
-- SQL Server 2017 or later recommended
```

### Step 2: Create Database
```sql
-- Run in SQL Server Management Studio:
CREATE DATABASE ReviztoData;
```

### Step 3: Configure Connection String
```json
// In appsettings.json:
{
  "Database": {
    "ConnectionString": "Server=YOUR_SERVER\\SQLEXPRESS;Database=ReviztoData;Trusted_Connection=True;"
  }
}
```

### Step 4: Run Application
- Tables are created automatically on first run
- No manual schema setup required
- Full data synchronization happens automatically

## 💼 Business Intelligence Integration

### Power BI Integration:
```sql
-- Connect Power BI directly to SQL Server
-- Use these sample queries for dashboards:

-- Project Overview
SELECT p.name, p.region, p.created, p.ownerEmail,
       COUNT(i.issueUuid) as TotalIssues
FROM tblReviztoProjects p
LEFT JOIN tblReviztoProjectIssues i ON p.uuid = i.projectUuid
GROUP BY p.name, p.region, p.created, p.ownerEmail;

-- Issue Status Summary  
SELECT status, COUNT(*) as IssueCount,
       AVG(DATEDIFF(day, created, COALESCE(updated, GETDATE()))) as AvgDaysOpen
FROM tblReviztoProjectIssues
GROUP BY status;

-- Team Activity
SELECT m.email, l.name as LicenseName,
       COUNT(DISTINCT p.uuid) as ProjectsAccess,
       m.lastActive
FROM tblLicenseMembers m
JOIN tblUserLicenses l ON m.licenseUuid = l.uuid
JOIN tblReviztoProjects p ON p.licenseUuid = l.uuid
GROUP BY m.email, l.name, m.lastActive;
```

### Excel Integration:
1. **Data Connection**: Connect Excel to SQL Server
2. **Pivot Tables**: Create dynamic reports from issue data
3. **Charts**: Visualize project progress and team performance
4. **Refresh**: Data updates automatically from live database

### Tableau Integration:
1. **SQL Server Connector**: Direct connection to ReviztoData
2. **Live Data**: Real-time dashboards with automatic refresh
3. **Custom Visualizations**: Project timelines, issue heatmaps, team workload

## 📈 Sample Queries for Project Management

### Project Health Dashboard:
```sql
-- Get project status overview
SELECT 
    p.name AS ProjectName,
    COUNT(i.issueUuid) AS TotalIssues,
    SUM(CASE WHEN i.status = 'Open' THEN 1 ELSE 0 END) AS OpenIssues,
    SUM(CASE WHEN i.status = 'Closed' THEN 1 ELSE 0 END) AS ClosedIssues,
    CAST(SUM(CASE WHEN i.status = 'Closed' THEN 1 ELSE 0 END) * 100.0 / COUNT(i.issueUuid) AS DECIMAL(5,2)) AS CompletionRate
FROM tblReviztoProjects p
LEFT JOIN tblReviztoProjectIssues i ON p.uuid = i.projectUuid
GROUP BY p.name, p.uuid
ORDER BY CompletionRate DESC;
```

### Team Performance Analysis:
```sql
-- Analyze team member activity and issue resolution
SELECT 
    m.email AS TeamMember,
    COUNT(DISTINCT i.assignedTo) AS IssuesAssigned,
    COUNT(DISTINCT CASE WHEN i.status = 'Closed' THEN i.issueUuid END) AS IssuesResolved,
    AVG(DATEDIFF(day, i.created, i.updated)) AS AvgResolutionDays
FROM tblLicenseMembers m
JOIN tblReviztoProjectIssues i ON i.assignedTo = m.email
WHERE i.updated IS NOT NULL
GROUP BY m.email
ORDER BY IssuesResolved DESC;
```

### Issue Trend Analysis:
```sql
-- Track issue creation and resolution trends
SELECT 
    YEAR(created) AS Year,
    MONTH(created) AS Month,
    COUNT(*) AS IssuesCreated,
    COUNT(CASE WHEN status = 'Closed' THEN 1 END) AS IssuesResolved
FROM tblReviztoProjectIssues
WHERE created >= DATEADD(month, -12, GETDATE())
GROUP BY YEAR(created), MONTH(created)
ORDER BY Year, Month;
```

## 🔧 Advanced Configuration

### Connection String Options:
```json
{
  "Database": {
    // Windows Authentication (recommended)
    "ConnectionString": "Server=MYSERVER\\SQLEXPRESS;Database=ReviztoData;Trusted_Connection=True;",
    
    // SQL Server Authentication  
    "ConnectionString": "Server=MYSERVER;Database=ReviztoData;User Id=ReviztoUser;Password=SecurePassword123!;",
    
    // Azure SQL Database
    "ConnectionString": "Server=myserver.database.windows.net;Database=ReviztoData;User Id=myuser;Password=mypassword;Encrypt=True;"
  }
}
```

### Performance Optimization:
```sql
-- Create indexes for better query performance (optional)
CREATE INDEX IX_ProjectIssues_ProjectUuid ON tblReviztoProjectIssues(projectUuid);
CREATE INDEX IX_ProjectIssues_Status ON tblReviztoProjectIssues(status);  
CREATE INDEX IX_ProjectIssues_Created ON tblReviztoProjectIssues(created);
CREATE INDEX IX_LicenseMembers_Email ON tblLicenseMembers(email);
```

## 🛡️ Security & Backup

### Database Security:
- Use Windows Authentication when possible
- Create dedicated database user for application
- Limit permissions to necessary operations only
- Enable SQL Server audit logging for compliance

### Backup Strategy:
```sql
-- Regular backup script
BACKUP DATABASE ReviztoData 
TO DISK = 'C:\Backups\ReviztoData_Full.bak'
WITH FORMAT, INIT, COMPRESSION;

-- Automated maintenance plan recommended for production
```

## 📞 Database Troubleshooting

### Common Connection Issues:
1. **SQL Server not running**: Check services and start SQL Server
2. **Database doesn't exist**: Run `setup_database.sql` script  
3. **Permission denied**: Ensure user has appropriate database roles
4. **Network issues**: Check firewall and SQL Server network configuration

### Monitoring Database Growth:
```sql
-- Check database size and growth
SELECT 
    DB_NAME() as DatabaseName,
    CAST(SUM(CAST(FILEPROPERTY(name, 'SpaceUsed') AS bigint) * 8192.) / 1024 / 1024 AS DECIMAL(15,2)) AS 'Size_MB'
FROM sys.database_files 
WHERE type_desc = 'ROWS';
```

---

**Perfect for Enterprise Integration**: The SQL Server database provides a robust foundation for enterprise project management reporting, business intelligence, and integration with existing corporate systems.