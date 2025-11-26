#!/bin/bash

# BIM Project Management - Development Startup Script (Unix/Mac)
# This script starts both the Flask backend and React frontend

echo "🚀 Starting BIM Project Management System..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "   Download from: https://nodejs.org/"
    exit 1
fi

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.12+ first."
    exit 1
fi

PYTHON_CMD=$(command -v python3 || command -v python)

echo "✅ Node.js version: $(node --version)"
echo "✅ Python version: $($PYTHON_CMD --version)"
echo ""

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    echo "✅ Dependencies installed!"
    echo ""
fi

# Start backend in background
echo "🔧 Starting Flask backend (port 5000)..."
$PYTHON_CMD backend/app.py &
BACKEND_PID=$!
sleep 2

# Start frontend in background
echo "⚛️  Starting React frontend (port 5173)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
sleep 2

echo ""
echo "✅ Development servers started!"
echo ""
echo "📊 Backend (Flask):  http://localhost:5000"
echo "🌐 Frontend (React): http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers..."

# Handle Ctrl+C
trap "echo ''; echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Wait for processes
wait
