# 📦 Revizto Data Exporter - Standalone Executable

## Quick Start

### 🚀 For Immediate Use:
1. **Configure API Access**: Edit `appsettings.json` with your Revizto credentials
2. **Run**: Double-click `start.bat` or run `ReviztoDataExporter.exe`
3. **Choose Mode**: GUI (interactive) or Console (automated)

### ⚡ Fast Setup:
```cmd
# Edit configuration
notepad appsettings.json

# Start with menu
start.bat

# Or run directly in GUI mode
ReviztoDataExporter.exe

# Or run in console mode (export all projects)  
ReviztoDataExporter.exe refresh
ReviztoDataExporter.exe export-all
```

## 📋 What's Included

### ✅ Core Application:
- **`ReviztoDataExporter.exe`** - Main application (39MB, no dependencies)
- **`appsettings.json`** - Configuration file (edit with your API credentials)
- **`sni.dll`** & **`SQLite.Interop.dll`** - Database support libraries

### 🎯 Easy Launchers:
- **`start.bat`** - Simple menu-driven launcher
- **`start.ps1`** - Advanced PowerShell launcher with status checking

### 📖 Documentation:
- **`DEPLOYMENT_GUIDE.md`** - Complete installation and usage guide
- **`TOKEN_MANAGEMENT.md`** - Token handling and troubleshooting
- **`README_CLI.md`** - Command-line interface reference

## 🔧 Configuration Required

### Before First Run:
Edit `appsettings.json` and replace these placeholder values:

```json
{
  "ReviztoAPI": {
    "AccessToken": "REPLACE_WITH_YOUR_ACCESS_TOKEN",
    "RefreshToken": "REPLACE_WITH_YOUR_REFRESH_TOKEN", 
    "ApiKey": "REPLACE_WITH_YOUR_API_KEY"
  }
}
```

### 🔑 Getting API Credentials:
1. Log into your Revizto account
2. Go to API settings/developer section
3. Generate an API key
4. Use the authentication flow to get initial tokens

## 💡 Usage Modes

### 🖥️ GUI Mode (Default):
- Interactive Windows Forms interface
- Real-time progress updates
- Project selection and filtering
- Perfect for manual exports

### 💻 Console Mode:
- Command-line operation
- JSON output for automation
- Perfect for scheduled tasks
- Integrates with other tools

### 📊 Project Management Integration:
```cmd
# Get all projects as JSON
ReviztoDataExporter.exe list-projects > projects.json

# Export specific project
ReviztoDataExporter.exe export "project-uuid" C:\Exports

# Export everything
ReviztoDataExporter.exe export-all C:\Exports

# Check status
ReviztoDataExporter.exe status
```

## �️ Database Integration

### ✅ Writes to SQL Server Database:
- **`ReviztoData`** database with structured tables
- **`tblUserLicenses`** - License and subscription data
- **`tblLicenseMembers`** - Team members and permissions  
- **`tblReviztoProjects`** - Project metadata and settings
- **`tblReviztoProjectIssues`** - All issues, tasks, and problems
- **`tblReviztoIssueComments`** - Comments and collaboration data

### 📊 Perfect for Business Intelligence:
- Direct SQL queries for custom reports
- Power BI / Tableau integration
- Excel pivot tables and analysis
- Custom dashboard development
- Data warehouse integration

### 🔧 Database Setup Required:
1. **Install SQL Server** (Express edition works fine)
2. **Create Database**: `CREATE DATABASE ReviztoData`
3. **Configure Connection** in `appsettings.json`
4. **Run Application** - Tables created automatically

## 📁 Generated Files

### SQL Server Database:
- **Structured tables** with normalized data for efficient querying
- **JSON columns** with complete API responses for flexibility  
- **Relationships** between licenses, projects, and issues
- **Timestamps** for data tracking and synchronization

### Exports:
- **`Exports/`** - JSON files with timestamped exports

### Logs:
- **`logs/log.txt`** - Current session logs
- **`logs/logYYYYMMDD.txt`** - Historical logs

## 🆘 Need Help?

1. **Quick Issues**: Run `start.ps1 -Status` to check system health
2. **Authentication Problems**: See `TOKEN_MANAGEMENT.md`
3. **Detailed Setup**: Read `DEPLOYMENT_GUIDE.md`
4. **Command Reference**: Check `README_CLI.md`

## 🎯 Perfect For:

- ✅ Project management dashboards
- ✅ Scheduled data synchronization  
- ✅ BI tool integration
- ✅ Data migration projects
- ✅ Custom reporting workflows
- ✅ Multi-system integration

---

**Ready to use!** No installation, no dependencies, just configure and run.

*Built with .NET 9.0 | Windows x64 | Self-contained executable*