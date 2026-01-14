# React Data Imports - Quick Start Guide

**Get the React Data Imports UI running and test from the Tkinter app!**

**Status**: ✅ Complete - Backend + Frontend + Tkinter Integration  
**Date**: October 13, 2025

---

## 🚀 Three Ways to Test React Components

### ⭐ Option 1: From Tkinter Application (RECOMMENDED)

**The easiest way** - Test React components directly from the BIM Project Management desktop application!

#### Steps:

1. **Launch the Tkinter Application**:
   ```powershell
   python run_enhanced_ui.py
   ```

2. **Navigate to Data Imports Tab**:
   - Click on the **"📥 Data Imports"** tab (second tab in the notebook)
   - You'll see a new section: **"🚀 React Data Imports Components (Modern UI)"**

3. **Start Development Servers**:
   - Click the **"🚀 Start Development Servers"** button
   - Two terminal windows will open:
     - Flask backend (port 5000)
     - React frontend (port 5173)
   - Wait 3-5 seconds for green "● Running" indicators

4. **Launch React UI**:
   - Click the **"🌐 Launch React UI"** button
   - Browser automatically opens to: `http://localhost:5173/data-imports`
   - All 5 React tabs are ready to test!

5. **Test Your Components**:
   - **ACC Desktop Connector** - Test file extraction
   - **ACC Data Import** - Test CSV/ZIP import with bookmarks
   - **ACC Issues** - Test filtering and statistics
   - **Revizto Extraction** - Test run management
   - **Revit Health** - Test health metrics display

6. **Quick Access to Documentation**:
   - Click **"📖 Implementation Guide"** to open full docs
   - Click **"🚀 Quick Start Guide"** (this file)
   - Click **"📊 API Reference"** for API details

7. **Stop Servers When Done**:
   - Click **"⏹️ Stop Servers"** button in Tkinter app
   - Or simply close the two terminal windows

#### ✅ Benefits:
- ✅ No manual server management
- ✅ Visual server status indicators (green/red dots)
- ✅ One-click browser launch
- ✅ Integrated documentation links
- ✅ Works within existing workflow
- ✅ Easy cleanup (one button to stop all)

#### 🎬 Traditional Tkinter Tools Still Available:
The same tab also includes traditional data import tools:
- ACC Desktop Connector (Tkinter controls)
- ACC Data Import (CSV/ZIP)
- Revizto Extraction Tool launcher
- Revit Health Check import

---

### Option 2: Using PowerShell Script (AUTOMATED)

**For standalone testing** - Use the automated startup script:

#### Steps:

1. **Run the Startup Script**:
   ```powershell
   .\start-data-imports-testing.ps1
   ```

2. **What It Does**:
   - ✅ Checks if ports 5000 and 5173 are available
   - ✅ Starts Flask backend in new terminal
   - ✅ Starts React Vite dev server in new terminal
   - ✅ Waits for both servers to be ready (up to 30 seconds)
   - ✅ Automatically opens browser to Data Imports UI
   - ✅ Displays server PIDs, URLs, and status
   - ✅ Saves PIDs to file for easy cleanup

3. **Test Your Components**:
   - Browser automatically opens to: `http://localhost:5173/data-imports`
   - Navigate through all 5 tabs
   - Test features end-to-end

4. **Stop All Servers**:
   ```powershell
   .\stop-servers.ps1
   ```
   
   This will:
   - Stop all server processes
   - Clear ports 5000 and 5173
   - Clean up PID tracking file

#### ✅ Benefits:
- ✅ Fully automated startup sequence
- ✅ Port conflict detection
- ✅ Automatic browser launch
- ✅ Clean shutdown with single command
- ✅ No leftover processes

#### 📋 Script Output Example:
```
============================================
  BIM Data Imports - React Testing Setup
============================================

🔍 Checking ports...
✅ Port 5000 (Backend) is available
✅ Port 5173 (Frontend) is available

🚀 Starting Flask Backend Server (port 5000)...
✅ Backend server started (PID: 12345)

🚀 Starting React Frontend Server (port 5173)...
✅ Frontend server started (PID: 67890)

⏳ Waiting for servers to be ready...
✅ Backend is ready! (http://localhost:5000)
✅ Frontend is ready! (http://localhost:5173)

============================================
  🎉 Servers Started Successfully!
============================================

Backend Server:
  URL: http://localhost:5000
  API: http://localhost:5000/api

Frontend Server:
  URL: http://localhost:5173
  Data Imports: http://localhost:5173/data-imports

🌐 Opening browser to Data Imports UI...
✅ All systems ready for testing!
```

---

### Option 3: Manual Server Start (TRADITIONAL)

**For developers who prefer manual control:**

#### Terminal 1 - Backend:

```powershell
# Navigate to backend
cd backend

# Start Flask server
python app.py
```

**Output**: Backend running on `http://localhost:5000`

