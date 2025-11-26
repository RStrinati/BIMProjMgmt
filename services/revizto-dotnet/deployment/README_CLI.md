# Revizto Data Exporter - Command Line Interface

## Overview

The Revizto Data Exporter has been enhanced with a command-line interface (CLI) that allows integration with Python tkinter applications, PowerShell scripts, batch files, and other automation tools.

> Legacy note: Tkinter integration is retained here for reference only; the primary UI path for the BIM tool is now the web frontend.

## Files Created

- **ReviztoDataExporter.exe** - Main executable (located in `publish/` folder)
- **python_integration_example.py** - Complete Python tkinter integration example
- **powershell_example.ps1** - PowerShell integration example
- **revizto_cli.bat** - Windows batch file wrapper
- **CommandLineInterface.cs** - CLI implementation source code

## Command Line Usage

The executable supports both GUI mode (no arguments) and CLI mode (with arguments).

### Available Commands

```bash
ReviztoDataExporter.exe <command> [options]
```

#### 1. Get Status
```bash
ReviztoDataExporter.exe status
```
Returns JSON with application status, project count, and database connectivity.

#### 2. List Projects
```bash
ReviztoDataExporter.exe list-projects
```
Returns JSON array of all available projects with IDs, names, and license information.

#### 3. Refresh Projects
```bash
ReviztoDataExporter.exe refresh
```
Fetches fresh project data from the Revizto API and updates the database.

#### 4. Export Single Project
```bash
ReviztoDataExporter.exe export <project-id> [output-path]
```
Exports issues for a specific project. Examples:
```bash
ReviztoDataExporter.exe export 429b27f4-4359-40d6-a526-c2ac8374a3c9
ReviztoDataExporter.exe export 429b27f4-4359-40d6-a526-c2ac8374a3c9 C:\MyExports
```

#### 5. Export All Projects
```bash
ReviztoDataExporter.exe export-all [output-directory]
```
Exports issues for all projects. Examples:
```bash
ReviztoDataExporter.exe export-all
ReviztoDataExporter.exe export-all C:\MyExports
```

## Integration Examples

### Python tkinter Integration

The included `python_integration_example.py` provides a complete example of integrating the exporter with a Python GUI application. Key features:

- **ReviztoExporterInterface class**: Handles subprocess calls to the executable
- **ReviztoExporterGUI class**: Complete tkinter interface
- **JSON parsing**: Automatic parsing of command results
- **Threading**: Non-blocking UI operations
- **Error handling**: Comprehensive error management

To use in your tkinter app:

```python
from python_integration_example import ReviztoExporterInterface

# Initialize the interface
exporter = ReviztoExporterInterface("./publish/ReviztoDataExporter.exe")

# Get projects
projects_result = exporter.list_projects()
if projects_result["success"]:
    for project in projects_result["projects"]:
        print(f"Project: {project['name']} ({project['id']})")

# Export a project
export_result = exporter.export_project("429b27f4-4359-40d6-a526-c2ac8374a3c9", "C:\\Exports")
if export_result["success"]:
    print(f"Export successful: {export_result['exportedFile']}")
```

### PowerShell Integration

Use the provided PowerShell functions:

```powershell
# Load the functions
. .\powershell_example.ps1

# Get status
$status = Get-ReviztoStatus
Write-Host "Projects available: $($status.status.projectCount)"

# List projects
$projects = Get-ReviztoProjects
foreach ($project in $projects) {
    Write-Host "- $($project.name)"
}

# Export a project
$result = Export-ReviztoProject -ProjectId "429b27f4-4359-40d6-a526-c2ac8374a3c9" -OutputPath "C:\Exports"
```

### Batch File Integration

Use the provided batch wrapper:

```batch
REM Get status
revizto_cli.bat status

REM List projects
revizto_cli.bat list-projects

REM Export project
revizto_cli.bat export 429b27f4-4359-40d6-a526-c2ac8374a3c9 C:\Exports
```

## Output Format

All CLI commands return JSON output with the following structure:

### Success Response
```json
{
  "success": true,
  "message": "Operation completed",
  "data": { /* command-specific data */ },
  "timestamp": "2025-09-24T15:02:04.8751995+10:00"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "timestamp": "2025-09-24T15:02:04.8751995+10:00"
}
```

## Return Codes

- **0**: Success
- **1**: Error

## Requirements

- .NET 9.0 Runtime (if not using self-contained executable)
- Valid `appsettings.json` file in the same directory as the executable
- SQL Server Express LocalDB (for database operations)
- Valid Revizto API credentials in configuration

## Configuration

The CLI uses the same `appsettings.json` configuration file as the GUI version:

```json
{
  "ReviztoAPI": {
    "BaseUrl": "https://app.revizto.com",
    "RefreshToken": "your-refresh-token-here",
    "AccessToken": ""
  },
  "Database": {
    "ConnectionString": "Server=(localdb)\\MSSQLLocalDB;Database=ReviztoData;Integrated Security=true;"
  },
  "ExportSettings": {
    "OutputDirectory": "Exports"
  }
}
```

## Integration Benefits for BIM Management

This command-line interface enables powerful automation scenarios:

1. **Scheduled Exports**: Use Windows Task Scheduler to automatically export project data
2. **Python Integration**: Embed Revizto data export into larger Python BIM workflows
3. **PowerShell Automation**: Create enterprise scripts for bulk operations
4. **Third-party Tool Integration**: Call from other applications via command line
5. **CI/CD Pipelines**: Integrate exports into automated build/deployment processes

## Troubleshooting

### Common Issues

1. **"Exporter not found"**: Ensure the executable path is correct
2. **JSON parsing errors**: Check that no console logging is mixing with JSON output
3. **Permission errors**: Run with appropriate file system permissions
4. **Database connection failed**: Verify SQL Server LocalDB is installed and running

### Debug Information

All operations are logged to `logs/log.txt` for troubleshooting purposes. The GUI mode shows full console logging, while CLI mode suppresses info-level logs to keep JSON output clean.

## Example Integration Workflow

1. **Install**: Copy `ReviztoDataExporter.exe` and `appsettings.json` to your desired location
2. **Configure**: Update `appsettings.json` with your Revizto API credentials
3. **Test**: Run `ReviztoDataExporter.exe status` to verify connectivity
4. **Integrate**: Use the provided Python, PowerShell, or batch examples as templates
5. **Automate**: Schedule regular refreshes and exports based on your needs

This executable is now ready for seamless integration into your Python tkinter application and other automation workflows!
