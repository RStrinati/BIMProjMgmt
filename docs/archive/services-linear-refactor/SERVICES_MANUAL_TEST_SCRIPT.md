# Services Linear UI Refactor - Manual Testing Script

**Duration**: 15-20 minutes  
**Tester**: QA / Developer  
**Environment**: Local dev server (`http://localhost:5173`)

---

## PRE-TEST SETUP (5 minutes)

### 1. Verify Code Changes
```bash
# Check that ProjectDetailPage.tsx has correct import
grep "ProjectServicesTab_Linear" frontend/src/pages/ProjectDetailPage.tsx
# Expected output: import { ProjectServicesTab } from '@/components/ProjectServicesTab_Linear';
```

### 2. Build Frontend
```bash
cd frontend
npm run build
# Expected: Build succeeds, no TypeScript errors
# Exit code 0
```

### 3. Start Dev Server
```bash
npm run dev
# Expected: "Local: http://localhost:5173"
# Services tab should be accessible
```

### 4. Open in Browser
```
http://localhost:5173/projects/1
```
(or any project ID that has services data)

---

## TEST SCRIPT (15 minutes)

### TEST 1: Visual Normalization (2 minutes)
**Goal**: Verify summary strip and flat list render correctly

**Steps**:
1. Navigate to Services tab
2. Look at top of tab:
   - [ ] See horizontal strip with "Total Contract Sum", "Fee Billed", "Remaining Fee"
   - [ ] Strip shows currency values (e.g., "$100,000", "$80,000")
   - [ ] Progress bar is thin (4px) and subtle
   - [ ] NO heavy Paper cards (no elevation/shadow)

3. Look at services table:
   - [ ] Each service is ONE ROW (not expandable)
   - [ ] Row shows: Service Code | Phase | Status | Agreed Fee | Billed | Remaining | Progress %
   - [ ] Row background is subtle (light hover on mouse over)
   - [ ] NO expand/collapse icons
   - [ ] Status shows as colored chip (Planned=blue, In Progress=orange, Completed=green)

**Pass Criteria**:
- [ ] Summary strip visible and correctly formatted
- [ ] Services list is flat (no expand/collapse)
- [ ] No heavy cards or elevation
- [ ] All 7 columns visible in row

**Fail Criteria**:
- ❌ Old expand/collapse icons visible
- ❌ Heavy Paper cards with elevation
- ❌ Columns missing or misaligned

---

### TEST 2: Drawer Opens on Row Click (1 minute)
**Goal**: Verify clicking service row opens right-side drawer

**Steps**:
1. Click on first service row (anywhere except action buttons)
2. Observe:
   - [ ] Drawer slides in from right side
   - [ ] Drawer is 480-600px wide
   - [ ] Drawer has smooth shadow
   - [ ] Service code and name visible at top
   - [ ] Drawer has close button (X) at top right

3. Click somewhere else on page (outside drawer):
   - [ ] Drawer remains open
   - [ ] Clicking another service row updates drawer content

4. Click close button (X):
   - [ ] Drawer slides out
   - [ ] Returns to normal list view

**Pass Criteria**:
- [ ] Drawer opens smoothly on row click
- [ ] Drawer displays correct service information
- [ ] Close button works

**Fail Criteria**:
- ❌ Drawer doesn't open
- ❌ Drawer shows wrong service
- ❌ Close button doesn't work

---

### TEST 3: Drawer Finance Section (1 minute)
**Goal**: Verify drawer shows billing information correctly

**Steps**:
1. With drawer open, scroll down to see Finance section:
   - [ ] Shows "Agreed Fee: $X,XXX.XX"
   - [ ] Shows "Billed: $X,XXX.XX"
   - [ ] Shows "Remaining: $X,XXX.XX"
   - [ ] Shows progress bar with percentage

2. Verify formatting:
   - [ ] Currency values have commas (e.g., "$10,000" not "$10000")
   - [ ] Progress bar is thin and proportional
   - [ ] Percentage label is visible (e.g., "80%")

**Pass Criteria**:
- [ ] All finance fields visible
- [ ] Values are correctly formatted
- [ ] Progress bar displays percentage

