# start-data-imports-testing.ps1
# 
# Comprehensive script to start all servers needed for Data Imports React Component Testing
# 
# This script:
# 1. Starts Flask backend (port 5000)
# 2. Starts React frontend (port 5173) with Vite dev server
# 3. Opens browser to React Data Imports UI
# 4. Provides status monitoring

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  BIM Data Imports - React Testing Setup  " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Get project root directory
$ProjectRoot = $PSScriptRoot
$BackendPath = Join-Path $ProjectRoot "backend"
$FrontendPath = Join-Path $ProjectRoot "frontend"

# Check if directories exist
if (-not (Test-Path $BackendPath)) {
    Write-Host "❌ ERROR: Backend directory not found: $BackendPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $FrontendPath)) {
    Write-Host "❌ ERROR: Frontend directory not found: $FrontendPath" -ForegroundColor Red
    exit 1
}

Write-Host "📁 Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "📁 Backend Path: $BackendPath" -ForegroundColor Gray
Write-Host "📁 Frontend Path: $FrontendPath" -ForegroundColor Gray
Write-Host ""

# Function to check if port is in use
function Test-Port {
    param([int]$Port)
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect("localhost", $Port)
        $tcpClient.Close()
        return $true
    } catch {
        return $false
    }
}

# Check if ports are already in use
Write-Host "🔍 Checking ports..." -ForegroundColor Yellow

if (Test-Port -Port 5000) {
    Write-Host "⚠️  WARNING: Port 5000 (Backend) is already in use" -ForegroundColor Yellow
    Write-Host "   Backend server may already be running" -ForegroundColor Gray
} else {
    Write-Host "✅ Port 5000 (Backend) is available" -ForegroundColor Green
}

if (Test-Port -Port 5173) {
    Write-Host "⚠️  WARNING: Port 5173 (Frontend) is already in use" -ForegroundColor Yellow
    Write-Host "   Frontend server may already be running" -ForegroundColor Gray
} else {
    Write-Host "✅ Port 5173 (Frontend) is available" -ForegroundColor Green
}

Write-Host ""

# Start Backend Server
Write-Host "🚀 Starting Flask Backend Server (port 5000)..." -ForegroundColor Cyan
$BackendJob = Start-Process -FilePath "python" -ArgumentList "app.py" `
    -WorkingDirectory $BackendPath `
    -PassThru `
    -WindowStyle Normal

if ($BackendJob) {
    Write-Host "✅ Backend server started (PID: $($BackendJob.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start backend server" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Wait a moment for backend to initialize
Write-Host "⏳ Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start Frontend Server
Write-Host "🚀 Starting React Frontend Server (port 5173)..." -ForegroundColor Cyan
$FrontendJob = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev" `
    -WorkingDirectory $FrontendPath `
    -PassThru `
    -WindowStyle Normal

if ($FrontendJob) {
    Write-Host "✅ Frontend server started (PID: $($FrontendJob.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start frontend server" -ForegroundColor Red
    # Clean up backend
    Stop-Process -Id $BackendJob.Id -Force
    exit 1
}

Write-Host ""

# Wait for servers to be ready
Write-Host "⏳ Waiting for servers to be ready..." -ForegroundColor Yellow
$maxWaitSeconds = 30
$waitedSeconds = 0
$backendReady = $false
$frontendReady = $false

while ($waitedSeconds -lt $maxWaitSeconds) {
    Start-Sleep -Seconds 1
    $waitedSeconds++
    
    if (-not $backendReady) {
        $backendReady = Test-Port -Port 5000
        if ($backendReady) {
            Write-Host "✅ Backend is ready! (http://localhost:5000)" -ForegroundColor Green
        }
    }
    
    if (-not $frontendReady) {
        $frontendReady = Test-Port -Port 5173
        if ($frontendReady) {
            Write-Host "✅ Frontend is ready! (http://localhost:5173)" -ForegroundColor Green
        }
    }
    
    if ($backendReady -and $frontendReady) {
        break
    }
    
    Write-Host "   Waiting... ($waitedSeconds/$maxWaitSeconds seconds)" -ForegroundColor Gray
}

Write-Host ""

if (-not $backendReady) {
    Write-Host "⚠️  WARNING: Backend may not be ready yet" -ForegroundColor Yellow
}

if (-not $frontendReady) {
    Write-Host "⚠️  WARNING: Frontend may not be ready yet" -ForegroundColor Yellow
}

# Display server info
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  🎉 Servers Started Successfully!  " -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend Server:" -ForegroundColor Yellow
Write-Host "  URL: http://localhost:5000" -ForegroundColor White
Write-Host "  API: http://localhost:5000/api" -ForegroundColor White
Write-Host "  PID: $($BackendJob.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "Frontend Server:" -ForegroundColor Yellow
Write-Host "  URL: http://localhost:5173" -ForegroundColor White
Write-Host "  Data Imports: http://localhost:5173/data-imports" -ForegroundColor White
Write-Host "  PID: $($FrontendJob.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "React Data Imports Features:" -ForegroundColor Yellow
Write-Host "  1. ACC Desktop Connector - File extraction" -ForegroundColor White
Write-Host "  2. ACC Data Import - CSV/ZIP import with bookmarks" -ForegroundColor White
Write-Host "  3. ACC Issues - Issues display with statistics" -ForegroundColor White
Write-Host "  4. Revizto Extraction - Run management" -ForegroundColor White
Write-Host "  5. Revit Health Check - Health metrics" -ForegroundColor White
Write-Host ""

# Open browser
Write-Host "🌐 Opening browser to Data Imports UI..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
Start-Process "http://localhost:5173/data-imports"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📖 Documentation:" -ForegroundColor Yellow
Write-Host "  • Quick Start: docs/REACT_DATA_IMPORTS_QUICK_START.md" -ForegroundColor White
Write-Host "  • Full Guide: docs/REACT_DATA_IMPORTS_IMPLEMENTATION_COMPLETE.md" -ForegroundColor White
Write-Host "  • API Reference: docs/DATA_IMPORTS_API_REFERENCE.md" -ForegroundColor White
Write-Host ""
Write-Host "🛑 To stop servers:" -ForegroundColor Yellow
Write-Host "  • Close both terminal windows" -ForegroundColor White
Write-Host "  • Or run: ./stop-servers.ps1" -ForegroundColor White
Write-Host ""
Write-Host "✅ All systems ready for testing!" -ForegroundColor Green
Write-Host ""

# Keep track of PIDs
$PidsFile = Join-Path $ProjectRoot "server-pids.txt"
"$($BackendJob.Id),$($FrontendJob.Id)" | Out-File -FilePath $PidsFile -Encoding UTF8

Write-Host "💾 Server PIDs saved to: server-pids.txt" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop monitoring (servers will continue running)" -ForegroundColor Gray
Write-Host "Press any other key to exit..." -ForegroundColor Gray

# Wait for user input
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
