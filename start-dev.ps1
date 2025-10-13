# BIM Project Management - Development Startup Script
# This script starts both the Flask backend and React frontend

Write-Host "Starting BIM Project Management System..." -ForegroundColor Green
Write-Host ""

# Check if Node.js is installed
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js is not installed. Please install Node.js 18+ first." -ForegroundColor Red
    Write-Host "   Download from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Check if Python is installed
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed. Please install Python 3.12+ first." -ForegroundColor Red
    exit 1
}

Write-Host "Node.js version: $(node --version)" -ForegroundColor Cyan
Write-Host "Python version: $(python --version)" -ForegroundColor Cyan
Write-Host ""

# Check if frontend dependencies are installed
if (!(Test-Path "frontend/node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
    Write-Host "Dependencies installed!" -ForegroundColor Green
    Write-Host ""
}

# Start backend in a new PowerShell window
Write-Host "Starting Flask backend (port 5000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python backend/app.py"
Start-Sleep -Seconds 2

# Start frontend in a new PowerShell window  
Write-Host "Starting React frontend (port 5173)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD/frontend'; npm run dev"
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "Development servers started!" -ForegroundColor Green
Write-Host ""
Write-Host "Backend (Flask):  http://localhost:5000" -ForegroundColor Yellow
Write-Host "Frontend (React): http://localhost:5173" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Enter to open the frontend in your browser..." -ForegroundColor Cyan
Read-Host

# Open browser
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "Happy coding!" -ForegroundColor Green
Write-Host "   Press Ctrl+C in each terminal window to stop the servers." -ForegroundColor Gray
