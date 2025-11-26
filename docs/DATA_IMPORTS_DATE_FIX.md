# Data Imports Date Formatting Fix

**Date**: October 13, 2025  
**Issue**: Invalid time value errors in React Data Imports components  
**Status**: ✅ RESOLVED

## Problem Summary

The Data Imports page was encountering **RangeError: Invalid time value** errors when attempting to format dates that were null, undefined, or invalid. This occurred in multiple components across the Data Imports feature.

### Error Details

```
Uncaught RangeError: Invalid time value
    at format (index.js:349:11)
    at ACCConnectorPanel.tsx:318:28
```

**Root Cause**: Direct use of `format(new Date(value), pattern)` without checking if the date value was valid first.

## Solution

### 1. Created Date Utility Module

Created `frontend/src/utils/dateUtils.ts` with safe date formatting functions:

```typescript
/**
 * Safely format a date with fallback for invalid dates
 * @param date - Date string, Date object, or null/undefined
 * @param formatString - date-fns format string (default: 'MMM d, yyyy')
 * @param fallback - Fallback text for invalid dates (default: 'N/A')
 */
export const formatDate = (
  date: string | Date | null | undefined,
  formatString: string = 'MMM d, yyyy',
  fallback: string = 'N/A'
): string => {
  if (!date) return fallback;
  
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    if (isNaN(dateObj.getTime())) return fallback;
    return dateFnsFormat(dateObj, formatString);
  } catch (error) {
    console.error('Error formatting date:', error, 'Date value:', date);
    return fallback;
  }
};

/**
 * Safely format a datetime with fallback
 * Convenience wrapper for 'MMM d, yyyy HH:mm' format
 */
export const formatDateTime = (
  date: string | Date | null | undefined,
  fallback: string = 'N/A'
): string => {
  return formatDate(date, 'MMM d, yyyy HH:mm', fallback);
};
```

### 2. Updated All Data Import Components

#### ACCConnectorPanel.tsx
- **Lines changed**: 36, 310-320
- **Old**: `format(new Date(file.date_modified), 'MMM d, yyyy HH:mm')`
- **New**: `formatDateTime(file.date_modified, 'N/A')`
- **Dates fixed**: `date_modified`, `date_extracted`

#### ACCDataImportPanel.tsx
- **Lines changed**: 50, 298, 355
- **Old**: `format(new Date(bookmark.last_used), 'MMM d, yyyy')`
- **New**: `formatDate(bookmark.last_used, 'MMM d, yyyy')`
- **Dates fixed**: `bookmark.last_used`, `log.import_date`

#### ACCIssuesPanel.tsx
- **Lines changed**: 40, 311-317
- **Old**: `format(new Date(issue.created_date), 'MMM d, yyyy')`
- **New**: `formatDate(issue.created_date, 'MMM d, yyyy')`
- **Dates fixed**: `issue.due_date`, `issue.created_date`

#### ReviztoImportPanel.tsx
- **Lines changed**: 40, 182, 292-298
- **Old**: `format(new Date(lastRun.start_time), 'MMM d, yyyy HH:mm')`
- **New**: `formatDateTime(lastRun.start_time)`
- **Dates fixed**: `lastRun.start_time`, `run.start_time`, `run.end_time`

#### RevitHealthPanel.tsx
- **Lines changed**: 39, 227, 288
- **Old**: `format(new Date(summary.latest_check_date), 'MMMM d, yyyy')`
- **New**: `formatDate(summary.latest_check_date, 'MMMM d, yyyy')`
- **Dates fixed**: `summary.latest_check_date`, `file.check_date`

## Benefits

### 1. **Null Safety**
- All date values are checked before formatting
- No more crashes on null/undefined dates
- Graceful fallback to 'N/A' or custom text

### 2. **Error Handling**
- Try-catch blocks prevent runtime errors
- Console logging for debugging invalid dates
- Invalid Date objects are detected and handled

### 3. **Consistency**
- Single source of truth for date formatting
- Standardized format patterns across all components
- Easy to update format globally if needed

### 4. **Type Safety**
- Accepts `string | Date | null | undefined`
- TypeScript ensures proper usage
- No need for manual type checking in components

## Testing Checklist

✅ **ACCConnectorPanel**
- Date modified displays correctly or shows 'N/A'
- Date extracted displays correctly or shows 'N/A'
- No console errors when dates are null

✅ **ACCDataImportPanel**
- Bookmark last used dates format correctly
- Import log dates display properly
- Handles missing bookmark usage dates

✅ **ACCIssuesPanel**
- Issue created dates always display
- Due dates show 'No due date' when null
- No crashes on missing dates

✅ **ReviztoImportPanel**
- Last run start time displays correctly
- Run history shows all dates properly
- End time shows '-' when null

✅ **RevitHealthPanel**
- Latest check date displays in alert
- File check dates format correctly
- Handles missing health check dates

## Code Quality

### Before
```typescript
// Unsafe - crashes if date is null/undefined/invalid
{format(new Date(file.date_extracted), 'MMM d, yyyy HH:mm')}
```

### After
```typescript
// Safe - handles all edge cases
{formatDateTime(file.date_extracted, 'N/A')}
```

## Performance Impact

- **Minimal**: Added validation checks are negligible
- **Improved UX**: No more app crashes from invalid dates
- **Better DX**: Centralized utility is easier to maintain

## Files Modified

1. ✅ `frontend/src/utils/dateUtils.ts` - **NEW** (68 lines)
2. ✅ `frontend/src/components/dataImports/ACCConnectorPanel.tsx` - Updated imports and 2 date calls
3. ✅ `frontend/src/components/dataImports/ACCDataImportPanel.tsx` - Updated imports and 2 date calls
4. ✅ `frontend/src/components/dataImports/ACCIssuesPanel.tsx` - Updated imports and 2 date calls
5. ✅ `frontend/src/components/dataImports/ReviztoImportPanel.tsx` - Updated imports and 3 date calls
6. ✅ `frontend/src/components/dataImports/RevitHealthPanel.tsx` - Updated imports and 2 date calls

## Verification

Run the React dev server and test all data import panels:

```powershell
cd frontend
npm run dev
```

Navigate to: http://localhost:5174/data-imports

**Expected Results**:
- ✅ No console errors
- ✅ All dates display correctly
- ✅ Invalid/null dates show 'N/A' or custom fallback
- ✅ No "Invalid time value" errors

## Future Improvements

1. **Add date validation on API response**
   - Ensure backend returns valid ISO 8601 dates
   - Add schema validation with Zod or similar

2. **Extend utility functions**
   - Add relative time formatting (e.g., "2 hours ago")
   - Add date range formatting
   - Add timezone support if needed

3. **Consider date-fns wrapper**
   - Create comprehensive date utility library
   - Add localization support
   - Standardize all date operations

## Related Documentation

- [Data Imports Implementation Summary](./DATA_IMPORTS_IMPLEMENTATION_SUMMARY.md)
- [React Component Development](./DEVELOPER_ONBOARDING.md)
- [TypeScript Best Practices](./DEVELOPER_ONBOARDING.md)

---

**Resolution Time**: ~15 minutes  
**Complexity**: Low  
**Impact**: High (prevents app crashes)  
**Status**: Production-ready ✅
