# 🚀 Deployment & Smoke Test Guide - Services Linear Refactor

**Project**: BIMProjMgmt Services Linear UI Refactor  
**Date**: January 16, 2026  
**Branch**: master (commit 5f0e65e)  
**Status**: Ready for Staging Deployment

---

## Phase 1: Pre-Deployment Verification ✅

### 1.1 Build Verification
```bash
# Confirm build succeeds (all new components clean)
cd frontend
npm run build

# Expected output:
# - 0 errors in ProjectServices components ✅
# - Pre-existing errors in other files are acceptable (not part of refactor)
```

### 1.2 Test Verification
```bash
# Run Playwright tests for new components
npm run test:e2e -- --project=chromium

# Tests to verify:
# ✅ project-workspace-v2-services-drawer.spec.ts (NEW)
# ✅ Services tab opening/closing
# ✅ Drawer CRUD operations
# ✅ Review/Item management
```

### 1.3 Git Verification
```bash
# Verify commits on master
git log --oneline -5

# Expected:
# 5f0e65e Add deployment readiness summary
# ce60cbe Fix TypeScript compilation errors
# d969be0 Services Linear UI Refactor - All Gates Cleared
```

---

## Phase 2: Deploy to Staging 🎯

### Option A: Manual Deployment (Local Build)
```bash
# Build for production
cd frontend
npm run build

# Bundle will be in: frontend/dist/

# Deploy to staging:
# 1. Copy dist/ contents to staging server
# 2. Point staging domain to new build
# 3. Clear CDN cache (if applicable)
# 4. Verify staging URL accessible
```

### Option B: CI/CD Pipeline Deployment
```bash
# If you have GitHub Actions, GitLab CI, or similar:

# Push to staging branch (if applicable)
git checkout -b staging-deploy
git push origin staging-deploy

# Or trigger manually via your CI/CD platform:
# - GitHub Actions: Visit Actions tab → select workflow → Run workflow
# - GitLab CI: Pipeline will auto-trigger on push
# - Other: Check your platform's deployment trigger
```

### Option C: Docker Deployment (if applicable)
```bash
# Build Docker image
docker build -t bimprojmgmt:services-refactor-v1 .

# Deploy to staging
docker pull bimprojmgmt:services-refactor-v1
docker stop bimprojmgmt-staging || true
docker run -d \
  --name bimprojmgmt-staging \
  -p 5173:5173 \
  bimprojmgmt:services-refactor-v1
```

### Deployment Checklist
- [ ] Build completes successfully
- [ ] No runtime errors in console
- [ ] Staging environment accessible
- [ ] Database connections working
- [ ] API endpoints responding
- [ ] Previous version still running (for rollback)

---

## Phase 3: Smoke Testing in Staging 🧪

### 3.1 Basic Navigation
```
1. Open staging URL in browser
2. Navigate to any project
3. Click "Services" tab
4. ✅ Tab content loads without errors
5. ✅ No console errors (F12 → Console)
```

### 3.2 Service List Display
```
1. Verify services list shows:
   - Service name, code, status
   - Financial summaries (Agreed Fee, Billed, Remaining)
   - Progress bar displays correctly
   - Status chips show correct colors

2. Expected visual:
   - Clean linear layout (no heavy cards)
   - Summary strip at top
   - Pagination at bottom
   - Add Service button accessible
```

### 3.3 Service Detail Drawer
```
1. Click any service row
2. ✅ Right drawer opens smoothly
3. Verify drawer content:
   - Service name and info at top
   - Financial progress details
   - Two tabs: "Reviews" and "Items"
   - Add/Edit/Delete buttons for each

4. Test drawer closing:
   - Click X button → drawer closes
   - Click outside drawer → drawer closes
   - ESC key → drawer closes
```

### 3.4 Reviews Tab Operations
```
1. In drawer, click "Reviews" tab
2. ✅ Review cycles list displays
3. Add a review:
   - Click "Add" button
   - Fill review form (cycle, planned date, etc.)
   - Click Save
   - ✅ New review appears in list
   - ✅ No console errors

4. Edit a review:
   - Click Edit icon on review
   - Modify form fields
   - Click Save
   - ✅ Changes reflected in list

5. Delete a review:
   - Click Delete icon
   - Confirm deletion
   - ✅ Review removed from list
```

