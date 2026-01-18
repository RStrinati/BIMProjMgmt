# Quality Register - Quick Start Guide

**Last Updated**: January 16, 2026

## One-Minute Setup

### 1. Start Backend
```bash
cd backend
python app.py
```
Endpoint ready: `http://localhost:5000/api/projects/:projectId/quality/register`

### 2. Start Frontend
```bash
cd frontend
npm run dev
```
App ready: `http://localhost:5173`

### 3. Test Quality Tab
1. Navigate to http://localhost:5173/projects
2. Click any project
3. Click **Quality** tab
4. Verify table loads

---

## Core Flows

### View Quality Register
```
/projects/:id/workspace → Click "Quality" tab → Linear table displays
```

**Expected**: Table with model names, freshness status (CURRENT/DUE_SOON/OUT_OF_DATE), validation status

### Toggle Filters
```
Click "Attention" or "All models" button → Row count changes
```

**Expected**: 
- Attention: Shows only models with issues (out of date / low validation / unmapped)
- All: Shows all models for project

### View Model Details
```
Click any table row → Right drawer opens
```

**Expected**: Drawer shows model metadata (name, discipline, last version date, status chips)

---

## Data Sources

**Models come from**:
- `tblRvtProjHealth` (RevitHealthCheckDB)
- `tblControlModels` (ProjectManagement)
- `ReviewSchedule` (ProjectManagement)

**No data import needed** – uses existing tables.

---

## Freshness Status Explained

| Status | Meaning | Color |
|--------|---------|-------|
| CURRENT | Last version ≥ 7 days before next review | 🟢 Green |
| DUE_SOON | Last version within 7 days of next review | 🟠 Orange |
| OUT_OF_DATE | Last version before next review date | 🔴 Red |
| UNKNOWN | Next review or version date missing | ⚫ Gray |

---

## Playwright E2E Tests

### Run All Quality Tests
```bash
npx playwright test tests/e2e/project-quality-register.spec.ts
```

### Run Specific Test
```bash
npx playwright test tests/e2e/project-quality-register.spec.ts -g "toggle between Attention"
```

### Interactive UI Mode
```bash
npx playwright test tests/e2e/project-quality-register.spec.ts --ui
```

### Expected Results
- ✅ All tests pass
- ✅ No console errors
- ✅ Table renders with data
- ✅ Filters work correctly
- ✅ Drawer opens on row click

---

## API Reference

### Endpoint
```
GET /api/projects/:projectId/quality/register
```

### Query Parameters
```
?page=1
&page_size=50
&sort_by=lastVersionDate
&sort_dir=desc
&filter_attention=false
```

### Response
```json
{
  "rows": [
    {
      "modelKey": "STR_M.rvt",
      "modelName": "STR_M.rvt",
      "discipline": "Structural",
      "company": "ABC Corp",
      "lastVersionDate": "2025-01-14T10:30:00Z",
      "source": "REVIT_HEALTH",
      "isControlModel": true,
      "freshnessStatus": "CURRENT",
      "validationOverall": "PASS",
      "primaryServiceId": null,
      "mappingStatus": "UNMAPPED"
    }
  ],
  "page": 1,
  "page_size": 50,
  "total": 42,
  "attention_count": 3
}
```

---

## Troubleshooting

### Empty table / no data
- [ ] Verify project has Revit models in `vw_LatestRvtFiles`
- [ ] Check database connection: `/api/health/schema`
- [ ] Check backend logs: `logs/app.log`

### Slow loading
- [ ] May need index on `vw_LatestRvtFiles.pm_project_id`
- [ ] Try reducing `page_size` parameter
- [ ] Check database performance

### Errors in console
- [ ] Clear browser cache (Ctrl+Shift+Delete)
- [ ] Restart frontend dev server
- [ ] Check CORS settings in backend/app.py

---

## Files

**Key Files to Review**:
- [docs/QUALITY_REGISTER_AUDIT.md](QUALITY_REGISTER_AUDIT.md) – Architecture decisions
- [docs/QUALITY_REGISTER_IMPLEMENTATION_SUMMARY.md](QUALITY_REGISTER_IMPLEMENTATION_SUMMARY.md) – Full implementation details
- [frontend/src/components/ProjectManagement/ProjectQualityRegisterTab.tsx](../frontend/src/components/ProjectManagement/ProjectQualityRegisterTab.tsx) – UI component
- [backend/app.py](../backend/app.py#L5381) – Backend endpoint
- [database.py](../database.py#L2693) – Database query logic
- [tests/e2e/project-quality-register.spec.ts](../tests/e2e/project-quality-register.spec.ts) – E2E tests

---

## Next Steps

- [ ] Run Playwright tests to verify core flows
- [ ] Test with actual project data
- [ ] Verify freshness computation is correct
- [ ] Check performance with large datasets
- [ ] Plan Phase 2 features (service mapping, exports, etc.)

---

## Quick Links

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:5000
- **API Docs**: http://localhost:5000/api/docs (if available)
- **Project Workspace**: http://localhost:5173/projects/:id/workspace?tab=Quality
