# Revizto Data Exporter - PowerShell Launcher
# Advanced deployment script for project management integration

param(
    [switch]$Console,
    [string]$Project = "",
    [switch]$Help,
    [switch]$Status
)

$ExeName = "ReviztoDataExporter.exe"
$ConfigFile = "appsettings.json"

function Show-Help {
    Write-Host "Revizto Data Exporter - PowerShell Launcher" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\start.ps1                    - Start GUI mode"
    Write-Host "  .\start.ps1 -Console           - Start console mode (export all)"
    Write-Host "  .\start.ps1 -Project <uuid>    - Export specific project"
    Write-Host "  .\start.ps1 -Status            - Check system status"
    Write-Host "  .\start.ps1 -Help              - Show this help"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\start.ps1 -Console"
    Write-Host "  .\start.ps1 -Project 'eadbc964-2829-49e0-a4ca-3b61dfc67aa5'"
    Write-Host ""
}

function Test-Prerequisites {
    $issues = @()
    
    if (-not (Test-Path $ExeName)) {
        $issues += "Missing: $ExeName"
    }
    
    if (-not (Test-Path $ConfigFile)) {
        $issues += "Missing: $ConfigFile"
    }
    
    if (-not (Test-Path "sni.dll")) {
        $issues += "Missing: sni.dll (SQL Server support)"
    }
    
    if (-not (Test-Path "SQLite.Interop.dll")) {
        $issues += "Missing: SQLite.Interop.dll (Database support)"
    }
    
    return $issues
}

function Show-Status {
    Write-Host "Revizto Data Exporter - System Status" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host ""
    
    $issues = Test-Prerequisites
    
    if ($issues.Count -eq 0) {
        Write-Host "✓ All required files present" -ForegroundColor Green
    } else {
        Write-Host "✗ Missing files detected:" -ForegroundColor Red
        foreach ($issue in $issues) {
            Write-Host "  - $issue" -ForegroundColor Red
        }
        return $false
    }
    
    # Check configuration
    if (Test-Path $ConfigFile) {
        try {
            $config = Get-Content $ConfigFile -Raw | ConvertFrom-Json
            $apiConfig = $config.ReviztoAPI
            
            if ($apiConfig.AccessToken -and $apiConfig.RefreshToken -and $apiConfig.ApiKey) {
                Write-Host "✓ API configuration appears complete" -ForegroundColor Green
            } else {
                Write-Host "⚠ API configuration may be incomplete - check tokens/API key" -ForegroundColor Yellow
            }
            
            # Check database configuration
            if ($config.Database -and $config.Database.ConnectionString) {
                if ($config.Database.ConnectionString -like "*YOUR_SQL_SERVER*" -or 
                    $config.Database.ConnectionString -like "*REPLACE_WITH*") {
                    Write-Host "⚠ Database connection string needs to be configured" -ForegroundColor Yellow
                } else {
                    Write-Host "✓ Database connection string is configured" -ForegroundColor Green
                }
            } else {
                Write-Host "✗ Database connection string is missing" -ForegroundColor Red
                return $false
            }
        } catch {
            Write-Host "✗ Configuration file is invalid JSON" -ForegroundColor Red
            return $false
        }
    }
    
    # Check for previous runs
    if (Test-Path "ReviztoData.db") {
        $dbSize = (Get-Item "ReviztoData.db").Length / 1KB
        Write-Host "✓ Database exists (Size: $($dbSize.ToString('F1')) KB)" -ForegroundColor Green
    } else {
        Write-Host "○ No database found (will be created on first run)" -ForegroundColor Gray
    }
    
    if (Test-Path "logs") {
        $logFiles = Get-ChildItem "logs" -Filter "*.txt" | Measure-Object
        Write-Host "✓ Log directory exists ($($logFiles.Count) log files)" -ForegroundColor Green
    } else {
        Write-Host "○ No logs directory (will be created on first run)" -ForegroundColor Gray
    }
    
    if (Test-Path "Exports") {
        $exportFiles = Get-ChildItem "Exports" -Filter "*.json" | Measure-Object
        Write-Host "✓ Exports directory exists ($($exportFiles.Count) export files)" -ForegroundColor Green
    } else {
        Write-Host "○ No exports directory (will be created on first run)" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "System appears ready for operation." -ForegroundColor Green
    return $true
}

# Main script logic
if ($Help) {
    Show-Help
    exit
}

if ($Status) {
    Show-Status
    exit
}

# Check prerequisites
$issues = Test-Prerequisites
if ($issues.Count -gt 0) {
    Write-Host "Cannot start: Missing required files" -ForegroundColor Red
    foreach ($issue in $issues) {
        Write-Host "  - $issue" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please ensure all deployment files are extracted to the same folder." -ForegroundColor Yellow
    exit 1
}

# Build command arguments
$arguments = @()

if ($Console) {
    $arguments += "--console"
    Write-Host "Starting in console mode..." -ForegroundColor Yellow
}

if ($Project) {
    $arguments += "--project"
    $arguments += $Project
    Write-Host "Exporting specific project: $Project" -ForegroundColor Yellow
}

# Start the application
try {
    if ($arguments.Count -gt 0) {
        Write-Host "Executing: $ExeName $($arguments -join ' ')" -ForegroundColor Gray
        & ".\$ExeName" $arguments
    } else {
        Write-Host "Starting GUI mode..." -ForegroundColor Yellow
        & ".\$ExeName"
    }
    
    $exitCode = $LASTEXITCODE
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "Application completed successfully." -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Application exited with code: $exitCode" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error starting application: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}