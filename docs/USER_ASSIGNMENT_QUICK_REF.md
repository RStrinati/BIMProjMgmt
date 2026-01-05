# User Assignment - Quick Reference

## Problem Solved
Project leads are responsible for services and reviews by default, but specific items need to be assignable to other users for workload distribution and tracking.

## Solution Overview
Added `assigned_user_id` column to ProjectServices, ServiceReviews, and ServiceItems tables with automatic defaulting to project lead and full reassignment capabilities.

## Quick Start

### 1. Run Database Migration
```powershell
sqlcmd -S <server> -d ProjectManagement -i sql/add_user_assignments.sql
```

### 2. API Endpoints Ready to Use

| Action | Endpoint | Method | Body |
|--------|----------|--------|------|
| Assign service | `/api/services/{id}/assign` | PUT | `{"user_id": 123}` |
| Assign review | `/api/reviews/{id}/assign` | PUT | `{"user_id": 123}` |
| Get user's work | `/api/users/{id}/assignments` | GET | - |
| Reassign all work | `/api/users/reassign` | POST | `{"from_user_id": 5, "to_user_id": 7}` |
| Workload summary | `/api/users/workload` | GET | - |

### 3. Default Behavior
- New services/reviews automatically assign to project's `internal_lead`
- Existing records were migrated to project lead during migration
- Unassigned items (NULL) fall back to project lead

## Common Use Cases

### Assign Specific Service to User
```python
assign_service_to_user(service_id=10, user_id=7)
```

### View User's Current Assignments
```python
assignments = get_user_assignments(user_id=7)
# Returns: services, reviews, and summary counts
```

### Reassign When User Leaves
```python
result = reassign_user_work(from_user_id=5, to_user_id=7)
# Moves all services and reviews from user 5 to user 7
```

### Check Team Workload
```python
workload = get_user_workload_summary()
# Returns list of users with service/review counts
```

## Database Objects Created

- **Columns**: `assigned_user_id` in ProjectServices, ServiceReviews, ServiceItems
- **View**: `vw_user_workload` - Real-time workload metrics
- **Function**: `fn_get_effective_assignee()` - Get assigned user with fallback
- **Procedure**: `sp_reassign_user_work` - Bulk reassignment
- **Trigger**: `tr_ProjectServices_AssignmentAudit` - Track changes
- **Table**: `audit_log` - Assignment change history

## Key Features

✅ Default to project lead automatically  
✅ Reassign to any user  
✅ Track workload across users  
✅ Audit all assignment changes  
✅ Bulk reassignment support  
✅ Project-specific reassignment  
✅ Foreign key protection (SET NULL on user delete)

## Frontend Integration Example

```typescript
// Assign service to user
await apiClient.put(`/services/${serviceId}/assign`, { 
  user_id: selectedUserId 
});

// Get user assignments
const { data } = await apiClient.get(`/users/${userId}/assignments`);
console.log(`User has ${data.summary.active_reviews} active reviews`);

// View team workload
const { data: workload } = await apiClient.get('/users/workload');
workload.forEach(user => {
  console.log(`${user.name}: ${user.active_reviews} active reviews`);
});
```

## Files Changed

- ✅ `sql/add_user_assignments.sql` - Migration script
- ✅ `constants/schema.py` - Added ASSIGNED_USER_ID constants
- ✅ `database.py` - Assignment functions + updated queries
- ✅ `backend/app.py` - API endpoints for assignments
- ✅ `docs/USER_ASSIGNMENT_IMPLEMENTATION.md` - Full documentation

## Next Actions

1. **Test**: Run migration and test API endpoints
2. **UI**: Add user dropdowns to service/review forms
3. **Dashboard**: Create workload visualization
4. **Reports**: Link assignments to billing/time tracking

For detailed documentation see: `docs/USER_ASSIGNMENT_IMPLEMENTATION.md`
