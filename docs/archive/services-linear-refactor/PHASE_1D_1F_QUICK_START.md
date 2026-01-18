# Phase 1D + 1F Quick Start Guide

## What Was Implemented

### UI Changes
1. **Quality Register Tab** - Now shows **expected models** by default (not observed)
2. **Register View** - Expected models in a linear list with columns: Status, Model, Discipline, Observed File, Last Version, Validation, Control, Mapping
3. **Unmatched View** - Shows unmapped observed files from Revit health checks
4. **Add Expected Model Modal** - Create new expected models on the fly
5. **Map Observed File Modal** - Link observed files to expected models via pattern matching

### API Updates
- `getExpectedRegister()` - Fetch expected-first register
- `createExpectedModel()` - Create expected model
- `createExpectedModelAlias()` - Create mapping alias
- Plus supporting list functions

### E2E Tests
- 8 Playwright tests covering seeding, UI rendering, modal workflows, and user interactions
- All tests use deterministic seeding via REST API
- Tests gracefully handle projects with no data

---

## Quick Verification

### 1. Check Files Exist
```powershell
# API client
Test-Path "c:\Users\RicoStrinati\Documents\research\BIMProjMngmt\frontend\src\api\quality.ts"

# Types
Test-Path "c:\Users\RicoStrinati\Documents\research\BIMProjMngmt\frontend\src\types\api.ts"

# Component
Test-Path "c:\Users\RicoStrinati\Documents\research\BIMProjMngmt\frontend\src\components\ProjectManagement\ProjectQualityRegisterTab.tsx"

# Tests
Test-Path "c:\Users\RicoStrinati\Documents\research\BIMProjMngmt\tests\e2e\project-quality-register-expected.spec.ts"
```

### 2. Run Backend
```bash
cd backend
python app.py
# Verify: http://localhost:5000/api/projects/2/quality/register?mode=expected returns 200
```

### 3. Run Frontend
```bash
cd frontend
npm run dev
# Navigate to http://localhost:5173/projects → open any project → Quality tab
```

### 4. Test UI
- Should see **Register** and **Unmatched** toggle buttons
- Register view should show expected models (or empty state)
- Click "Add Expected Model" → modal should appear
- Click "Map" button (if in Unmatched view) → mapping modal should appear

### 5. Run E2E Tests
```bash
# From project root
npx playwright test tests/e2e/project-quality-register-expected.spec.ts --headed

# Or specific test
npx playwright test -g "should display Register and Unmatched"

# With custom URLs
$env:BASE_URL="http://localhost:3000"; $env:API_BASE_URL="http://localhost:5001"; npx playwright test
```

---

## Key Files

| Path | Purpose |
|------|---------|
| `frontend/src/api/quality.ts` | API client for expected register |
| `frontend/src/types/api.ts` | TypeScript types for expected mode |
| `frontend/src/components/ProjectManagement/ProjectQualityRegisterTab.tsx` | Main UI component |
| `tests/e2e/project-quality-register-expected.spec.ts` | E2E tests |

---

## Configuration

### Environment Variables (E2E Tests)
```bash
BASE_URL=http://localhost:5173          # Frontend
API_BASE_URL=http://localhost:5000      # Backend
```

### Playwright Config
- See `playwright.config.ts` in root
- Default browser: chromium
- Test timeout: 30 seconds per test
- Retry on failure: 0 (set to 1 for CI)

---

## Troubleshooting

### Backend endpoints not found
- Ensure migration was run: `python check_schema.py --update-constants`
- Check `ExpectedModels` and `ExpectedModelAliases` tables exist
- Verify Flask app is running on port 5000

### Modal not opening
- Check browser console for errors
- Verify component is rendering (search for "Add Expected Model" button)
- Check React Query cache keys in DevTools

### Tests failing
- Ensure project 2 exists in database
- Check API is running and accessible
- Run with `--headed` flag to see what's happening
- Check logs: `logs/app.log` (backend), `logs/frontend.log` (frontend)

### No data in Register view
- Create an expected model first via "Add Expected Model" button
- Or seed via API:
  ```bash
  curl -X POST http://localhost:5000/api/projects/2/quality/expected-models \
    -H "Content-Type: application/json" \
    -d '{"expected_model_key":"STR_M.rvt","display_name":"Structural","discipline":"Structural"}'
  ```

---

## Implementation Checklist

- [x] Backend tables exist
- [x] Backend endpoints working
- [x] API client created with new functions
- [x] Types defined for expected mode
- [x] Register view implemented
- [x] Unmatched view implemented
- [x] Add Expected Model modal
- [x] Map Observed File modal
- [x] Detail drawer
- [x] Query invalidation on mutations
- [x] E2E tests with seeding
- [x] Tests for all major workflows
- [x] Documentation

---

## Next Actions

1. **Manual Testing**: Load a project, go to Quality tab, verify Register view loads
2. **E2E Testing**: Run Playwright tests with `--headed` to visually verify
3. **Code Review**: Check for any TypeScript errors or lint issues
4. **Integration**: Ensure backend seeding/test data matches expected schema
5. **Deployment**: Add to deployment pipeline once validated

---

## Support

For issues or questions:
1. Check console logs (browser DevTools F12)
2. Review error messages in modal dialogs
3. Check `logs/app.log` and `logs/warehouse.log`
4. Run tests with `--debug` flag for step-by-step execution
