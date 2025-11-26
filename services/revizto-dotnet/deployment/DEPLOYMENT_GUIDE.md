# Revizto Data Exporter - Deployment Guide

## 📦 Executable Package Contents

This deployment package contains everything needed to run the Revizto Data Exporter as a standalone application:

### Core Files:
- **`ReviztoDataExporter.exe`** - Main executable (no .NET runtime required)
- **`appsettings.json`** - Configuration file for API credentials
- **`sni.dll`** - SQL Server native client library
- **`SQLite.Interop.dll`** - SQLite database interface

### Documentation:
- **`DEPLOYMENT_GUIDE.md`** - This file
- **`TOKEN_MANAGEMENT.md`** - Token management and troubleshooting
- **`README_CLI.md`** - Command-line interface documentation

## 🚀 Installation Instructions

### Step 1: Extract Files
1. Create a folder on your target machine (e.g., `C:\ReviztoExporter`)
2. Copy all files from this deployment package to that folder
3. Ensure the folder is writable (for logs and database files)

### Step 2: Configure API Access
1. Open `appsettings.json` in a text editor
2. Replace the placeholder values with your Revizto credentials:

```json
{
  "ReviztoAPI": {
    "AccessToken": "your-access-token-here",
    "RefreshToken": "your-refresh-token-here", 
    "BaseUrl": "https://app.revizto.com/api",
    "ApiKey": "your-api-key-here"
  },
  "DatabasePath": "ReviztoData.db"
}
```

### Step 3: Get Initial Tokens (First Time Only)
If you don't have tokens yet, run the executable once to trigger the authentication flow:
1. Double-click `ReviztoDataExporter.exe` or run from command line
2. When prompted, enter your Revizto API key
3. The system will automatically obtain and save your tokens

## 🖥️ Running the Application

### GUI Mode (Default):
```cmd
ReviztoDataExporter.exe
```
- Opens Windows Forms interface
- Interactive project selection
- Real-time progress updates

### Command Line Mode:
```cmd
ReviztoDataExporter.exe --console
```
- Runs in console mode
- Exports all projects automatically
- Suitable for scheduled tasks

### Export Specific Project:
```cmd
ReviztoDataExporter.exe --console --project "project-uuid-here"
```

## 🗄️ SQL Server Database & Export Files

### Database Configuration:
- **Type**: Microsoft SQL Server (not SQLite)
- **Database Name**: `ReviztoData` (configurable)
- **Connection**: Uses Windows Authentication by default
- **Tables Created**: 
  - `tblUserLicenses` - License information and metadata
  - `tblLicenseMembers` - Team members for each license
  - `tblReviztoProjects` - Project details and metadata  
  - `tblReviztoProjectIssues` - All issues/tasks from projects
  - `tblReviztoIssueComments` - Comments and discussions on issues

### SQL Server Setup Required:
1. **Install SQL Server** (Express edition is sufficient)
2. **Create Database**: `CREATE DATABASE ReviztoData`
3. **Configure Connection String** in `appsettings.json`:
   ```json
   "Database": {
     "ConnectionString": "Server=YOUR_SERVER;Database=ReviztoData;Trusted_Connection=True;"
   }
   ```

### Database Schema:
The application automatically creates and manages all tables. Each table includes:
- **Structured Data**: Normalized columns for efficient querying
- **JSON Columns**: Complete original API responses for flexibility
- **GUIDs**: Consistent with Revizto's UUID system
- **Timestamps**: Creation and modification tracking