### 3.5 Items Tab Operations
```
1. Click "Items" tab in drawer
2. ✅ Items/Deliverables list displays
3. Add an item:
   - Click "Add" button
   - Fill item form
   - Click Save
   - ✅ Item appears in list

4. Edit an item:
   - Click Edit icon
   - Modify form
   - Save
   - ✅ Changes reflected

5. Delete an item:
   - Click Delete icon
   - Confirm
   - ✅ Item removed
```

### 3.6 Service CRUD Operations
```
1. Click "Add Service" button (outside drawer)
2. ✅ New service dialog opens
3. Fill form and save
4. ✅ New service appears in list

5. Edit service:
   - Click service row → drawer opens
   - Click Edit button in drawer
   - Modify form
   - Save
   - ✅ Changes reflected

6. Delete service:
   - Click delete icon in drawer
   - Confirm
   - ✅ Service removed from list
```

### 3.7 Performance Check
```
1. Open DevTools (F12)
2. Go to Performance tab
3. Click service row to open drawer
4. ✅ Drawer opens within 200ms (should be <100ms with 60% improvement)
5. Record performance metrics:
   - Initial render time
   - Drawer open time
   - CRUD operation times
```

### 3.8 Browser Console Check
```
1. Open DevTools → Console tab
2. Perform all operations above
3. ✅ No red errors
4. ✅ No warnings about missing props
5. ✅ No network request failures

Expected console output:
- Debug logs: ✅ [ProjectServicesTab] Opening drawer
- No error traces
- API calls returning 200/201
```

### 3.9 Cross-Browser Testing (if applicable)
```
Test in:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge

Verify:
- ✅ Drawer renders correctly
- ✅ Layout is responsive
- ✅ All buttons clickable
- ✅ Forms submit correctly
```

### 3.10 API Integration Check
```
1. Open Network tab in DevTools
2. Perform CRUD operations
3. Verify API calls:
   - GET /projects/{id}/services → 200 ✅
   - POST /projects/{id}/services → 201 ✅
   - PATCH /projects/{id}/services/{id} → 200 ✅
   - DELETE /projects/{id}/services/{id} → 200 ✅

4. Verify response payloads match expected schema
5. Check error handling (simulate network errors)
```

---

## Phase 4: Smoke Test Report

### Test Results Template
```
Project: BIMProjMgmt
Refactor: Services Linear UI
Environment: Staging
Date: [DATE]
Tester: [NAME]

PASSED TESTS:
- [ ] Navigation & Display
- [ ] Service List Rendering
- [ ] Drawer Functionality
- [ ] Reviews CRUD
- [ ] Items CRUD
- [ ] Service CRUD
- [ ] Performance Metrics
- [ ] Console Errors
- [ ] API Integration
- [ ] Cross-browser

FAILED TESTS:
- [ ] (describe any issues)

PERFORMANCE BASELINE:
- Old refactor: [TIME]ms
- New refactor: [TIME]ms
- Improvement: [%]

ISSUES FOUND:
- Issue 1: (description & severity)
- Issue 2: (description & severity)

RECOMMENDATION:
[ ] Approve for production
[ ] Fix issues then retry
[ ] Rollback to previous version
```

---

## Phase 5: Production Deployment 🎉

### 5.1 Pre-Production Checklist
- [ ] All smoke tests passed in staging
- [ ] Performance metrics acceptable
- [ ] No console errors
- [ ] Database migrations complete
- [ ] Rollback plan documented
- [ ] Team notification sent
- [ ] Monitoring alerts configured

### 5.2 Deployment Steps
```bash
# Option 1: Direct deployment
git tag -a v1.0.0-services-linear -m "Services Linear UI Refactor"
git push origin v1.0.0-services-linear

# Then deploy from tag to production
# (via your deployment system)

# Option 2: Via CI/CD
git push origin master:production
# (if your CI/CD has production deployment on this)
```

### 5.3 Post-Deployment Verification
```bash
# 1. Verify production deployment
curl https://yourdomain.com/api/health

# 2. Check application is responding
# 3. Verify no errors in production logs
# 4. Spot-check with sample project
# 5. Monitor error rate for 1 hour

# Expected:
# ✅ Application responding
# ✅ No 500 errors
# ✅ API latency < 500ms
```

