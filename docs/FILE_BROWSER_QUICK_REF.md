# File Browser & App Launcher - Quick Reference

## Quick Start

### Start Servers
```powershell
# Terminal 1 - Backend (Flask)
cd backend
python app.py

# Terminal 2 - Frontend (React)
cd frontend
npm run dev
```

### Access Data Imports
Navigate to: `http://localhost:5174/data-imports`

---

## Component Features

### 1. ACC Data Import
**Browse Files**: CSV or ZIP
```
1. Click "Browse" button
2. Select CSV or ZIP file
3. Path auto-fills
4. Click "Import Data"
```

### 2. Revizto Import
**Launch App**: Revizto Data Exporter
```
1. Click "Launch Revizto Data Exporter"
2. App opens automatically
3. Export data using Revizto
4. Return to React app
5. Click "Start Extraction"
6. Browse for export folder
7. Click "Start"
```

**Browse Folders**: Export location
```
1. Click "Start Extraction"
2. In dialog, click "Browse"
3. Select folder
4. Path auto-fills
5. Click "Start"
```

### 3. Revit Health Check
**Import Health Data**: Run importer script
```
1. Click "Browse" in Import section
2. Select folder with JSON files
3. Click "Run Health Importer"
4. Wait for completion (shows execution time)
5. Tables auto-refresh
```

---

## API Endpoints

### File Browser
- `POST /api/file-browser/select-file` - Open file dialog
- `POST /api/file-browser/select-folder` - Open folder dialog

### Application Launcher
- `POST /api/applications/launch` - Launch any application
- `POST /api/applications/revizto-exporter` - Launch Revizto Data Exporter

### Script Runner
- `POST /api/scripts/run-health-importer` - Run health importer on folder

---

## File Locations

### Backend
- `backend/app.py` - Lines 1400+ (new endpoints)

### Frontend API
- `frontend/src/api/fileBrowser.ts` - New file (147 lines)

### Frontend Components
- `frontend/src/components/dataImports/ACCDataImportPanel.tsx` - Browse button added
- `frontend/src/components/dataImports/ReviztoImportPanel.tsx` - Launch + Browse added
- `frontend/src/components/dataImports/RevitHealthPanel.tsx` - Full import section added

---

## Troubleshooting

### "Revizto Data Exporter not found"
**Solution**: Install Revizto or check installation path
- Default paths checked:
  - `C:\Program Files\Revizto\DataExporter\ReviztoDataExporter.exe`
  - `C:\Program Files (x86)\Revizto\DataExporter\ReviztoDataExporter.exe`
  - `C:\Revizto\DataExporter\ReviztoDataExporter.exe`

### File dialog doesn't open
**Solution**: Check Flask backend is running and tkinter is available
```powershell
python -c "import tkinter; print('OK')"
```

### Import fails
**Solution**: Check folder contains valid JSON files
```powershell
# Check folder contents
dir "C:\Exports\RevitHealth\Project1"
```

---

## Example Workflows

### Workflow 1: Import ACC ZIP File
```
1. Navigate to Data Imports
2. Select project from dropdown
3. Go to "ACC Data Import" tab
4. Select "ZIP" from Type dropdown
5. Click "Browse"
6. Navigate to C:\Data\ACC\
7. Select issues.zip
8. Click "Open"
9. Path shows: C:\Data\ACC\issues.zip
10. Click "Import Data"
11. Wait for "records imported successfully!"
```

### Workflow 2: Extract Revizto Data
```
1. Navigate to Data Imports
2. Go to "Revizto Import" tab
3. Click "Launch Revizto Data Exporter"
4. Revizto app opens
5. In Revizto: Export issues data
6. Back in React app: Click "Start Extraction"
7. In dialog: Click "Browse"
8. Select C:\Exports\Revizto\Project1
9. Click "Select Folder"
10. Click "Start"
11. Extraction runs → shows Run ID
```

### Workflow 3: Import Revit Health Data
```
1. Navigate to Data Imports
2. Select project
3. Go to "Revit Health" tab
4. In "Import Health Check Data" section:
5. Click "Browse"
6. Select C:\Exports\RevitHealth\Project1
7. Click "Select Folder"
8. Click "Run Health Importer"
9. Wait (shows "Importing...")
10. Success! Shows "Import completed successfully in 12.34s"
11. Health Files table refreshes automatically
```

---

## Testing Commands

### Test Backend Endpoints
```powershell
# Test file browser
curl -X POST http://localhost:5000/api/file-browser/select-file `
  -H "Content-Type: application/json" `
  -d '{"title":"Test"}'

# Test folder browser
curl -X POST http://localhost:5000/api/file-browser/select-folder `
  -H "Content-Type: application/json" `
  -d '{"title":"Test"}'

# Test Revizto launcher
curl -X POST http://localhost:5000/api/applications/revizto-exporter

# Test health importer
curl -X POST http://localhost:5000/api/scripts/run-health-importer `
  -H "Content-Type: application/json" `
  -d '{"folder_path":"C:\\Exports\\RevitHealth\\Test","project_id":1}'
```

---

## Key Features

✅ **Native File Dialogs** - OS-native file/folder pickers  
✅ **File Type Filtering** - Auto-filter by CSV/ZIP  
✅ **Auto-Path Population** - Selected paths fill inputs  
✅ **External App Launch** - Launch Revizto Data Exporter  
✅ **Script Execution** - Run Python importers from UI  
✅ **Progress Tracking** - Shows execution time  
✅ **Auto-Refresh** - Tables update after import  
✅ **Error Handling** - Clear error messages  
✅ **Cross-Platform** - Works on Windows/macOS/Linux  

---

## Status Indicators

| Component | Browse Files | Browse Folders | Launch App | Run Script |
|-----------|-------------|----------------|------------|------------|
| ACC Data Import | ✅ | - | - | - |
| Revizto Import | - | ✅ | ✅ | - |
| Revit Health | - | ✅ | - | ✅ |

---

## Next Steps

1. **Test** with real project data
2. **Verify** all file paths and folder structures
3. **Configure** Revizto installation path if needed
4. **Add** to user documentation
5. **Train** users on new workflows

---

**Version**: 1.0  
**Last Updated**: October 13, 2025  
**Status**: Production Ready ✅