**Fail Criteria**:
- ❌ Finance section missing
- ❌ Values not formatted
- ❌ Progress bar not showing

---

### TEST 4: Drawer Tabs - Reviews (2 minutes)
**Goal**: Verify Reviews tab shows review cycles

**Steps**:
1. With drawer open, locate tabs:
   - [ ] See "Reviews" and "Items" tabs at bottom of drawer
   - [ ] Reviews tab is selected by default (darker background)

2. Look at Reviews section:
   - [ ] If service has reviews, table shows: Cycle # | Planned Date | Status | Actions
   - [ ] If service has no reviews, shows empty state
   - [ ] Each review row has Edit and Delete buttons

3. Scroll in drawer if needed:
   - [ ] Reviews section scrolls smoothly
   - [ ] Action buttons remain visible and clickable

**Pass Criteria**:
- [ ] Reviews tab visible and selected
- [ ] Review data displays correctly
- [ ] No scrolling issues

**Fail Criteria**:
- ❌ Reviews tab missing
- ❌ Reviews don't load or show error
- ❌ Tab switching broken

---

### TEST 5: Drawer Tabs - Items (2 minutes)
**Goal**: Verify Items tab shows service items

**Steps**:
1. Click "Items" tab in drawer
2. Verify Items section shows:
   - [ ] If service has items, table shows: Type | Title | Status | Actions
   - [ ] If service has no items, shows empty state
   - [ ] Each item row has Edit and Delete buttons

3. Click back to Reviews tab:
   - [ ] Reviews tab content appears again
   - [ ] Tab switching is smooth

4. Repeat switching tabs 3 times:
   - [ ] Switching is always responsive (no lag)
   - [ ] Data is correct each time

**Pass Criteria**:
- [ ] Items tab works and displays data
- [ ] Tab switching is smooth and responsive
- [ ] Data is correct after switching

**Fail Criteria**:
- ❌ Items tab doesn't show data
- ❌ Tab switching is slow or broken
- ❌ Wrong data shown in tabs

---

### TEST 6: Event Handling - Row Buttons Don't Open Drawer (2 minutes)
**Goal**: Verify Edit/Delete buttons on row don't open drawer

**Steps**:
1. Close drawer (if open)
2. Find a service row
3. Click Edit button (pencil icon) on the row:
   - [ ] Edit dialog opens (showing service form)
   - [ ] Drawer does NOT open
   - [ ] Dialog is focused (not drawer)

4. Click Cancel on dialog to close it:
   - [ ] Dialog closes
   - [ ] No drawer open in background

5. Click Delete button (trash icon) on the row:
   - [ ] Delete confirmation dialog appears
   - [ ] Drawer does NOT open

6. Click Cancel on confirmation:
   - [ ] Dialog closes

7. Click row itself (not buttons):
   - [ ] Drawer opens

**Pass Criteria**:
- [ ] Edit button opens dialog (not drawer)
- [ ] Delete button opens confirmation (not drawer)
- [ ] Row click opens drawer

**Fail Criteria**:
- ❌ Edit button opens drawer instead of dialog
- ❌ Delete button opens drawer instead of confirmation
- ❌ Multiple windows open at once

---

### TEST 7: CRUD - Create Service (2 minutes)
**Goal**: Verify creating new service works

**Steps**:
1. Click [Add Service] button at top of Services tab
2. Verify dialog opens with form fields
3. Fill in form:
   - [ ] Service Code: "TEST-01"
   - [ ] Service Name: "Test Service"
   - [ ] Phase: Select a phase
   - [ ] Status: Select "Planned"
   - [ ] Agreed Fee: 5000

4. Click Save:
   - [ ] Dialog closes
   - [ ] New service appears in list
   - [ ] Summary strip updates (total increases)
   - [ ] New row has all fields filled

**Pass Criteria**:
- [ ] Service created successfully
- [ ] List refreshes with new service
- [ ] No errors in console

**Fail Criteria**:
- ❌ Form doesn't open
- ❌ Save fails or shows error
- ❌ New service not in list

---

### TEST 8: CRUD - Edit Service (2 minutes)
**Goal**: Verify editing service works

