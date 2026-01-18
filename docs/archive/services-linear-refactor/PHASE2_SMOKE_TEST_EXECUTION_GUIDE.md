# 🧪 PHASE 2: SMOKE TEST EXECUTION GUIDE

**Date**: January 16, 2026  
**Duration**: ~30 minutes  
**Prepared For**: Services Linear UI Refactor Validation  
**Status**: ✅ READY TO EXECUTE

---

## BUILD VERIFICATION ✅

**Build Status**: PASSED
```
✅ Generated production artifacts
✅ dist/index.html present
✅ dist/assets/ folder present
✅ Total size: ~1.6MB (uncompressed), ~457KB (gzipped)
✅ No TypeScript errors in new components
✅ Build completed in 20.17 seconds
```

**Artifacts Location**: `frontend/dist/`

---

## PRE-TEST CHECKLIST

- [ ] Backend API running (`python app.py` or `flask run`)
- [ ] Staging environment ready OR local dev server ready
- [ ] Chrome/Chromium installed (for Playwright)
- [ ] Network connectivity verified
- [ ] Test database contains sample projects with services

---

## SMOKE TEST EXECUTION (30 MINUTES)

### Segment 1: Manual Drawer Testing (10 minutes)

**Test 1.1: Open Services List**
```
Steps:
1. Navigate to Projects page
2. Select a project (e.g., "Sample Construction Project")
3. Click "Services" tab
4. Observe: Linear list of services displayed

Expected: ✅
- Services list rendered
- No console errors
- Material-UI components load correctly
- Row layout is horizontal (linear, not cards)
```

**Test 1.2: Open Service Drawer**
```
Steps:
1. From Services tab, click on any service row
2. Drawer slides in from right side
3. Observe: Service details populate

Expected: ✅
- Drawer opens smoothly (animation visible)
- Service name, description visible
- No stale data from previous service
- Close button (X) visible in drawer header
```

**Test 1.3: Service Drawer Sections**
```
Steps:
1. In drawer, scroll through sections:
   - Service Details (name, type, status)
   - Reviews (if applicable)
   - Items (if applicable)
   - Billing (if applicable)
2. Observe: Content loads correctly

Expected: ✅
- All sections render without errors
- Lazy loading: Reviews/Items load on demand (API call)
- No duplicate data
- No missing fields
```

**Test 1.4: Close Drawer**
```
Steps:
1. Click drawer close button (X)
2. Or click outside drawer area
3. Observe: Drawer closes smoothly

Expected: ✅
- Drawer closes with animation
- Services list remains visible
- No orphaned drawer state
```

**Test 1.5: Switch Between Services**
```
Steps:
1. Open drawer for Service A
2. WITHOUT closing, click another service in list
3. Drawer updates to show Service B
4. Repeat 2-3 times

Expected: ✅
- Drawer content switches immediately
- No stale data from Service A
- New API calls made (verify in Network tab)
- Performance smooth (no lag)
```

---

### Segment 2: CRUD Operations Testing (12 minutes)

**Test 2.1: Add Review to Service**
```
Steps:
1. Open service drawer
2. Click "Add Review" button (in Reviews section)
3. Fill form:
   - Title: "Weekly Progress"
   - Start date: Today
   - End date: +7 days
   - Status: "Scheduled"
4. Click Save

Expected: ✅
- Review appears in drawer
- No console errors
- Form clears after save
- New review visible in list immediately
```

**Test 2.2: Edit Review**
```
Steps:
1. In drawer, find added review
2. Click edit icon
3. Modify title to "Weekly Progress - Updated"
4. Click Save

Expected: ✅
- Review title updates
- Change reflected immediately
- No console errors
- Drawer stays open
```

**Test 2.3: Delete Review**
```
Steps:
1. In drawer, click delete icon on review
2. Confirm deletion in dialog

Expected: ✅
- Review removed from list
- Drawer refreshes
- No console errors
- Database reflects deletion (refresh drawer confirms)
```

**Test 2.4: Add Service Item**
```
Steps:
1. In drawer, go to Items section
2. Click "Add Item" button
3. Fill form:
   - Item name: "Weekly Report"
   - Item type: "Report"
   - Status: "Pending"
4. Click Save

Expected: ✅
- Item appears in drawer
- Form clears
- Item visible in Items list
- No console errors
```

**Test 2.5: Edit Service Item**
```
Steps:
1. Click edit on added item
2. Change status to "Delivered"
3. Click Save

Expected: ✅
- Item updated
- Change reflects immediately
- No console errors
```

