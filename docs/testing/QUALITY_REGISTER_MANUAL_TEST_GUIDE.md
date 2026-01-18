# Quality Register Phase 1D+2+3 - Manual Testing Guide

## Prerequisites
1. Backend running: `cd backend && python app.py`
2. Frontend running: `cd frontend && npm run dev`
3. Database migrations applied (done in implementation)

## Phase D: Quick Sanity Checks

### Test 1: Quality Tab Loads
1. Navigate to any project workspace (e.g., `/projects/1`)
2. Click the **Quality** tab
3. ✅ Table should load with 12 columns:
   - ABV, Model Name, Company, Discipline, Description, BIM Contact
   - Folder Path, ACC (icon), ACC Date, Revizto (icon), Revizto Date, Notes

### Test 2: Empty State
1. If no models exist in register:
   - ✅ Should show "No models registered. Click 'Add Model' to create the first entry."

### Test 3: Add Model (Additive Workflow)
1. Click **"Add Model"** button
2. ✅ Side panel opens immediately on the right
3. ✅ New empty row appears in table
4. Reload page → ✅ Empty row persists

### Test 4: Side Panel Opens on Row Click
1. Click any row in the table
2. ✅ Side panel opens showing "Model Details"
3. ✅ Four tabs visible: Register, Mapping, Health, Activity
4. ✅ Close button (X) closes panel

### Test 5: Edit Fields in Register Tab
1. Open side panel for a model
2. In **Register** tab, fill in:
   - ABV: `AR`
   - Model Name: `TEST-MODEL-001`
   - Company: `Test Company`
   - Discipline: `Architecture`
   - Description: `Test model description`
   - BIM Contact: `john.smith@example.com`
   - Notes: `This is a test note`
3. Click **"Save Changes"**
4. ✅ Table row updates immediately with new values

### Test 6: Notes Update Workflow
1. Open side panel for a model
2. Update **Notes** field: "Updated notes at [timestamp]"
3. Save changes
4. Close panel
5. ✅ Notes column in table shows truncated version (first 50 chars)

### Test 7: Mapping Tab - Add Alias
1. Open side panel
2. Switch to **Mapping** tab
3. Click **"Add Alias"** button
4. Fill form:
   - Match Type: `contains`
   - Pattern: `TEST-PATTERN-*`
5. Click **Add**
6. ✅ Alias appears in aliases list
7. ✅ Mapping status chip may update

### Test 8: Activity Tab - View History
1. After making any edit (e.g., update notes)
2. Open side panel → **Activity** tab
3. ✅ Should show at least one history entry:
   - Change type (INSERT, UPDATE)
   - Timestamp
   - Changed fields (if UPDATE)

### Test 9: Phase 3 - Service Linkage
1. Open side panel → **Register** tab
2. Scroll to **"Service & Delivery (Phase 3)"** section
3. ✅ Fields visible:
   - Service ID (number input)
   - Review Cycle ID (number input)
   - Expected Delivery Date (date picker)
   - Actual Delivery Date (date picker)
   - Delivery Status (dropdown: Pending, On Track, At Risk, Delivered, Late)
4. Fill in values and save
5. ✅ Values persist after save

### Test 10: Health Tab Placeholder
1. Open side panel → **Health** tab
2. ✅ Shows placeholder sections:
   - Validation Status (chip)
   - Freshness Status (chip)
   - Message: "Health metrics will be populated from RevitHealthCheckDB when available"

## Expected Behavior Summary

### ✅ Additive Model
- Rows created empty and filled incrementally
- No forced forms or wizards
- Everything is optional

### ✅ Linear UI
- Dense table on left
- Right side panel for details
- No blocking modals

### ✅ Data Persistence
- All edits save via PATCH endpoint
- Table refreshes after save
- History tracked automatically

### ✅ Query Invalidation
- After PATCH: refetch detail + invalidate register list
- After Add Model: invalidate register list (new row appears)
- After Add Alias: refetch detail (aliases list updates)

## Common Issues to Check

❌ **Side panel doesn't open**: Check that row has `expected_model_id` property
❌ **Save doesn't update table**: Check query key consistency (`quality-register-phase1d`)
❌ **Empty rows don't appear**: Check createEmptyModel returns `{ id: number }`
❌ **History doesn't show**: Check database trigger is installed and working
❌ **Type errors**: Ensure all API methods use proper typed responses

## API Endpoints Used
- `GET /api/projects/:id/quality/register?mode=phase1d` - Register list
- `GET /api/projects/:id/quality/models/:expectedModelId` - Model detail
- `PATCH /api/projects/:id/quality/expected-models/:expectedModelId` - Update model
- `POST /api/projects/:id/quality/expected-models` - Create empty model
- `GET /api/projects/:id/quality/models/:expectedModelId/history` - Audit trail
- `POST /api/projects/:id/quality/expected-model-aliases` - Add alias

## Next Steps After Manual Testing
1. Run Playwright E2E tests: `npx playwright test quality-register-phase1d`
2. If tests fail, check browser console for errors
3. Verify backend logs for API errors
4. Check database state with `tools/check_quality_tables.py`
