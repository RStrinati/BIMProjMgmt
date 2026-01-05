# User Assignment Implementation Guide

## Overview

This implementation adds comprehensive user assignment capabilities to services, reviews, and items in the BIM Project Management system. The project lead is the default assignee, but work can be reassigned to other users as needed.

## Database Changes

### Migration Script
Location: `sql/add_user_assignments.sql`

**Tables Modified:**
1. **ProjectServices** - Added `assigned_user_id` column
2. **ServiceReviews** - Added `assigned_user_id` column
3. **ServiceItems** - Added `assigned_user_id` column (if exists)

**Foreign Keys:**
All `assigned_user_id` columns reference `users.user_id` with `ON DELETE SET NULL`

### Default Assignment Logic
- Existing records are automatically assigned to the project's internal lead
- New services/reviews default to the project lead unless explicitly assigned
- The SQL function `fn_get_effective_assignee()` returns the assigned user or defaults to project lead

### Helper Objects Created
1. **View: `vw_user_workload`** - Real-time user workload analysis
2. **Function: `fn_get_effective_assignee`** - Get effective assignee with fallback
3. **Trigger: `tr_ProjectServices_AssignmentAudit`** - Audit assignment changes
4. **Stored Proc: `sp_reassign_user_work`** - Bulk reassignment operations
5. **Table: `audit_log`** - Track all assignment changes

## Backend Implementation

### Schema Constants Updated (`constants/schema.py`)

```python
class ProjectServices:
    ASSIGNED_USER_ID = "assigned_user_id"  # NEW

class ServiceReviews:
    ASSIGNED_USER_ID = "assigned_user_id"  # NEW

class ServiceItems:
    ASSIGNED_USER_ID = "assigned_user_id"  # NEW
```

### Database Functions Added (`database.py`)

#### Assignment Functions
```python
assign_service_to_user(service_id, user_id)
# Assign a service to a specific user

assign_review_to_user(review_id, user_id)
# Assign a review to a specific user

get_user_assignments(user_id)
# Get all services and reviews assigned to a user
# Returns: {'services': [...], 'reviews': [...], 'summary': {...}}

reassign_user_work(from_user_id, to_user_id, project_id=None)
# Reassign all work from one user to another (optionally filtered by project)
# Returns: {'services_reassigned': int, 'reviews_reassigned': int}

get_project_lead_user_id(project_id)
# Get the user_id of the project's internal lead

get_user_workload_summary()
# Get workload summary for all users with assignments
# Returns list of users with counts of services, reviews, etc.
```

#### Modified Functions
- `get_project_services()` - Now includes `assigned_user_id` and `assigned_user_name`

### API Endpoints (`backend/app.py`)

#### User Assignment Endpoints

**Assign Service to User**
```
PUT /api/services/<service_id>/assign
Body: {"user_id": 123}
Response: {"message": "Service assigned successfully"}
```

**Assign Review to User**
```
PUT /api/reviews/<review_id>/assign
Body: {"user_id": 123}
Response: {"message": "Review assigned successfully"}
```

**Get User Assignments**
```
GET /api/users/<user_id>/assignments
Response: {
  "services": [
    {
      "service_id": 1,
      "service_name": "Design Review",
      "service_code": "DR-001",
      "status": "in_progress",
      "project_id": 10,
      "project_name": "Solar Farm Project",
      "progress_pct": 45.5
    }
  ],
  "reviews": [
    {
      "review_id": 5,
      "cycle_no": 2,
      "status": "planned",
      "due_date": "2025-12-15",
      "service_name": "Design Review",
      "service_id": 1,
      "project_name": "Solar Farm Project",
      "project_id": 10
    }
  ],
  "summary": {
    "total_services": 3,
    "total_reviews": 8,
    "active_reviews": 5
  }
}
```

**Reassign User Work**
```
POST /api/users/reassign
Body: {
  "from_user_id": 5,
  "to_user_id": 7,
  "project_id": 10  // Optional - omit to reassign all work
}
Response: {
  "services_reassigned": 3,
  "reviews_reassigned": 12
}
```

**Get User Workload Summary**
```
GET /api/users/workload
Response: [
  {
    "user_id": 1,
    "name": "John Smith",
    "email": "john@example.com",
    "role": "Project Manager",
    "assigned_services": 5,
    "assigned_reviews": 15,
    "active_reviews": 12,
    "overdue_reviews": 2,
    "projects": 3
  },
  ...
]
```