#### Terminal 2 - Frontend:

```powershell
# Navigate to frontend
cd frontend

# Install dependencies (first time only)
npm install

# Start Vite dev server
npm run dev
```

**Output**: Frontend running on `http://localhost:5173`

#### Open Browser:

Navigate to: `http://localhost:5173/data-imports`

---

## 📍 Navigation Paths

Once React frontend is running, you can access Data Imports via:

### From a Specific Project:
```
http://localhost:5173/projects/1/data-imports
```
- Replace `1` with actual project ID
- Shows data specific to that project

### Standalone View:
```
http://localhost:5173/data-imports
```
- General data imports page
- Can select project from within

---

## 🎯 Quick Feature Testing Guide

### Tab 1: ACC Desktop Connector 📁

**Test Flow**:
1. View current folder path configuration
2. Edit folder path: `C:\Users\YourName\Autodesk\ACC\ProjectName`
3. Click **"Save Folder Path"**
4. Verify folder exists (shows green checkmark)
5. Click **"Extract Files"**
6. Monitor progress bar
7. View extracted files in paginated table
8. Test pagination (10, 25, 50, 100 items per page)

**Endpoints Tested**:
- `GET /api/acc-connector/folder/:projectId` ✅
- `POST /api/acc-connector/folder` ✅
- `GET /api/acc-connector/files/:projectId` ✅
- `POST /api/acc-connector/extract` ✅

---

### Tab 2: ACC Data Import 📤

**Test Flow**:
1. Enter file path: `C:\path\to\data.csv`
2. Select type: **CSV** or **ZIP**
3. Click **"Import Data"**
4. Monitor import progress
5. View import logs table (status, records, errors)
6. Test bookmark features:
   - Click **"Add Bookmark"** with current path
   - Enter bookmark name
   - Click saved bookmark to load path
   - Delete bookmark
7. Test pagination on import logs

**Endpoints Tested**:
- `GET /api/acc-import/logs/:projectId` ✅
- `POST /api/acc-import/import` ✅
- `GET /api/acc-import/bookmarks/:projectId` ✅
- `POST /api/acc-import/bookmark` ✅
- `PUT /api/acc-import/bookmark/:id` ✅
- `DELETE /api/acc-import/bookmark/:id` ✅

---

### Tab 3: ACC Issues 🐛

**Test Flow**:
1. View statistics cards:
   - Total Issues
   - Open Issues
   - Closed Issues
   - Overdue Issues
2. Enter search term in filter (e.g., "Clash")
3. Click **"Apply Filter"**
4. View filtered issues in table
5. Check status color chips (Open=blue, Closed=green)
6. Test pagination
7. Click **"Clear Filter"**

**Endpoints Tested**:
- `GET /api/acc-issues/issues/:projectId` ✅
- `GET /api/acc-issues/stats/:projectId` ✅

---

### Tab 4: Revizto Extraction 🔄

**Test Flow**:
1. View last extraction run summary:
   - Run ID
   - Status
   - Records extracted
   - Timestamp
2. Click **"Start New Extraction"**
3. Enter export folder path
4. Confirm extraction
5. Monitor new run in history table
6. View status icons (✅, ⚠️, ⏳)
7. Check duration calculations
8. Test pagination on runs table

**Endpoints Tested**:
- `GET /api/revizto/runs/:projectId` ✅
- `POST /api/revizto/start` ✅
- `GET /api/revizto/last-run/:projectId` ✅

---

### Tab 5: Revit Health Check ❤️

**Test Flow**:
1. View statistics cards:
   - Total Files
   - Average Health Score (with progress bar)
   - Total Warnings
   - Total Errors
2. View health files table
3. Check health score color coding:
   - Green (Good) ≥ 80
   - Yellow (Fair) ≥ 60
   - Red (Poor) < 60
4. Sort by file name or health score
5. Test pagination

**Endpoints Tested**:
- `GET /api/revit-health/files/:projectId` ✅
- `GET /api/revit-health/summary/:projectId` ✅

---

## 🧪 Component Testing Checklist

Use this checklist to ensure all components work properly:

### General UI Tests
- [ ] All 5 tabs are visible
- [ ] Tab icons display correctly
- [ ] Tab switching works smoothly
- [ ] Breadcrumb navigation shows correct path
- [ ] Loading spinners appear during API calls
- [ ] Error messages display when API fails

### ACC Desktop Connector Tests
- [ ] Folder path loads from database
- [ ] Folder path can be saved
- [ ] Folder existence validation works
- [ ] Files extraction triggers successfully
- [ ] Progress bar shows during extraction
- [ ] Files table populates with data
- [ ] Pagination controls work (10/25/50/100)
- [ ] File type chips display correctly

