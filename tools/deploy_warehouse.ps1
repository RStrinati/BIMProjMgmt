# ==============================================================================
# Revit Health Warehouse - PowerShell Deployment Script
# Deploys all warehouse objects in correct dependency order
# ==============================================================================

param(
    [string]$Server = "localhost",
    [string]$Database = "ProjectManagement",
    [switch]$Debug = $false
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "REVIT HEALTH WAREHOUSE DEPLOYMENT" -ForegroundColor Cyan
Write-Host "Server: $Server" -ForegroundColor Cyan
Write-Host "Database: $Database" -ForegroundColor Cyan
Write-Host "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date
$scriptRoot = Split-Path -Parent $PSCommandPath
$projectRoot = Split-Path -Parent $scriptRoot

# SQL files in deployment order
$deploymentSteps = @(
    @{
        Name = "Dimension Tables"
        Files = @(
            "$projectRoot\sql\tables\dim_revit_file.sql"
        )
    },
    @{
        Name = "Staging Tables"
        Files = @(
            "$projectRoot\sql\tables\stg_revit_health_snapshots.sql"
        )
    },
    @{
        Name = "Fact Tables"
        Files = @(
            "$projectRoot\sql\tables\fact_revit_health_daily.sql"
        )
    },
    @{
        Name = "ETL Procedures"
        Files = @(
            "$projectRoot\sql\procedures\usp_load_stg_revit_health.sql",
            "$projectRoot\sql\procedures\usp_load_fact_revit_health_daily.sql"
        )
    },
    @{
        Name = "Analytical Marts"
        Files = @(
            "$projectRoot\sql\views\mart_v_project_health_summary.sql",
            "$projectRoot\sql\views\mart_v_health_trends_monthly.sql"
        )
    }
)

$errorCount = 0
$successCount = 0

# Function to execute SQL file
function Invoke-SqlFile {
    param(
        [string]$FilePath,
        [string]$Server,
        [string]$Database
    )
    
    if (-not (Test-Path $FilePath)) {
        Write-Host "  ✗ File not found: $FilePath" -ForegroundColor Red
        return $false
    }
    
    try {
        $fileName = Split-Path -Leaf $FilePath
        Write-Host "  → Executing: $fileName" -ForegroundColor Gray
        
        $sqlContent = Get-Content $FilePath -Raw
        
        # Execute using Invoke-Sqlcmd if available, otherwise use sqlcmd.exe
        if (Get-Command Invoke-Sqlcmd -ErrorAction SilentlyContinue) {
            Invoke-Sqlcmd -ServerInstance $Server -Database $Database -Query $sqlContent -Verbose:$Debug
        } else {
            # Use sqlcmd.exe
            $tempFile = [System.IO.Path]::GetTempFileName()
            $sqlContent | Out-File -FilePath $tempFile -Encoding UTF8
            
            $result = & sqlcmd -S $Server -d $Database -E -i $tempFile 2>&1
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  ✗ Error executing $fileName" -ForegroundColor Red
                Write-Host $result -ForegroundColor Red
                Remove-Item $tempFile -Force
                return $false
            }
            
            if ($Debug) {
                Write-Host $result -ForegroundColor Gray
            }
            
            Remove-Item $tempFile -Force
        }
        
        Write-Host "  ✓ $fileName completed" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Host "  ✗ Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Deploy each step
$stepNumber = 1
foreach ($step in $deploymentSteps) {
    Write-Host ""
    Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host "STEP ${stepNumber}: Creating $($step.Name)" -ForegroundColor Yellow
    Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Yellow
    
    $stepStart = Get-Date
    
    foreach ($file in $step.Files) {
        $success = Invoke-SqlFile -FilePath $file -Server $Server -Database $Database
        
        if ($success) {
            $successCount++
        } else {
            $errorCount++
        }
    }
    
    $stepDuration = (Get-Date) - $stepStart
    Write-Host "  Duration: $([math]::Round($stepDuration.TotalSeconds, 2)) seconds" -ForegroundColor Gray
    
    $stepNumber++
}

# Verification
Write-Host ""
Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Yellow
Write-Host "STEP ${stepNumber}: Verifying Deployment" -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Yellow

$verificationSQL = @'
-- Check all objects exist
SELECT 
    ''dim.revit_file'' as object_name,
    CASE WHEN OBJECT_ID(''dim.revit_file'', ''U'') IS NOT NULL THEN ''EXISTS'' ELSE ''MISSING'' END as status
UNION ALL
SELECT 
    ''stg.revit_health_snapshots'',
    CASE WHEN OBJECT_ID(''stg.revit_health_snapshots'', ''U'') IS NOT NULL THEN ''EXISTS'' ELSE ''MISSING'' END
UNION ALL
SELECT 
    ''fact.revit_health_daily'',
    CASE WHEN OBJECT_ID(''fact.revit_health_daily'', ''U'') IS NOT NULL THEN ''EXISTS'' ELSE ''MISSING'' END
UNION ALL
SELECT 
    ''warehouse.usp_load_stg_revit_health'',
    CASE WHEN OBJECT_ID(''warehouse.usp_load_stg_revit_health'', ''P'') IS NOT NULL THEN ''EXISTS'' ELSE ''MISSING'' END
UNION ALL
SELECT 
    ''warehouse.usp_load_fact_revit_health_daily'',
    CASE WHEN OBJECT_ID(''warehouse.usp_load_fact_revit_health_daily'', ''P'') IS NOT NULL THEN ''EXISTS'' ELSE ''MISSING'' END
UNION ALL
SELECT 
    ''mart.v_project_health_summary'',
    CASE WHEN OBJECT_ID(''mart.v_project_health_summary'', ''V'') IS NOT NULL THEN ''EXISTS'' ELSE ''MISSING'' END
UNION ALL
SELECT 
    ''mart.v_health_trends_monthly'',
    CASE WHEN OBJECT_ID(''mart.v_health_trends_monthly'', ''V'') IS NOT NULL THEN ''EXISTS'' ELSE ''MISSING'' END
'@

$verificationResults = @()
try {
    if (Get-Command Invoke-Sqlcmd -ErrorAction SilentlyContinue) {
        $verificationResults = Invoke-Sqlcmd -ServerInstance $Server -Database $Database -Query $verificationSQL
    } else {
        $tempFile = [System.IO.Path]::GetTempFileName()
        $verificationSQL | Out-File -FilePath $tempFile -Encoding UTF8
        $output = & sqlcmd -S $Server -d $Database -E -i $tempFile -h -1 -W
        Remove-Item $tempFile -Force
        
        $output | ForEach-Object {
            if ($_ -match '(\S+)\s+(\S+)') {
                $verificationResults += [PSCustomObject]@{
                    object_name = $matches[1]
                    status = $matches[2]
                }
            }
        }
    }
} catch {
    Write-Host "  ✗ Verification failed: $($_.Exception.Message)" -ForegroundColor Red
    $errorCount++
}

foreach ($result in $verificationResults) {
    if ($result.status -eq 'EXISTS') {
        Write-Host "  ✓ $($result.object_name) exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $($result.object_name) MISSING" -ForegroundColor Red
        $errorCount++
    }
}

# Summary
$totalDuration = (Get-Date) - $startTime
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT SUMMARY" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

if ($errorCount -eq 0) {
    Write-Host "Status: ✓ SUCCESS" -ForegroundColor Green
} else {
    Write-Host "Status: ✗ FAILED" -ForegroundColor Red
}

Write-Host "Files Deployed: $successCount" -ForegroundColor White
Write-Host "Errors: $errorCount" -ForegroundColor $(if ($errorCount -eq 0) { "Green" } else { "Red" })
Write-Host "Total Duration: $([math]::Round($totalDuration.TotalSeconds, 2)) seconds" -ForegroundColor White
Write-Host "Completed: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

if ($errorCount -eq 0) {
    Write-Host "✓ All warehouse objects deployed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "NEXT STEPS:" -ForegroundColor Yellow
    Write-Host "  1. Run initial ETL:" -ForegroundColor White
    Write-Host "     sqlcmd -S $Server -d $Database -E -Q `"EXEC warehouse.usp_load_stg_revit_health @debug = 1`"" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Load fact table:" -ForegroundColor White
    Write-Host "     sqlcmd -S $Server -d $Database -E -Q `"EXEC warehouse.usp_load_fact_revit_health_daily @debug = 1`"" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. Test Python service:" -ForegroundColor White
    Write-Host "     python tools\deploy_warehouse.py" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "✗ Deployment completed with errors. Please review the log above." -ForegroundColor Red
    exit 1
}