**Test 2.6: Delete Service Item**
```
Steps:
1. Click delete icon on item
2. Confirm deletion

Expected: ✅
- Item removed
- Drawer refreshes
- No console errors
```

---

### Segment 3: Performance & Edge Cases (5 minutes)

**Test 3.1: Lazy Loading Verification**
```
Steps:
1. Open browser DevTools (F12)
2. Go to Network tab
3. Open service drawer
4. Observe: No immediate API calls for reviews/items
5. Click Reviews section
6. Observe: API call made at that moment

Expected: ✅
- Reviews/Items API calls only when sections opened
- No unnecessary data fetching on drawer open
- Efficient network usage (< 3 seconds per section)
```

**Test 3.2: Performance Check**
```
Steps:
1. Open drawer for 10 different services
2. Measure time for each open
3. Check for memory leaks (no constant growth)
4. Observe: Should be consistent speed

Expected: ✅
- Each drawer open < 500ms
- No slowdown after multiple opens
- Smooth animations (60 FPS)
- No memory leaks (DevTools heap)
```

**Test 3.3: Console Errors Check**
```
Steps:
1. Keep DevTools open (Console tab)
2. Execute Tests 1.1 - 3.2 above
3. Review entire console output

Expected: ✅
- NO red error messages
- NO exceptions thrown
- Warnings OK (deprecation warnings acceptable)
- All API calls successful (200-201 status)
```

**Test 3.4: Template Application (if applicable)**
```
Steps:
1. Open service drawer
2. Click "Apply Template" or similar
3. Verify: Template items/reviews load correctly

Expected: ✅
- Template content loads
- No console errors
- Correct associations
```

---

### Segment 4: Regression Spot Checks (3 minutes)

**Test 4.1: Other Tabs Unaffected**
```
Steps:
1. Navigate away from Services tab to:
   - Projects tab
   - Reviews tab
   - Issues tab (if exists)
2. Verify each tab functions normally

Expected: ✅
- No errors in other tabs
- Navigation works smoothly
- No performance degradation
- Refactor did not break other features
```

**Test 4.2: Project Selection Unaffected**
```
Steps:
1. Switch to different project
2. Navigate back to Services tab
3. Verify correct services load

Expected: ✅
- Services match selected project
- No cross-project data mixing
- Correct filtering applied
```

**Test 4.3: Authorization/Permissions**
```
Steps:
1. Try to edit/delete with test user
2. Verify: Only authorized operations work

Expected: ✅
- Permissions enforced
- No unauthorized access
- Error messages clear (if denied)
```

---

## AUTOMATED PLAYWRIGHT TESTS

After manual testing, run automated tests:

```bash
cd c:\Users\RicoStrinati\Documents\research\BIMProjMngmt\frontend

# Run our new Services drawer test
npm run test:e2e -- tests/e2e/project-workspace-v2-services-drawer.spec.ts

# Or run all E2E tests
npm run test:e2e

# Run with UI for visibility
npm run test:e2e -- --ui

# Run in debug mode if needed
npm run test:e2e -- --debug
```

**Expected Output**:
```
✅ 12+ tests passed
✅ Drawer open/close verified
✅ CRUD operations validated
✅ Service switching confirmed
✅ Performance benchmarks met
✅ No timeouts or failures
```

---

## GO/NO-GO DECISION CRITERIA

### ✅ GO TO PRODUCTION IF

**All of the following are TRUE**:

- [ ] **No Console Errors**: Zero red error messages during entire test sequence
- [ ] **Drawer Behaves Correctly**: 
  - Opens smoothly on service click
  - Closes without orphaned state
  - Switches between services without stale data
  - No data corruption observed
- [ ] **CRUD Operations Work**:
  - Add review/item succeeds
  - Edit updates correctly
  - Delete removes completely
  - Data persisted (verified by refresh)
- [ ] **Performance Acceptable**:
  - Drawer opens < 500ms consistently
  - No memory leaks (heap stable)
  - Animations smooth (60 FPS)
  - Lazy loading works (no unnecessary API calls)
- [ ] **Playwright Tests Pass**:
  - All tests pass (0 failures)
  - No timeout issues
  - Performance benchmarks met
- [ ] **No Regressions**:
  - Other tabs function normally
  - Project switching works
  - Authorization intact
  - Cross-project data clean