**Steps**:
1. Open drawer for any service
2. Click Edit button in drawer footer:
   - [ ] Edit dialog opens with service fields prefilled

3. Change one field:
   - [ ] Example: Change Status from "Planned" to "In Progress"

4. Click Save:
   - [ ] Dialog closes
   - [ ] Drawer updates showing new status
   - [ ] Row in list also updates (status chip changes color)

**Pass Criteria**:
- [ ] Edit dialog opens and is prefilled
- [ ] Changes are saved
- [ ] UI updates immediately

**Fail Criteria**:
- ❌ Edit button doesn't work
- ❌ Changes not saved
- ❌ UI doesn't update

---

### TEST 9: CRUD - Add Review (2 minutes)
**Goal**: Verify adding review via drawer works

**Steps**:
1. Open drawer for any service
2. Make sure you're on Reviews tab
3. Look for [+ Add] or [Add Review] button
4. Click it:
   - [ ] Review dialog opens with form fields

5. Fill in form:
   - [ ] Cycle: 1
   - [ ] Planned Date: Pick a date (e.g., 1/25/2026)
   - [ ] Status: Planned or Completed

6. Click Save:
   - [ ] Dialog closes
   - [ ] New review appears in drawer Reviews table immediately
   - [ ] No need to refresh

**Pass Criteria**:
- [ ] Review created successfully
- [ ] Appears in drawer immediately

**Fail Criteria**:
- ❌ Add button doesn't work
- ❌ Save fails or shows error
- ❌ Review doesn't appear

---

### TEST 10: CRUD - Add Item (2 minutes)
**Goal**: Verify adding item via drawer works

**Steps**:
1. Open drawer for any service
2. Click Items tab
3. Look for [+ Add] or [Add Item] button
4. Click it:
   - [ ] Item dialog opens with form fields

5. Fill in form:
   - [ ] Type: Select "Report" or similar
   - [ ] Title: "Test Item"
   - [ ] Status: Pending

6. Click Save:
   - [ ] Dialog closes
   - [ ] New item appears in drawer Items table immediately

**Pass Criteria**:
- [ ] Item created successfully
- [ ] Appears in drawer immediately

**Fail Criteria**:
- ❌ Add button doesn't work
- ❌ Save fails
- ❌ Item doesn't appear

---

### TEST 11: Event Handling - Switching Services (1 minute)
**Goal**: Verify switching between services updates drawer correctly

**Steps**:
1. Open drawer for service #1
2. Note service name and reviews/items
3. Click on service #2 row:
   - [ ] Drawer updates immediately
   - [ ] Service #2 name appears
   - [ ] Reviews/Items for service #2 show (if any)
   - [ ] Finance numbers update

4. Switch back to service #1:
   - [ ] Drawer shows service #1 data again
   - [ ] No stale data from #2

**Pass Criteria**:
- [ ] Drawer updates smoothly when switching services
- [ ] Data is correct for each service

**Fail Criteria**:
- ❌ Drawer shows wrong service
- ❌ Data doesn't update
- ❌ Stale data visible

---

### TEST 12: Template Apply (1 minute)
**Goal**: Verify template apply still works

**Steps**:
1. Click [Apply Template] button at top of Services tab
2. Verify dialog opens with template options
3. Select a template:
   - [ ] Dialog shows "Create new services" option

4. Click Apply:
   - [ ] Services created from template
   - [ ] List refreshes with new services
   - [ ] Summary strip updates

**Pass Criteria**:
- [ ] Template dialog opens
- [ ] Services created successfully
- [ ] List updates

**Fail Criteria**:
- ❌ Apply button doesn't work
- ❌ Template fails or shows error
- ❌ List doesn't update

---

## EDGE CASE TESTING (Optional, 5 minutes)

### Edge Case 1: Service with No Reviews/Items
**Steps**:
1. Find a service with no reviews or items
2. Open drawer
3. Switch to Reviews tab:
   - [ ] Shows "No reviews" or empty state
4. Switch to Items tab:
   - [ ] Shows "No items" or empty state

**Expected**: Graceful empty state, no errors

---

