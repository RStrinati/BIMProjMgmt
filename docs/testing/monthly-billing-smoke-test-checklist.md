# Monthly Billing Smoke Test Checklist

**Purpose:** Manual validation of monthly billing features with real database  
**Duration:** 1-2 hours  
**Status:** ⏳ NOT STARTED  
**Tester:** _________________  
**Date:** _________________

## Pre-Test Setup

### Environment Setup
- [ ] Backend running: `python backend/app.py`
- [ ] Frontend running: `npm run dev` in `frontend/`
- [ ] Database accessible: SQL Server `.\SQLEXPRESS`
- [ ] Test project exists with services and deliverables
- [ ] Logs directory writable: `logs/app.log`

### Test Data Requirements
- [ ] Project with at least 5 service reviews (deliverables)
- [ ] Mix of statuses: planned, in-progress, completed
- [ ] Mix of due dates: past month, current month, future months
- [ ] At least 1 invoice batch created for current month
- [ ] At least 1 deliverable already billed (is_billed = true)

### Recommended Test Project
```sql
-- Check existing projects
SELECT project_id, project_name, status 
FROM Projects 
WHERE status = 'active';

-- Check project has deliverables
SELECT COUNT(*) 
FROM ServiceReviews 
WHERE project_id = 1;  -- Replace with your project_id

-- Verify deliverable diversity
SELECT 
    status, 
    COUNT(*) as count,
    SUM(CASE WHEN invoice_batch_id IS NULL THEN 1 ELSE 0 END) as unbatched_count
FROM ServiceReviews 
WHERE project_id = 1
GROUP BY status;
```

## Test Scenarios

### 1. Invoice Month Auto-Calculation

#### Scenario 1.1: Change due_date updates invoice_month_auto
- [ ] Navigate to project workspace → Deliverables tab
- [ ] Find deliverable with no invoice_month_override (shows auto month)
- [ ] Note current invoice_month_final: _________________
- [ ] Click due_date cell, change to new month (e.g., 2026-02-15)
- [ ] Press Enter to save
- [ ] **Expected:** invoice_month_final updates to new month (2026-02)
- [ ] **Expected:** Snackbar shows "Invoice month auto-calculated to 2026-02 (due_date changed)"
- [ ] Check logs: `grep "invoice_month_auto" logs/app.log | tail -5`
- [ ] **Expected:** Log entry shows: "ServiceReview {id}: invoice_month_auto {old} → {new}"

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Notes:** _______________________________________________________________

#### Scenario 1.2: Null due_date results in null invoice_month_auto
- [ ] Find deliverable with due_date set
- [ ] Clear due_date (set to empty)
- [ ] Press Enter to save
- [ ] **Expected:** invoice_month_final becomes null (or shows empty)
- [ ] **Expected:** Log entry shows: "ServiceReview {id}: due_date cleared → invoice_month_auto = NULL"

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Notes:** _______________________________________________________________

### 2. Invoice Month Override Preservation

#### Scenario 2.1: Set override, then change due_date
- [ ] Find deliverable with due_date in current month
- [ ] Click invoice_month_final cell
- [ ] Set override to next month (e.g., if current is 2026-01, set to 2026-02)
- [ ] Press Enter to save
- [ ] **Expected:** invoice_month_final shows override month (2026-02)
- [ ] Now change due_date to different month (e.g., 2026-03-15)
- [ ] Press Enter to save
- [ ] **Expected:** invoice_month_final STILL shows override (2026-02)
- [ ] **Expected:** Snackbar shows "auto-calculated to 2026-03 but override (2026-02) was preserved"
- [ ] Check logs: `grep "invoice_month_override preserved" logs/app.log | tail -3`
- [ ] **Expected:** Log entry confirms override preservation

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Notes:** _______________________________________________________________

