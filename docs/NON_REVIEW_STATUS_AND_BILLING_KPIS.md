# Non-Review Service Status Management & Billing KPIs

## Overview

This document describes the enhanced status management system for non-review services and the new billing KPI displays added to the BIM Project Management system.

## Feature Summary

### 1. **Non-Review Service Status Management**
Non-review services (Digital Initiation, PC Reports, Audits, etc.) can now have their status manually managed with automatic progress updates:

- **Planned** → 0% progress
- **In Progress** → 50% progress  
- **Completed** → 100% progress

### 2. **Billing KPIs in Project Setup Tab**
The Project Setup tab now displays comprehensive billing metrics:

- **Total Project Value**: Sum of all agreed fees
- **Total Billed to Date**: Sum of all claimed amounts
- **Overall Progress Percentage**: (Billed / Total Value) × 100
- **Remaining Amount**: Total Value - Billed to Date
- **Current Month Billing**: Reviews scheduled for billing this month
- **Billable by Stage Table**: Shows billed amounts grouped by construction phase/stage

### 3. **Billing Summary Tables in Review Management Tab**
The Billing tab in Review Management now includes two new summary sections:

- **Total Billable by Stage**: Aggregates billed amounts by phase (Phase 4/5, Phase 7, Phase 8, etc.)
- **Total Billable by Month**: Shows monthly billing totals from billing claims

---

## User Guide

### How to Update Non-Review Service Status

1. **Navigate to Review Management Tab**
   - Open the application and select your project
   - Go to the **Review Management** tab
   - Click the **📝 Service Setup** sub-tab

2. **Select a Non-Review Service**
   - In the "Current Project Services" grid, find a service with unit_type:
     - `lump_sum` (e.g., Digital Initiation, PC Report)
     - `audit` (e.g., Cupix Reviews, Phase 7 Audits)
     - Any non-`review` type service

3. **Update Status**
   - Click the service row to select it
   - Click the **📝 Update Status** button
   - A dialog will appear showing:
     - Service name
     - Service type
     - Current status
   
4. **Choose New Status**
   - Select one of:
     - **📋 Planned (0%)**: Service is planned but not yet started
     - **🔄 In Progress (50%)**: Service work has begun
     - **✅ Completed (100%)**: Service is fully complete
   - Click **Save**

5. **Automatic Updates**
   - The service's `progress_pct` is automatically set based on status
   - Billing calculations are immediately updated to reflect the new progress
   - The Project Setup tab KPIs will update on next refresh

### Example: Digital Initiation Lifecycle

**Initial State:**
```
Service: Digital Initiation (DEXP, Kickoff, ACC/Revizto setup)
Type: lump_sum
Fee: $15,000
Status: planned
Progress: 0%
Billed: $0
```

**After Kickoff Meeting (In Progress):**
```
Status: in_progress
Progress: 50%
Billed: $7,500 (50% of $15,000)
```

**After Setup Complete (Completed):**
```
Status: completed
Progress: 100%
Billed: $15,000 (100% of $15,000)
```

---

## Viewing Billing KPIs

### Project Setup Tab - Billing & Progress KPIs Section

The Project Setup tab now displays a comprehensive billing summary:

**Top Summary Line:**
```
Total Project Value: $250,000 | Billed to Date: $125,000 (50.0%) | Remaining: $125,000
```

**Current Month:**
```
This Month (October): $22,000 (4 reviews)
```

**Billable by Stage Table:**
```
┌─────────────────────────────────┬──────────────────┐
│ Stage/Phase                     │ Billed Amount    │
├─────────────────────────────────┼──────────────────┤
│ Phase 4/5 – Digital Initiation  │ $15,000         │
│ Phase 4/5 – Digital Production  │ $22,000         │
│ Phase 7 – Digital Production    │ $66,000         │
│ Phase 8 – Digital Handover      │ $17,000         │
└─────────────────────────────────┴──────────────────┘
```

### Review Management Tab - Billing Tab

The **💰 Billing** sub-tab in Review Management includes:

**Left Panel:**
- **Billing Claims**: Shows generated billing claims with PO refs, periods, and totals
- **Service Progress & Billing**: Lists all services with progress %, billed amounts, and remaining fees

**Right Panel:**
- **Total Billable by Stage**: Same table as Project Setup, showing phase-level totals
- **Total Billable by Month**: Shows billing amounts by month from claim dates

**Example Monthly Billing Table:**
```
┌─────────────┬──────────────────┐
│ Month       │ Total Billed     │
├─────────────┼──────────────────┤
│ Oct 2025    │ $22,000         │
│ Sep 2025    │ $27,500         │
│ Aug 2025    │ $33,000         │
│ ═══ TOTAL ═══│ $82,500         │
└─────────────┴──────────────────┘
```

---