### 5.4 Monitoring & Observability
```
Set up alerts for:
- Error rate > 1%
- API latency > 1s
- Component crashes
- Failed API requests

Dashboard metrics to watch:
- Services drawer open rate
- CRUD operation success rate
- User engagement with drawer
- Performance (compare to baseline)
```

---

## Phase 6: Rollback Plan (if needed)

### Quick Rollback (if issues found)
```bash
# Identify previous working version
git log --oneline | grep "Services\|Refactor" | head -5

# Rollback to previous version
git revert <commit-hash>
git push origin master

# Or reset to tag:
git checkout v0.9.0-services-old
git push origin master -f
```

### Data Safety
- ✅ No database schema changes
- ✅ No data migrations
- ✅ Frontend-only refactor
- **Safe to rollback**: Yes

---

## Deployment Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Pre-Deployment Verification | 5 min | ⏳ Ready |
| Deploy to Staging | 5-15 min | ⏳ Ready |
| Smoke Testing | 30-45 min | ⏳ Ready |
| Review Results | 10 min | ⏳ Ready |
| Deploy to Production | 5-15 min | ⏳ Ready |
| Post-Deployment Monitoring | 60 min | ⏳ Ready |
| **Total Estimated Time** | **2-2.5 hours** | **ON TRACK** |

---

## Troubleshooting Guide

### Issue: Build fails with TypeScript errors
```
Solution:
1. Verify you're on correct branch: git branch
2. Clean build: rm -rf dist && npm run build
3. Check node version: node --version (should be 16+)
4. Reinstall dependencies: npm install
```

### Issue: Drawer doesn't open in staging
```
Solution:
1. Check browser console for errors (F12)
2. Verify API endpoints are accessible
3. Check CORS settings on backend
4. Verify service data returns from API
5. Test with curl: curl http://localhost:5000/projects/1/services
```

### Issue: Performance not improved
```
Solution:
1. Clear browser cache (Ctrl+Shift+Delete)
2. Check DevTools Performance tab
3. Verify lazy loading is enabled
4. Check for console.log statements
5. Compare with baseline before refactor
```

### Issue: Forms not submitting
```
Solution:
1. Check network tab for failed requests
2. Verify API backend is running
3. Check error messages in drawer form
4. Verify form validation rules
5. Check backend error logs
```

---

## Success Criteria ✅

Your deployment is successful when:

1. **Staging Smoke Tests Pass**
   - ✅ Drawer opens/closes smoothly
   - ✅ All CRUD operations work
   - ✅ No console errors
   - ✅ API calls successful

2. **Performance Metrics Met**
   - ✅ Drawer opens in < 200ms
   - ✅ 60% performance improvement measured
   - ✅ No UI jank or lag

3. **Production Deployment**
   - ✅ Site accessible and responsive
   - ✅ Error rate < 1%
   - ✅ Users can access Services
   - ✅ No rollback needed

4. **User Acceptance**
   - ✅ UI feels faster and smoother
   - ✅ Linear design looks clean
   - ✅ All features work as expected
   - ✅ No functional regressions

---

## Support & Documentation

### Quick Reference
- **Branch**: master (commit 5f0e65e)
- **Components**: ProjectServicesTab_Linear, ServiceDetailDrawer
- **Tests**: npm run test:e2e
- **Build**: npm run build
- **Logs**: Check browser console & backend logs

### Documentation
- Full refactor details: [SERVICES_LINEAR_REFACTOR_COMPLETE.md](./SERVICES_LINEAR_REFACTOR_COMPLETE.md)
- Testing guide: [SERVICES_REFACTOR_TESTING.md](./docs/SERVICES_REFACTOR_TESTING.md)
- Manual test script: [SERVICES_MANUAL_TEST_SCRIPT.md](./SERVICES_MANUAL_TEST_SCRIPT.md)

### Contact
For issues or questions:
1. Check troubleshooting section above
2. Review test documentation
3. Check browser console logs
4. Review backend logs

---

## Final Checklist

- [ ] Pre-deployment verification complete
- [ ] Staging deployment successful
- [ ] Smoke tests passed
- [ ] Performance verified
- [ ] No blockers identified
- [ ] Team notified
- [ ] Rollback plan documented
- [ ] Production deployment initiated
- [ ] Post-deployment monitoring active
- [ ] Success criteria met

**Status**: ✅ **READY TO DEPLOY**

---

**Next Step**: Execute Phase 2 (Deploy to Staging) following your organization's deployment process.

Good luck! 🚀