#### Scenario 2.2: Clear override falls back to auto
- [ ] Find deliverable with invoice_month_override set
- [ ] Click invoice_month_final cell
- [ ] Clear the month input (set to empty)
- [ ] Press Enter to save
- [ ] **Expected:** invoice_month_final reverts to invoice_month_auto (based on due_date)
- [ ] Check logs: `grep "invoice_month_override cleared" logs/app.log | tail -3`
- [ ] **Expected:** Log entry shows: "override cleared → using auto {month}"

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Notes:** _______________________________________________________________

### 3. Filters

#### Scenario 3.1: Due this month filter
- [ ] Navigate to Deliverables tab
- [ ] Click "Due this month" filter toggle
- [ ] **Expected:** Shows only deliverables with invoice_month_final = current month
- [ ] Verify by checking a few invoice_month_final values in table
- [ ] Turn off filter
- [ ] **Expected:** All deliverables visible again

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Filtered count:** _______________  
**Notes:** _______________________________________________________________

#### Scenario 3.2: Unbatched filter
- [ ] Click "Unbatched" filter toggle
- [ ] **Expected:** Shows only deliverables with invoice_batch_id = null
- [ ] Verify by checking batch column (should show "—" or empty)
- [ ] Turn off filter

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Filtered count:** _______________  
**Notes:** _______________________________________________________________

#### Scenario 3.3: Ready to invoice filter
- [ ] Click "Ready to invoice" filter toggle
- [ ] **Expected:** Shows only deliverables with status = completed AND is_billed = false
- [ ] Verify status column shows only "completed"
- [ ] Verify billed column shows only "No" or unchecked
- [ ] Turn off filter

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Filtered count:** _______________  
**Notes:** _______________________________________________________________

#### Scenario 3.4: Combined filters (AND logic)
- [ ] Turn ON "Due this month" filter
- [ ] Turn ON "Unbatched" filter
- [ ] Turn ON "Ready to invoice" filter
- [ ] **Expected:** Shows deliverables matching ALL three criteria
- [ ] Verify: invoice_month_final = current month AND no batch AND completed + unbilled
- [ ] Count should be <= each individual filter count

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Filtered count:** _______________  
**Notes:** _______________________________________________________________

### 4. Batch Workflows

#### Scenario 4.1: Batch dropdown disabled without invoice_month
- [ ] Find deliverable with invoice_month_final = null (or clear due_date to make it null)
- [ ] Click batch dropdown
- [ ] **Expected:** Dropdown is disabled
- [ ] Hover over dropdown
- [ ] **Expected:** Tooltip shows "Set invoice month first"

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Notes:** _______________________________________________________________

#### Scenario 4.2: Batch dropdown filtered by invoice_month
- [ ] Find deliverable with invoice_month_final = current month
- [ ] Click batch dropdown
- [ ] **Expected:** Dropdown shows only batches with invoice_month = current month
- [ ] If batches exist for other months, verify they are NOT shown
- [ ] Assign deliverable to batch
- [ ] **Expected:** Batch column updates with batch name

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Batches shown:** _______________  
**Notes:** _______________________________________________________________

#### Scenario 4.3: Helper text when no batches exist
- [ ] Find deliverable with invoice_month_final = future month (e.g., 3 months out)
- [ ] Click batch dropdown
- [ ] **Expected:** Dropdown shows "No batches for [month] - create one"
- [ ] Click "Create new batch" option
- [ ] **Expected:** Batch creation dialog opens
- [ ] **Expected:** invoice_month pre-filled with deliverable's invoice_month_final

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Notes:** _______________________________________________________________

#### Scenario 4.4: Create new batch via dropdown
- [ ] Find deliverable with invoice_month_final set
- [ ] Click batch dropdown → "Create new batch"
- [ ] **Expected:** Dialog opens with invoice_month pre-filled
- [ ] Fill in title: "Test Batch [current month]"
- [ ] Add notes: "Smoke test batch"
- [ ] Click "Create"
- [ ] **Expected:** Batch created and assigned to deliverable
- [ ] **Expected:** Deliverable's batch column shows new batch name

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Batch created:** _______________  
**Notes:** _______________________________________________________________