## Technical Details

### Database Schema

**ProjectServices Table:**
```sql
service_id        INT PRIMARY KEY
project_id        INT
phase             NVARCHAR(100)      -- e.g., "Phase 4/5 – Digital Initiation"
service_code      NVARCHAR(50)       -- INIT, PROD, AUDIT, HANDOVER
service_name      NVARCHAR(200)
unit_type         NVARCHAR(50)       -- lump_sum, review, audit, license
agreed_fee        DECIMAL(18,2)
status            NVARCHAR(30)       -- planned, in_progress, completed
progress_pct      DECIMAL(9,4)       -- 0.0000 to 100.0000
claimed_to_date   DECIMAL(18,2)
```

### Backend Methods

**Setting Non-Review Service Status:**
```python
from review_management_service import ReviewManagementService

service = ReviewManagementService(db_connection)

# Update status - automatically sets progress_pct
service.set_non_review_service_status(
    service_id=123,
    status='completed'  # planned | in_progress | completed
)
```

**Getting Billing Summaries:**
```python
# Get billable by stage
stage_billing = service.get_billable_by_stage(project_id=1)
# Returns: [{'phase': 'Phase 4/5...', 'billed_amount': 15000.00}, ...]

# Get billable by month
month_billing = service.get_billable_by_month(project_id=1)
# Returns: [{'month': 'Oct 2025', 'total_billed': 22000.00}, ...]
```

---

## Business Rules

### Status Restrictions

1. **Review-Type Services**
   - Cannot use manual status updates
   - Status is automatically managed through review cycles
   - Progress is calculated based on completed review cycles

2. **Non-Review Services**
   - Can be manually updated via the UI
   - Status changes immediately affect `progress_pct`
   - Progress changes trigger billing recalculations

### Billing Calculation

**For Non-Review Services:**
```
Billed Amount = agreed_fee × (progress_pct / 100)
```

**Example:**
```
Service: Digital Initiation
Agreed Fee: $15,000
Status: in_progress
Progress: 50%
Billed Amount: $15,000 × 0.50 = $7,500
```

### Stage Aggregation

Services are grouped by the `phase` column:
- Phase 4/5 – Digital Initiation
- Phase 4/5 – Digital Production
- Phase 7 – Digital Production
- Phase 8 – Digital Handover

Billing amounts for all services in each phase are summed for the "Total Billable by Stage" view.

### Month Aggregation

Billing claims are grouped by the `period_start` month:
- Claims with period_start in October 2025 → "Oct 2025"
- All line items within those claims are summed

---

## Workflow Integration

### Typical Project Lifecycle

1. **Project Setup**
   - Apply service template (e.g., SINSW - Melrose Park HS)
   - Services are created with status = `planned`, progress = 0%

2. **Digital Initiation Phase**
   - Set "Digital Initiation" service to `in_progress` (50%)
   - Billing KPI shows partial progress
   - Generate billing claim for initial payment

3. **Complete Initiation**
   - Set "Digital Initiation" to `completed` (100%)
   - Full $15,000 is now billable
   - Generate claim for remaining 50%

4. **Review Cycles**
   - Review-type services progress automatically as reviews complete
   - Each completed review increases progress_pct

5. **Handover Phase**
   - Set PC Report to `in_progress`, then `completed`
   - Set Cupix Reviews to `completed` as audits finish
   - Final billing claim generated

---

## Testing

### Test Script

Run the comprehensive test script to verify the functionality:

```bash
python tools/test_non_review_status.py
```

**Test Coverage:**
- Status updates for non-review services
- Progress percentage verification
- Billing calculation accuracy
- Stage and month aggregations

---

## FAQ

**Q: Why can't I update status on a review-type service?**  
A: Review-type services are managed through the review cycle system. Their progress is calculated based on completed review cycles, not manual status updates.

**Q: What happens if I set a service to "completed" before the work is done?**  
A: The system will immediately mark it as 100% complete and include the full fee in billing calculations. Only set services to "completed" when work is actually finished.

**Q: How do I revert a service from "completed" back to "in progress"?**  
A: Use the same **📝 Update Status** dialog and select a different status. The progress percentage will update accordingly.

**Q: Will changing status affect existing billing claims?**  
A: No, existing billing claims are historical records and remain unchanged. However, future billing claim generation will use the updated progress percentages.

**Q: Where do the month labels in "Billable by Month" come from?**  
A: They come from the `period_start` date of billing claims. When you generate a billing claim for a specific period, that claim's start month determines its categorization.

---

## Support

For issues or questions:
1. Check that the service is a non-review type (lump_sum, audit, etc.)
2. Verify database connection is active
3. Review error messages in the console
4. Run the test script to verify system functionality

For development support, see `review_management_service.py` and `phase1_enhanced_ui.py` source code.
