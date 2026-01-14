# 🐛 Troubleshooting & Error Resolution

**Solutions for known issues, bugs, and error messages**

This directory contains documented fixes for problems that have been encountered and resolved.

## 📚 Fixes by Category

### Review Management Issues
Issues related to review creation, updating, and deletion:
- **[DELETE_ALL_REVIEWS_FIX.md](./DELETE_ALL_REVIEWS_FIX.md)** - Resolution for delete all reviews issue
- **[REVIEW_STATUS_UPDATE_FIX.md](./REVIEW_STATUS_UPDATE_FIX.md)** - Review status not updating properly

### Template & Loading Issues
Problems with template loading and initialization:
- **[TEMPLATE_LOADING_FIX.md](./TEMPLATE_LOADING_FIX.md)** - Templates not loading in UI

### Data Import Issues
Problems during ACC, Revit health, or other data imports:
- **[ACC_IMPORT_405_FIX.md](./ACC_IMPORT_405_FIX.md)** - HTTP 405 error during ACC import
- **[MISSING_PROJECTS_FIX.md](./MISSING_PROJECTS_FIX.md)** - Projects missing from ACC import results

### External Integration Issues
Problems with Revizto, ACC, or other integrations:
- **[REVIZTO_ISSUES_MISSING_DIAGNOSTIC.md](./REVIZTO_ISSUES_MISSING_DIAGNOSTIC.md)** - Revizto issues not appearing in dashboard
- **[DATE_BASED_REVIEW_REFRESH.md](./DATE_BASED_REVIEW_REFRESH.md)** - Date-based refresh showing incorrect data

### Frontend Issues
React application problems and display issues:
- **[REACT_FRONTEND_PROJECT_LOADING_FIX.md](./REACT_FRONTEND_PROJECT_LOADING_FIX.md)** - Frontend failing to load projects

---

## 🎯 How to Use This Directory

### When You Encounter an Error

1. **Read the error message carefully** - Note:
   - Exact error text
   - Component or page affected
   - When it occurs (creation, update, import, etc.)

2. **Search this directory** for matching keywords:
   - Issue type (DELETE, LOADING, IMPORT, etc.)
   - Component name (REVIEW, TEMPLATE, PROJECT, etc.)
   - Error code (405, timeout, etc.)

3. **Read the fix document** for:
   - Problem description and root cause
   - Step-by-step solution
   - Prevention tips
   - Related issues

4. **Try the solution** and report if it doesn't work

---

## 🔍 Error Quick Reference

| Error | Symptom | Document |
|-------|---------|----------|
| **HTTP 405** | ACC import fails with "Method Not Allowed" | [ACC_IMPORT_405_FIX.md](./ACC_IMPORT_405_FIX.md) |
| **Projects not found** | ACC import completes but projects don't appear | [MISSING_PROJECTS_FIX.md](./MISSING_PROJECTS_FIX.md) |
| **Status not changing** | Review status update button has no effect | [REVIEW_STATUS_UPDATE_FIX.md](./REVIEW_STATUS_UPDATE_FIX.md) |
| **Delete button broken** | Delete all reviews doesn't work | [DELETE_ALL_REVIEWS_FIX.md](./DELETE_ALL_REVIEWS_FIX.md) |
| **Templates missing** | Service templates won't load in dialog | [TEMPLATE_LOADING_FIX.md](./TEMPLATE_LOADING_FIX.md) |
| **Revizto empty** | No Revizto issues showing in dashboard | [REVIZTO_ISSUES_MISSING_DIAGNOSTIC.md](./REVIZTO_ISSUES_MISSING_DIAGNOSTIC.md) |
| **Frontend blank** | Application fails to load projects on startup | [REACT_FRONTEND_PROJECT_LOADING_FIX.md](./REACT_FRONTEND_PROJECT_LOADING_FIX.md) |
| **Wrong data** | Reviews show stale or incorrect date-based data | [DATE_BASED_REVIEW_REFRESH.md](./DATE_BASED_REVIEW_REFRESH.md) |

---

## 💡 Common Patterns

Many fixes follow these patterns - **try these first:**

### "X not loading" Issues
- Check network tab (browser DevTools)
- Verify API endpoint is responding
- Check server logs for errors
- Clear browser cache and reload
- See relevant *_LOADING_FIX.md file

### "X not saving" Issues
- Verify form validation passed
- Check browser console for JS errors
- Verify database connection
- Check server logs
- See relevant *_FIX.md file

### "X throwing error" Issues
- Read the full error message and stack trace
- Check if it's a known issue (search this directory)
- Try clearing cache and restarting
- Check configuration (environment variables)
- See specific *_FIX.md file

---

## 📋 When Reporting Issues

Include:
1. **What you were trying to do** - Step-by-step reproduction
2. **What error you got** - Exact message, error codes, stack traces
3. **When it started** - Recently or always?
4. **Environment** - Browser, Python version, database server
5. **Related files** - Screenshots, logs if applicable

Then check this directory to see if it's already fixed!

---

## 🔧 Contributing Fixes

When you solve a new problem:
1. Document the **symptoms** - How did you know something was wrong?
2. Document the **root cause** - Why did it happen?
3. Document the **solution** - Exact steps to fix it
4. Document **prevention** - How to avoid in future
5. Create a `ISSUE_NAME_FIX.md` file in this directory
6. Add entry to the table above

---

## 🎯 Prevention Tips

- Keep logs enabled and monitor them regularly
- Run integration tests after any database changes
- Test imports with small datasets first
- Clear browser cache before major testing
- Check error logs before contacting support
- Update documentation when you find undocumented issues

---

**Still having issues?** 
- Check the main [../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)
- Review [../core/DATABASE_CONNECTION_GUIDE.md](../core/DATABASE_CONNECTION_GUIDE.md) if database-related
- Check feature documentation in [../features/](../features/)

See [../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) for other documentation categories