### Edge Case 2: Multiple Drawer Opens
**Steps**:
1. Rapidly click different services (3-4 times)
2. Observe:
   - [ ] Drawer always shows current selected service
   - [ ] No duplicate drawers open
   - [ ] Data loads correctly each time

**Expected**: Only one drawer, data is correct

---

### Edge Case 3: Long Service Name
**Steps**:
1. Find service with very long name (or create one)
2. Open drawer:
   - [ ] Service name doesn't overflow
   - [ ] Text wraps or truncates appropriately

3. Check row in list:
   - [ ] Long name displays correctly

**Expected**: UI handles long text gracefully

---

### Edge Case 4: Pagination
**Steps**:
1. If more than 10 services exist, look for pagination
2. Click next page:
   - [ ] New services load
   - [ ] Drawer closes
   - [ ] Summary still visible

3. Click previous:
   - [ ] Original services show

**Expected**: Pagination works, drawer closes on page change

---

## BROWSER CONSOLE VERIFICATION (1 minute)

**Steps**:
1. Open DevTools: F12
2. Click Console tab
3. Perform all tests above
4. Check for errors:
   - [ ] No red errors (✕ icon)
   - [ ] No TypeScript errors
   - [ ] No import errors

**Expected**: Console is clean, no errors related to Services

---

## PERFORMANCE VERIFICATION (Optional, 2 minutes)

**Steps**:
1. Open DevTools: F12
2. Click Performance tab (or Network tab)
3. Navigate to Services tab:
   - [ ] Tab loads in < 500ms
   - [ ] Summary strip renders immediately

4. Click service row:
   - [ ] Drawer opens in < 200ms
   - [ ] Reviews/Items fetch and display in < 500ms total

**Expected**: Performance is responsive, no lag

---

## FINAL CHECKLIST

### All Tests Passed?
- [ ] TEST 1: Visual Normalization ✅
- [ ] TEST 2: Drawer Opens on Row Click ✅
- [ ] TEST 3: Drawer Finance Section ✅
- [ ] TEST 4: Drawer Tabs - Reviews ✅
- [ ] TEST 5: Drawer Tabs - Items ✅
- [ ] TEST 6: Event Handling (Row Buttons) ✅
- [ ] TEST 7: CRUD - Create Service ✅
- [ ] TEST 8: CRUD - Edit Service ✅
- [ ] TEST 9: CRUD - Add Review ✅
- [ ] TEST 10: CRUD - Add Item ✅
- [ ] TEST 11: Event Handling (Switching Services) ✅
- [ ] TEST 12: Template Apply ✅

### Edge Cases?
- [ ] Service with No Reviews/Items ✅
- [ ] Multiple Drawer Opens ✅
- [ ] Long Service Names ✅
- [ ] Pagination ✅

### Console Clean?
- [ ] No errors ✅
- [ ] No TypeScript errors ✅
- [ ] No import/module errors ✅

### Performance?
- [ ] Services tab loads fast (< 500ms) ✅
- [ ] Drawer opens fast (< 200ms) ✅
- [ ] Data loads fast (< 500ms) ✅

---

## SIGN-OFF

**Tester Name**: ___________________  
**Date/Time**: ___________________  
**Browser**: ___________________  
**OS**: ___________________  

**All Tests Passed**: [ ] Yes [ ] No

**Issues Found**: (If any)
```
1. _________________________________________________
2. _________________________________________________
3. _________________________________________________
```

**Recommendation**:
- [ ] APPROVED FOR DEPLOYMENT
- [ ] ISSUES FOUND - DO NOT DEPLOY (see above)

---

## NEXT STEPS (If All Passed)

1. ✅ Manual testing complete
2. ✅ Run automated tests: `npm run test:e2e`
3. ✅ Commit to feature branch
4. ✅ Create Pull Request
5. ✅ Merge to main
6. ✅ Deploy to production

**Deployment Time**: < 5 minutes  
**Rollback Time**: < 5 minutes (if issues)

---

**Questions?** Refer to:
- Architecture: `docs/SERVICES_REFACTOR_LINEAR_UI.md`
- Go/No-Go Gates: `SERVICES_GONOG_VALIDATION.md`
- Deployment: `SERVICES_DEPLOYMENT_READINESS.md`