**Get Project Lead User**
```
GET /api/projects/<project_id>/lead-user
Response: {"user_id": 123}
```

## Implementation Steps

### Step 1: Run Database Migration

```powershell
# Connect to SQL Server and run the migration
sqlcmd -S <server> -d ProjectManagement -i sql/add_user_assignments.sql
```

Or execute via your SQL client (SSMS, Azure Data Studio, etc.)

### Step 2: Restart Backend Server

```powershell
# The backend will automatically use the new schema constants
cd backend
python app.py
```

### Step 3: Frontend Integration (Example)

#### Add User Assignment Dropdown to Service/Review Forms

```typescript
// In your service or review component
import { usersApi } from '../api/users';

function ServiceAssignmentSelector({ serviceId, currentUserId }) {
  const { data: users } = useQuery({
    queryKey: ['users'],
    queryFn: usersApi.getAll,
  });

  const assignMutation = useMutation({
    mutationFn: async (userId: number) => {
      const response = await apiClient.put(`/services/${serviceId}/assign`, {
        user_id: userId,
      });
      return response.data;
    },
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['services'] });
    },
  });

  return (
    <FormControl fullWidth>
      <InputLabel>Assigned To</InputLabel>
      <Select
        value={currentUserId || ''}
        onChange={(e) => assignMutation.mutate(Number(e.target.value))}
      >
        {users?.map((user) => (
          <MenuItem key={user.user_id} value={user.user_id}>
            {user.name} ({user.role})
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
```

#### Display User Workload Dashboard

```typescript
function UserWorkloadDashboard() {
  const { data: workload } = useQuery({
    queryKey: ['users', 'workload'],
    queryFn: async () => {
      const response = await apiClient.get('/users/workload');
      return response.data;
    },
  });

  return (
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>User</TableCell>
            <TableCell>Services</TableCell>
            <TableCell>Active Reviews</TableCell>
            <TableCell>Overdue</TableCell>
            <TableCell>Projects</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {workload?.map((user) => (
            <TableRow key={user.user_id}>
              <TableCell>{user.name}</TableCell>
              <TableCell>{user.assigned_services}</TableCell>
              <TableCell>{user.active_reviews}</TableCell>
              <TableCell>
                <Chip 
                  label={user.overdue_reviews}
                  color={user.overdue_reviews > 0 ? 'error' : 'default'}
                />
              </TableCell>
              <TableCell>{user.projects}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
```

## Usage Scenarios

### Scenario 1: Default Assignment (Project Lead)
When creating a new service or review without specifying an assignee, the system automatically assigns it to the project's internal lead.

```python
# Backend automatically assigns to project lead if user_id not provided
service_id = create_project_service(
    project_id=10,
    service_code="DR-001",
    service_name="Design Review"
)
# Service is automatically assigned to project lead
```

### Scenario 2: Explicit Assignment
Assign a service to a specific team member:

```python
# Assign service to a specific user
assign_service_to_user(service_id=5, user_id=7)
```

### Scenario 3: Reassignment Due to Leave
When a user goes on leave, reassign all their work:

```python
# Reassign all work from user 5 to user 7
result = reassign_user_work(from_user_id=5, to_user_id=7)
# Returns: {'services_reassigned': 3, 'reviews_reassigned': 12}
```

### Scenario 4: Project-Specific Reassignment
Reassign work for a specific project only:

```python
# Reassign only Project 10 work
result = reassign_user_work(
    from_user_id=5, 
    to_user_id=7, 
    project_id=10
)
```

### Scenario 5: Workload Balancing
View current workload to balance assignments:

```python
workload = get_user_workload_summary()
# Returns list of users with their current workload
```

## Reporting & Analytics

### User Workload View
Query the database view for real-time workload data:

```sql
SELECT * FROM vw_user_workload
ORDER BY active_reviews_count DESC;
```

### Assignment Audit Trail
Review assignment changes:

```sql
SELECT 
    al.changed_at,
    al.table_name,
    al.record_id,
    al.old_value AS old_user_id,
    al.new_value AS new_user_id,
    u1.name AS old_user_name,
    u2.name AS new_user_name
FROM audit_log al
LEFT JOIN users u1 ON al.old_value = CAST(u1.user_id AS NVARCHAR(50))
LEFT JOIN users u2 ON al.new_value = CAST(u2.user_id AS NVARCHAR(50))
WHERE al.table_name = 'ProjectServices'
  AND al.action = 'assignment_change'
ORDER BY al.changed_at DESC;
```

### User Performance Metrics
```sql
SELECT 
    u.name,
    COUNT(DISTINCT sr.service_id) AS services_completed,
    COUNT(sr.review_id) AS reviews_completed,
    AVG(DATEDIFF(day, sr.planned_date, sr.actual_issued_at)) AS avg_turnaround_days,
    SUM(CASE 
        WHEN sr.due_date >= sr.actual_issued_at THEN 1 
        ELSE 0 
    END) * 100.0 / COUNT(*) AS on_time_percentage
FROM users u
INNER JOIN ServiceReviews sr ON u.user_id = sr.assigned_user_id
WHERE sr.status = 'completed'
  AND sr.actual_issued_at IS NOT NULL
GROUP BY u.user_id, u.name
ORDER BY on_time_percentage DESC;
```

## Financial Implications

### User Time & Cost Tracking
The assigned user can now be linked to:
- **Billing rates** - Associate user hourly rates for accurate billing
- **Time tracking** - Track time spent by each user on services/reviews
- **Cost allocation** - Attribute costs to specific users for project accounting
- **Resource planning** - Forecast resource needs based on user assignments

### Future Enhancements
1. **User Billing Rates Table** - Store hourly/daily rates per user
2. **Time Entries** - Link time entries to assignments
3. **Cost Reports** - Generate cost reports by user, project, and service
4. **Capacity Planning** - Calculate user capacity vs. assigned workload

## Troubleshooting

### Services Not Showing Assigned User
1. Check if migration ran successfully
2. Verify column exists: `SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ProjectServices' AND COLUMN_NAME = 'assigned_user_id'`
3. Check if users are linked properly

### Default Assignment Not Working
1. Verify project has `internal_lead` set
2. Ensure `internal_lead` matches a user's `name` in users table
3. Check the `fn_get_effective_assignee` function exists

### API Returns 500 Error
1. Check backend logs for detailed error messages
2. Verify database connection is working
3. Ensure all imports are present in `backend/app.py`

## Testing Checklist

- [ ] Run SQL migration successfully
- [ ] Verify columns exist in all tables
- [ ] Test `GET /api/users/workload` endpoint
- [ ] Test `PUT /api/services/<id>/assign` endpoint
- [ ] Test `GET /api/users/<id>/assignments` endpoint
- [ ] Test `POST /api/users/reassign` endpoint
- [ ] Verify default assignment to project lead
- [ ] Verify assignment changes are audited
- [ ] Test reassignment across projects
- [ ] Verify foreign key constraints work (delete user sets NULL)
- [ ] Test workload summary calculation
- [ ] Verify assignment appears in service listings

## Security Considerations

1. **Authorization** - Add role-based checks to ensure only authorized users can reassign work
2. **Audit Logging** - All assignment changes are logged in `audit_log` table
3. **Data Integrity** - Foreign keys ensure referential integrity
4. **Soft Deletes** - User deletion sets `assigned_user_id` to NULL (preserves data)

## Files Modified

### Created
- `sql/add_user_assignments.sql` - Database migration script
- `docs/USER_ASSIGNMENT_IMPLEMENTATION.md` - This documentation

### Modified
- `constants/schema.py` - Added `ASSIGNED_USER_ID` constants
- `database.py` - Added assignment functions and updated queries
- `backend/app.py` - Added API endpoints and imports

## Next Steps

1. **Run the migration** - Execute `sql/add_user_assignments.sql`
2. **Test API endpoints** - Use Postman or curl to test
3. **Update frontend** - Add user assignment UI components
4. **Train users** - Document workflow for assigning and reassigning work
5. **Monitor workload** - Use the workload dashboard to balance assignments

## Support

For questions or issues with this implementation:
1. Check the troubleshooting section above
2. Review audit logs for assignment history
3. Check backend logs for detailed error messages
4. Verify database schema matches expected structure