**Decision**: ✅ **GO - DEPLOY TO PRODUCTION**

---

### ❌ NO-GO (STOP) IF

**Any of the following are TRUE**:

- [ ] Console shows red errors (TypeScript runtime errors)
- [ ] Drawer fails to open or close
- [ ] Stale data visible when switching services
- [ ] CRUD operations fail or don't persist
- [ ] Performance degradation (slow opens, memory leaks)
- [ ] Playwright tests fail (any failure = no-go)
- [ ] Other UI tabs are broken
- [ ] Authorization bypassed or errors

**Decision**: ❌ **NO-GO - DO NOT DEPLOY**

**Action**: 
1. Document specific error
2. Create issue in backlog
3. Rollback changes (revert deploy)
4. Fix issue locally
5. Restart smoke test

---

## DOCUMENTATION TO PRESERVE

After go/no-go decision, document:

1. **Test Execution Log** (attach screenshots of console, drawer, etc.)
2. **Performance Metrics** (drawer open time, memory usage)
3. **Issues Found** (list any bugs, even minor)
4. **Sign-Off** (tester name, date, decision)
5. **Deployment Approval** (manager/lead approval)

**Template**:
```
SMOKE TEST RESULTS
==================
Date: [Date]
Tester: [Name]
Version: f40c975 (Services Linear Refactor)

Manual Tests: ✅ All Passed / ❌ Failed
Playwright Tests: ✅ All Passed / ❌ Failed

Decision: ✅ GO / ❌ NO-GO

Issues Found: [List any bugs]
Performance: [Drawer open times, memory usage]
Sign-Off: [Tester signature/approval]
```

---

## STAGING ENVIRONMENT PREP

**Before deploying dist/ to staging**:

1. **Backup Current Staging**:
   ```bash
   cp -r /staging/frontend /staging/frontend.backup
   ```

2. **Deploy New Build**:
   ```bash
   cp -r frontend/dist/* /staging/frontend/
   ```

3. **Verify Staging Deployment**:
   ```
   - Open staging URL
   - Services tab loads
   - Drawer functions
   - Backend API connects
   ```

4. **Smoke Test in Staging**:
   - Repeat manual tests above in staging environment
   - Verify against production data sample
   - Check cross-browser (Chrome, Firefox, Edge)

---

## PRODUCTION DEPLOYMENT CHECKLIST

- [ ] Staging smoke test completed (GO decision made)
- [ ] All issues resolved or documented
- [ ] Performance verified acceptable
- [ ] Team approval obtained
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured
- [ ] Deployment window scheduled
- [ ] User communication ready
- [ ] Release notes prepared
- [ ] Post-deployment validation plan ready

---

## MONITORING POST-DEPLOYMENT

After production deployment, monitor for:

1. **Error Tracking**: Sentry/Rollbar for frontend errors
2. **Performance**: Loader time, drawer open time
3. **User Activity**: Services tab usage, drawer interactions
4. **Database**: Review/Item creation rates normal
5. **API Load**: Backend responding normally

**SLA**: 
- Drawer open time: < 500ms
- Error rate: < 0.1%
- Availability: > 99.5%

---

## ROLLBACK PROCEDURE

If production deployment has issues:

```bash
# 1. Identify issue
# 2. Stop serving new code
# 3. Restore previous version
git revert f40c975
npm run build
# 4. Deploy previous version
# 5. Notify team
# 6. Create incident report
# 7. Fix issue locally
# 8. Schedule retry
```

---

## TEST ENVIRONMENT REQUIREMENTS

**Frontend**:
- Node.js v18+
- npm 9+
- Playwright 1.49+

**Backend**:
- Python 3.12+
- Flask running
- Database connection active

**Browser**:
- Chrome/Chromium (latest)
- DevTools available
- Console access

**Network**:
- Staging URL accessible
- Backend API responding
- Network latency < 100ms

---

## NEXT STEPS

1. ✅ Complete manual smoke test (Segment 1-4)
2. ✅ Run Playwright automated tests
3. ✅ Document results per template above
4. ✅ Make go/no-go decision
5. ✅ If GO: Proceed to production deployment
6. ✅ If NO-GO: Fix issues, restart smoke test

---

**Smoke Test Guide Version**: 2.0  
**Last Updated**: January 16, 2026  
**Status**: READY FOR EXECUTION

**🚀 BEGIN SMOKE TEST EXECUTION → START WITH SEGMENT 1 ABOVE**