### ACC Data Import Tests
- [ ] Import form accepts file path
- [ ] Type selector switches CSV/ZIP
- [ ] Import triggers and shows progress
- [ ] Import logs table loads
- [ ] Status chips show correct colors
- [ ] Error tooltips display on hover
- [ ] Add bookmark dialog opens
- [ ] Bookmarks save and load correctly
- [ ] Delete bookmark works
- [ ] Pagination works on logs table

### ACC Issues Tests
- [ ] Statistics cards load with correct numbers
- [ ] Total, Open, Closed, Overdue counts accurate
- [ ] Search filter applies correctly
- [ ] Issues table filters by search term
- [ ] Status chips color-coded (blue/green)
- [ ] Type chips display correctly
- [ ] Pagination works
- [ ] Clear filter resets search

### Revizto Extraction Tests
- [ ] Last run summary displays
- [ ] Start extraction dialog opens
- [ ] Export folder path accepts input
- [ ] New extraction triggers
- [ ] Runs table loads
- [ ] Status icons display (✅⚠️⏳)
- [ ] Duration calculates correctly
- [ ] Pagination works

### Revit Health Tests
- [ ] Statistics cards load
- [ ] Average health score calculates
- [ ] Progress bar shows score visually
- [ ] Warnings/Errors counts accurate
- [ ] Files table loads
- [ ] Health scores color-coded (green/yellow/red)
- [ ] Good/Fair/Poor labels correct
- [ ] Pagination works

### React Query & Data Fetching Tests
- [ ] Initial data loads on tab mount
- [ ] Refresh button re-fetches data
- [ ] Cache works (fast subsequent loads)
- [ ] Stale data updates automatically
- [ ] Error states handle gracefully
- [ ] Loading states show spinners

### Responsive Design Tests
- [ ] Desktop layout (1920x1080) looks good
- [ ] Laptop layout (1366x768) works
- [ ] Tablet layout (768x1024) adapts
- [ ] Mobile layout (375x667) usable
- [ ] Tables scroll horizontally if needed
- [ ] Cards stack on narrow screens

---

## 🔧 Troubleshooting

### Servers Won't Start from Tkinter

**Symptom**: Clicking "Start Development Servers" does nothing or shows error

**Solutions**:
1. Check if ports are already in use:
   ```powershell
   netstat -an | findstr "5000 5173"
   ```
2. Kill existing processes:
   ```powershell
   .\stop-servers.ps1
   ```
3. Try starting manually (Option 3 above)

### Browser Doesn't Open

**Symptom**: Servers start but browser doesn't launch

**Solutions**:
1. Manually navigate to: `http://localhost:5173/data-imports`
2. Check if default browser is set
3. Try different browser

### React UI Shows Blank Page

**Symptom**: Browser opens but page is blank or shows error

**Solutions**:
1. Check browser console (F12) for errors
2. Verify backend is running: `http://localhost:5000/api/projects`
3. Check network tab for failed API calls
4. Restart both servers

### API Calls Fail (Network Errors)

**Symptom**: Components load but data doesn't appear

**Solutions**:
1. Verify backend running on port 5000
2. Check backend terminal for errors
3. Test API directly: `http://localhost:5000/api/projects`
4. Check database connection
5. Review backend logs

### TypeScript Errors in Console

**Symptom**: Browser console shows TypeScript/React errors

**Solutions**:
1. Rebuild frontend:
   ```powershell
   cd frontend
   npm run build
   npm run dev
   ```
2. Clear browser cache (Ctrl+Shift+Delete)
3. Hard refresh (Ctrl+F5)

### Data Doesn't Load (Empty Tables)

**Symptom**: UI works but tables show "No data"

**Solutions**:
1. Check if project has data in database
2. Try different project ID
3. Verify API returns data:
   ```powershell
   curl http://localhost:5000/api/acc-connector/files/1
   ```
4. Check API response format matches TypeScript types

---

## 📚 Next Steps

### Learn More:
- **Full Implementation Guide**: `docs/REACT_DATA_IMPORTS_IMPLEMENTATION_COMPLETE.md`
- **API Reference**: `docs/DATA_IMPORTS_API_REFERENCE.md`
- **Implementation Summary**: `docs/DATA_IMPORTS_IMPLEMENTATION_SUMMARY.md`

### Run Tests:
```powershell
cd frontend
npm run test
```

### Build for Production:
```powershell
cd frontend
npm run build
```

### Deploy:
- Backend: Deploy Flask app to production server
- Frontend: Deploy `frontend/dist` to web server or CDN
- Configure environment variables
- Set up reverse proxy (nginx/Apache)

---

## 🎉 Success!

You now have three convenient ways to test the React Data Imports components:

1. ⭐ **From Tkinter App** - Most integrated, easiest for daily use
2. 🚀 **PowerShell Script** - Automated, best for standalone testing
3. 🔧 **Manual Start** - Full control, best for development

Choose the method that works best for your workflow and start testing!

**Happy Testing!** 🚀
