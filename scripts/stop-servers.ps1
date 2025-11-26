# stop-servers.ps1
#
# Script to stop all Data Imports testing servers

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Stopping Data Imports Testing Servers  " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = $PSScriptRoot
$PidsFile = Join-Path $ProjectRoot "server-pids.txt"

# Check if PIDs file exists
if (Test-Path $PidsFile) {
    Write-Host "📄 Reading server PIDs from file..." -ForegroundColor Yellow
    $PidsContent = Get-Content -Path $PidsFile
    $Pids = $PidsContent -split ","
    
    foreach ($Pid in $Pids) {
        if ($Pid -match '^\d+$') {
            $PidNum = [int]$Pid
            try {
                $Process = Get-Process -Id $PidNum -ErrorAction SilentlyContinue
                if ($Process) {
                    Write-Host "🛑 Stopping process $PidNum ($($Process.ProcessName))..." -ForegroundColor Yellow
                    Stop-Process -Id $PidNum -Force
                    Write-Host "✅ Process $PidNum stopped" -ForegroundColor Green
                } else {
                    Write-Host "ℹ️  Process $PidNum not found (may have already stopped)" -ForegroundColor Gray
                }
            } catch {
                Write-Host "⚠️  Could not stop process $PidNum" -ForegroundColor Yellow
            }
        }
    }
    
    # Remove PIDs file
    Remove-Item -Path $PidsFile -Force
    Write-Host "🗑️  PIDs file removed" -ForegroundColor Gray
} else {
    Write-Host "ℹ️  No PIDs file found" -ForegroundColor Gray
}

Write-Host ""

# Also try to kill any Python/Node processes on those ports
Write-Host "🔍 Checking for processes on ports 5000 and 5173..." -ForegroundColor Yellow

# Kill processes on port 5000 (Backend)
$Port5000 = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($Port5000) {
    $ProcessId = $Port5000.OwningProcess
    Write-Host "🛑 Stopping process on port 5000 (PID: $ProcessId)..." -ForegroundColor Yellow
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Port 5000 cleared" -ForegroundColor Green
} else {
    Write-Host "✅ Port 5000 is already free" -ForegroundColor Green
}

# Kill processes on port 5173 (Frontend)
$Port5173 = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
if ($Port5173) {
    $ProcessId = $Port5173.OwningProcess
    Write-Host "🛑 Stopping process on port 5173 (PID: $ProcessId)..." -ForegroundColor Yellow
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Port 5173 cleared" -ForegroundColor Green
} else {
    Write-Host "✅ Port 5173 is already free" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ All servers stopped!" -ForegroundColor Green
Write-Host ""