### 5. Overview Tab Metrics

#### Scenario 5.1: Invoice pipeline aggregation
- [ ] Navigate to Overview tab
- [ ] Locate "Invoice Pipeline" widget
- [ ] **Expected:** Shows months with deliverable counts and total amounts
- [ ] Verify: Current month row shows count matching "Due this month" filter
- [ ] Click on a month row
- [ ] **Expected:** Navigates to Deliverables tab with month filter applied

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Current month count:** _______________  
**Current month amount:** _______________  
**Notes:** _______________________________________________________________

#### Scenario 5.2: Ready this month metric
- [ ] In Overview tab, locate "Ready this month" metric
- [ ] **Expected:** Shows count and amount of completed + unbilled deliverables for current month
- [ ] Note count: _______________
- [ ] Navigate to Deliverables tab
- [ ] Apply filters: "Due this month" + "Ready to invoice"
- [ ] **Expected:** Count matches "Ready this month" metric

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Metric count:** _______________  
**Filter count:** _______________  
**Notes:** _______________________________________________________________

#### Scenario 5.3: Unbatched risk metric
- [ ] In Overview tab, locate "Unbatched risk" metric
- [ ] **Expected:** Shows count and amount of unbatched deliverables due current month
- [ ] **Expected:** Warning icon visible if count > 0
- [ ] Note count: _______________
- [ ] Navigate to Deliverables tab
- [ ] Apply filters: "Due this month" + "Unbatched"
- [ ] **Expected:** Count matches "Unbatched risk" metric

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Metric count:** _______________  
**Filter count:** _______________  
**Notes:** _______________________________________________________________

### 6. Edge Cases

#### Scenario 6.1: Past month due_date
- [ ] Find deliverable
- [ ] Set due_date to past month (e.g., 2025-12-15)
- [ ] **Expected:** invoice_month_auto = 2025-12
- [ ] **Expected:** invoice_month_final = 2025-12 (if no override)
- [ ] Verify no errors or warnings in console
- [ ] Check logs for any issues

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Notes:** _______________________________________________________________

#### Scenario 6.2: Override to past month
- [ ] Find deliverable with current/future due_date
- [ ] Set invoice_month_override to past month (e.g., 2025-11)
- [ ] **Expected:** invoice_month_final = 2025-11 (override accepted)
- [ ] Verify batch dropdown shows batches for 2025-11 (if any exist)
- [ ] Document: Should system prevent past month overrides? (Design decision)

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Notes:** _______________________________________________________________

#### Scenario 6.3: Batch with mixed months (should not happen)
- [ ] Create batch for current month
- [ ] Assign deliverable with invoice_month_final = next month
- [ ] **Expected:** Assignment should fail OR batch dropdown should not show batch
- [ ] Verify data integrity: batch.invoice_month matches deliverable.invoice_month_final

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Notes:** _______________________________________________________________

#### Scenario 6.4: Multiple simultaneous due_date changes
- [ ] Open project workspace in two browser tabs
- [ ] In Tab 1: Change due_date of deliverable A
- [ ] In Tab 2: Change due_date of deliverable A to different month
- [ ] **Expected:** Both updates succeed (last write wins)
- [ ] Check logs: Both updates logged
- [ ] Verify invoice_month_final reflects last update

**Result:** ✅ PASS / ❌ FAIL / ⚠️ PARTIAL  
**Notes:** _______________________________________________________________

## Log Verification

### Required Log Entries

Check `logs/app.log` for these message patterns:

- [ ] `ServiceReview {id}: due_date changed → recalculating invoice_month_auto`
- [ ] `ServiceReview {id}: invoice_month_auto {old} → {new}`
- [ ] `ServiceReview {id}: invoice_month_override preserved: {month}`
- [ ] `ServiceReview {id}: invoice_month_override cleared → using auto {month}`

### Log Analysis Commands
```bash
# Filter invoice month logs
grep "invoice_month" logs/app.log | tail -20

# Check for errors
grep "ERROR" logs/app.log | tail -10

# Check for warnings
grep "WARNING" logs/app.log | tail -10
```