### Export Files:
- **Location**: `Exports\` folder (created automatically)
- **Format**: JSON files with timestamp
- **Naming**: `Issues_{ProjectUUID}_{DateTime}.json`

### Log Files:
- **Location**: `logs\` folder (created automatically)
- **Current**: `log.txt` - Today's log
- **Historical**: `logYYYYMMDD.txt` - Previous days

## ⚙️ System Requirements

### Minimum Requirements:
- **OS**: Windows 10 or Windows Server 2016
- **Architecture**: x64 (64-bit)
- **Memory**: 512 MB RAM
- **Disk**: 100 MB free space (more for large datasets)
- **Network**: Internet access to Revizto API
- **Database**: SQL Server (Express, Standard, or Enterprise)

### Recommended:
- **Memory**: 2 GB RAM (for large projects)
- **Disk**: 1 GB free space
- **Network**: Stable broadband connection
- **Database**: SQL Server with sufficient storage for project data

## 🔧 Configuration Options

### appsettings.json Parameters:

```json
{
  "ReviztoAPI": {
    "AccessToken": "JWT access token",
    "RefreshToken": "JWT refresh token", 
    "BaseUrl": "https://app.revizto.com/api",
    "ApiKey": "Your Revizto API key"
  },
  "Database": {
    "ConnectionString": "Server=YOUR_SQL_SERVER;Database=ReviztoData;Trusted_Connection=True;"
  },
  "ExportSettings": {
    "OutputDirectory": "Exports",
    "LogDirectory": "logs"
  },
  "Serilog": {
    "MinimumLevel": "Information",
    "WriteTo": [
      {
        "Name": "Console"
      },
      {
        "Name": "File",
        "Args": {
          "path": "logs/log.txt",
          "rollingInterval": "Day"
        }
      }
    ]
  }
}
```

## 📋 Usage Scenarios

### 1. Project Management Dashboard
- Run regularly to sync Revizto data
- Import SQLite database into BI tools
- Create dashboards from exported JSON

### 2. Scheduled Data Sync
- Create Windows Task Scheduler job
- Run in console mode with specific projects
- Automate data pipeline integration

### 3. One-Time Data Migration
- Export all historical data
- Process JSON files with custom tools
- Migrate to other project management systems

## 🛠️ Troubleshooting

### Common Issues:

#### Database Connection Errors:
- Verify SQL Server is running and accessible
- Check connection string format and server name
- Ensure database `ReviztoData` exists
- Verify Windows Authentication or provide SQL credentials
- Check firewall settings for SQL Server port (1433)

#### Table Creation Failures:
- Ensure application has CREATE TABLE permissions
- Verify database user has db_ddladmin role
- Check SQL Server error logs for detailed messages
- Confirm sufficient disk space on SQL Server

#### Data Import Issues:
- Monitor SQL Server for deadlocks or timeouts
- Check transaction log space availability
- Verify network stability during large imports
- Review application logs for specific SQL errors

#### "Access Denied" Errors:
- Ensure folder is writable
- Run as Administrator if needed
- Check antivirus software blocking

#### Token Refresh Failures:
- Check internet connectivity
- Verify API key is still valid
- Review `TOKEN_MANAGEMENT.md` for details

#### Database Errors:
- Ensure SQLite.Interop.dll is present
- Check disk space availability
- Verify write permissions on folder

#### Network Timeouts:
- Check firewall settings
- Verify Revizto API endpoint accessibility
- Consider proxy configuration if needed

### Getting Help:
1. Check log files in `logs\` folder
2. Review error messages carefully
3. Consult `TOKEN_MANAGEMENT.md` for auth issues
4. Verify all deployment files are present

## 🔄 Updates & Maintenance

### Token Maintenance:
- Access tokens refresh automatically
- Monitor logs for refresh activities
- Re-authenticate if refresh tokens expire

### Application Updates:
- Replace `ReviztoDataExporter.exe` with new version
- Keep existing `appsettings.json` and database files
- Review release notes for configuration changes

### Database Maintenance:
- SQLite database grows with data
- Consider periodic cleanup of old records
- Backup database files regularly

## 📞 Support Information

### Log Analysis:
- Logs use structured format with timestamps
- Key events: authentication, API calls, database operations
- Error levels: Information, Warning, Error

### Performance Monitoring:
- API call timing logged for each request
- Database operation performance tracked
- Memory usage typically under 100MB

### Security Considerations:
- Keep `appsettings.json` secure (contains tokens)
- Limit file system permissions appropriately
- Rotate API keys periodically per organization policy

---

**Version**: 1.0  
**Build Date**: September 29, 2025  
**Target Framework**: .NET 9.0  
**Architecture**: Windows x64