**Log Review Result:** ✅ PASS / ❌ FAIL  
**Notes:** _______________________________________________________________

## Database Verification

### Post-Test Data Integrity Checks

```sql
-- Check invoice_month_final matches COALESCE(override, auto)
SELECT 
    review_id,
    invoice_month_override,
    invoice_month_auto,
    invoice_month_final,
    CASE 
        WHEN invoice_month_final = COALESCE(invoice_month_override, invoice_month_auto) 
        THEN 'OK' 
        ELSE 'MISMATCH' 
    END as integrity_check
FROM ServiceReviews
WHERE project_id = 1;
```

- [ ] All rows show `integrity_check = 'OK'`
- [ ] No orphaned invoice_month_override (override set but auto is null)
- [ ] invoice_month_auto matches due_date month (YYYY-MM)

**Database Integrity Result:** ✅ PASS / ❌ FAIL  
**Mismatches found:** _______________  
**Notes:** _______________________________________________________________

## Performance Checks

### Page Load Times
- [ ] Overview tab load time: _____ seconds (should be < 2s)
- [ ] Deliverables tab load time: _____ seconds (should be < 3s)
- [ ] Filter application response: _____ ms (should be < 500ms)
- [ ] Inline edit save response: _____ ms (should be < 1s)

### Database Query Performance
```sql
-- Check view query time
SET STATISTICS TIME ON;
SELECT * FROM vw_invoice_pipeline_by_project_month WHERE project_id = 1;
SET STATISTICS TIME OFF;
```

- [ ] Query execution time: _____ ms (should be < 100ms)

**Performance Result:** ✅ PASS / ❌ FAIL  
**Notes:** _______________________________________________________________

## Browser Compatibility (Optional)

Test in multiple browsers:
- [ ] Chrome/Edge (Chromium): ✅ / ❌
- [ ] Firefox: ✅ / ❌
- [ ] Safari (if available): ✅ / ❌

**Browser Issues:** _______________________________________________________________

## Test Summary

### Pass/Fail Count
- Total scenarios: 19
- Passed: _____
- Failed: _____
- Partial: _____
- Not tested: _____

### Critical Issues Found
1. _______________________________________________________________
2. _______________________________________________________________
3. _______________________________________________________________

### Non-Critical Issues Found
1. _______________________________________________________________
2. _______________________________________________________________
3. _______________________________________________________________

### Recommendations
1. _______________________________________________________________
2. _______________________________________________________________
3. _______________________________________________________________

## Sign-Off

**Tester Name:** _________________  
**Tester Signature:** _________________  
**Date:** _________________  

**Status:** ✅ APPROVED FOR PRODUCTION / ❌ REQUIRES FIXES / ⚠️ CONDITIONAL APPROVAL  

**Conditions (if applicable):** _______________________________________________________________

---

## Next Steps After Testing

### If All Tests Pass
1. Deploy to production environment
2. Monitor logs for first 24 hours
3. Check for user feedback on snackbar notifications
4. Review "unbatched risk" metric usage in analytics

### If Tests Fail
1. Document failure details in bug tracker
2. Prioritize issues (critical vs. non-critical)
3. Fix issues and re-run smoke test
4. Do not deploy until all critical issues resolved

### Post-Deployment Monitoring
- [ ] Check `logs/app.log` for invoice month change entries (daily for 1 week)
- [ ] Monitor database integrity checks (weekly for 1 month)
- [ ] Gather user feedback on new features (snackbar, unbatched metric)
- [ ] Review analytics for filter usage patterns
- [ ] Check performance metrics (page load, query execution)

## Related Documentation
- [Monthly Billing Discovery](./monthly_billing_discovery.md)
- [Monthly Billing Implementation Summary](./monthly-billing-implementation-summary.md)
- [Monthly Billing Test Suite Reference](../testing/monthly-billing-test-suite.md)
