# Component Test ID Audit & Implementation Checklist

This document helps you audit your component library and ensure all components have consistent, meaningful test IDs aligned with the Golden Set.

## Test ID Naming Convention

Use this pattern for all components:

```
data-testid="[feature]-[component]-[type]-[identifier]-[optional-state]"

Examples:
  data-testid="workspace-service-row-123"
  data-testid="workspace-service-row-123-actions"
  data-testid="cell-title-456-input"
  data-testid="cell-title-456-save"
  data-testid="form-dialog-service-create"
  data-testid="status-badge-789"
  data-testid="blocker-badge-101"
```

---

## Golden Primitives Audit Checklist

### AppButton
- [ ] Primary button has `data-testid="btn-[action]-primary"`
- [ ] Secondary button has `data-testid="btn-[action]-secondary"`
- [ ] Outline button has `data-testid="btn-[action]-outline"`
- [ ] Ghost button has `data-testid="btn-[action]-ghost"`
- [ ] Link button has `data-testid="btn-[action]-link"`
- [ ] Destructive button has `data-testid="btn-[action]-destructive"`

**Component Template:**
```tsx
<AppButton 
  data-testid="btn-save-primary" 
  variant="primary"
>
  Save
</AppButton>
```

**Verification Command:**
```bash
grep -r 'data-testid="btn-' frontend/src/components/primitives/AppButton.tsx
grep -r 'variant=' frontend/src/components/ | grep -v 'data-testid'
```

---

### AppInput
- [ ] Text input has `data-testid="input-[name]"`
- [ ] Search input has `data-testid="input-search"`
- [ ] Number input has `data-testid="input-[name]-number"`
- [ ] Error state is visible in DOM
- [ ] Helper text has `data-testid="input-[name]-helper"`
- [ ] Error message has `data-testid="input-[name]-error"`

**Component Template:**
```tsx
<AppInput 
  data-testid="input-project-name"
  name="projectName"
  type="text"
  error={!!errors.projectName}
  helperText={errors.projectName}
/>
```

**Verification:**
```bash
grep -r 'data-testid="input-' frontend/src/components/
grep -r 'AppInput' frontend/src/components/ | grep -v 'data-testid'
```

---

### AppSelect
- [ ] Select container has `data-testid="select-[name]"`
- [ ] Each option can be identified by `getByRole('option')`
- [ ] Open/close state is testable
- [ ] Error state is visible

**Component Template:**
```tsx
<AppSelect
  data-testid="select-status"
  value={status}
  onChange={setStatus}
  options={[
    { value: 'draft', label: 'Draft' },
    { value: 'active', label: 'Active' },
  ]}
/>
```

**Verification:**
```bash
grep -r 'data-testid="select-' frontend/src/components/
```

---

### AppTextarea
- [ ] Has `data-testid="textarea-[name]"`
- [ ] Error state visible
- [ ] Character count visible if applicable

**Component Template:**
```tsx
<AppTextarea
  data-testid="textarea-description"
  name="description"
  error={!!errors.description}
/>
```

---

### AppCheckbox & AppSwitch
- [ ] Checkbox has `data-testid="checkbox-[name]"`
- [ ] Switch has `data-testid="switch-[name]"`
- [ ] Both use `getByRole('checkbox')` or `getByRole('switch')`

**Component Template:**
```tsx
<AppCheckbox
  data-testid="checkbox-include-attachments"
  label="Include attachments"
/>

<AppSwitch
  data-testid="switch-notifications"
  label="Enable notifications"
/>
```

---

### AppBadge & AppChip
- [ ] Badge has `data-testid="badge-[type]-[id]"`
- [ ] Status badge has `data-testid="status-badge-[recordId]"`
- [ ] Severity badge has `data-testid="severity-badge-[id]"`
- [ ] Chip has `data-testid="chip-[category]-[value]"`

**Component Template:**
```tsx
<AppBadge 
  data-testid="status-badge-123"
  status="active"
>
  Active
</AppBadge>

<AppBadge
  data-testid="severity-badge-high"
  severity="high"
>
  High Priority
</AppBadge>

<AppChip
  data-testid="chip-phase-design"
  label="Design"
/>
```

---

### AppCard & AppPanel
- [ ] Card has `data-testid="card-[feature]"`
- [ ] Panel has `data-testid="[feature]-panel"`
- [ ] Each section has `data-testid="[feature]-section-[name]"`

**Component Template:**
```tsx
<AppCard data-testid="card-project-summary">
  <CardContent>{/* ... */}</CardContent>
</AppCard>

<AppPanel data-testid="service-details-panel">
  <RightPanelSection 
    data-testid="service-details-section-info"
    title="Information"
  >
    {/* ... */}
  </RightPanelSection>
</AppPanel>
```

---

### AppDivider
- [ ] Generally not tested (visual only)
- [ ] No test ID needed unless it separates testable sections

---

### AppIconButton
- [ ] Has `data-testid="icon-btn-[action]"` OR uses `getByRole('button')`
- [ ] Include accessible label: `aria-label="Edit"`

**Component Template:**
```tsx
<AppIconButton 
  data-testid="icon-btn-delete"
  aria-label="Delete item"
  icon={<DeleteIcon />}
  onClick={onDelete}
/>
```

---

## Golden Patterns Audit Checklist

### RightPanel
- [ ] Panel root has `data-testid="[feature]-right-panel"`
- [ ] Panel is fixed width (no test needed)
- [ ] Scroll behavior works (test: scroll should work)
- [ ] Empty state has `data-testid="[feature]-empty-state"`

**Component Template:**
```tsx
<div data-testid="service-right-panel" className="fixed-width panel">
  {isEmpty ? (
    <div data-testid="service-empty-state">
      No service selected
    </div>
  ) : (
    <ServiceDetails />
  )}
</div>
```

---

### RightPanelSection
- [ ] Has `data-testid="[feature]-section-[name]"`
- [ ] Is collapsible (if applicable)
- [ ] Has optional action button with `data-testid="[feature]-section-[name]-action"`

**Component Template:**
```tsx
<RightPanelSection
  data-testid="service-section-billing"
  title="Billing"
  collapsible
  action={
    <AppButton data-testid="service-section-billing-action">
      Add Item
    </AppButton>
  }
>
  {/* content */}
</RightPanelSection>
```

---

### LinearListRow
- [ ] Row has `data-testid="[feature]-row-[id]"`
- [ ] Left section (title/subtitle) is readable
- [ ] Middle section (chips) is testable
- [ ] Right section (status + actions) has test IDs

**Component Template:**
```tsx
<LinearListRow 
  data-testid="service-row-123"
  left={{
    primary: 'Design Review',
    secondary: 'Phase: Design',
  }}
  middle={[
    <AppChip key="1" label="Active" />,
    <AppChip key="2" label="BIM" />,
  ]}
  right={{
    status: 'Active',
    actions: (
      <AppIconButton 
        data-testid="service-row-123-actions"
        icon={<MoreIcon />}
      />
    ),
  }}
/>
```

---

### InlineEditableCell
- [ ] Cell container has `data-testid="cell-[fieldName]-[recordId]"`
- [ ] Edit input has `data-testid="cell-[fieldName]-[recordId]-input"`
- [ ] Save button has `data-testid="cell-[fieldName]-[recordId]-save"`
- [ ] Cancel button has `data-testid="cell-[fieldName]-[recordId]-cancel"`
- [ ] Dirty indicator visible when changed

**Component Template:**
```tsx
<InlineEditableCell
  data-testid="cell-title-901"
  value={item.title}
  onEdit={(newValue) => updateItem(901, { title: newValue })}
  renderInput={(props) => (
    <AppInput 
      {...props}
      data-testid="cell-title-901-input"
    />
  )}
  renderActions={() => (
    <>
      <button data-testid="cell-title-901-save">Save</button>
      <button data-testid="cell-title-901-cancel">Cancel</button>
    </>
  )}
/>
```

---

### EmptyState
- [ ] Has `data-testid="[container]-empty-state"`
- [ ] Shows appropriate icon/message
- [ ] Has CTA button (if applicable)

**Component Template:**
```tsx
<EmptyState
  data-testid="projects-empty-state"
  icon={<ProjectIcon />}
  title="No Projects"
  description="Create your first project to get started"
  action={
    <AppButton data-testid="projects-empty-state-cta">
      Create Project
    </AppButton>
  }
/>
```

---

### KpiStrip & KpiCard
- [ ] Strip/Card has `data-testid="kpi-[metric]"`
- [ ] Value is readable
- [ ] Trend indicator (if any) is testable

**Component Template:**
```tsx
<KpiCard
  data-testid="kpi-agreed-fee"
  title="Agreed Fee"
  value="$100,000"
  trend="+5%"
/>

<KpiStrip data-testid="kpi-strip-billing">
  <KpiCard data-testid="kpi-billed" value="$25,000" />
  <KpiCard data-testid="kpi-unbilled" value="$75,000" />
</KpiStrip>
```

---

## Feature-Specific Components

### Projects Home Page
- [ ] Table has `data-testid="projects-home-table"`
- [ ] Row has `data-testid="projects-home-row-[projectId]"`
- [ ] New button has `data-testid="projects-home-new-button"`
- [ ] KPI cards have `data-testid="kpi-*"`

### Workspace Tabs
- [ ] Tab buttons use `getByRole('tab', { name: '...' })`
- [ ] Services panel has `data-testid="workspace-services-panel"`
- [ ] Services list has `data-testid="project-workspace-v2-services"`
- [ ] Service row has `data-testid="workspace-service-row-[serviceId]"`

### Service Items (Deliverables)
- [ ] Table has `data-testid="project-workspace-v2-deliverables"`
- [ ] Item row has `data-testid="deliverable-item-row-[itemId]"`
- [ ] Title cell has `data-testid="cell-item-title-[itemId]"`
- [ ] Due date cell has `data-testid="cell-item-duedate-[itemId]"`
- [ ] Status cell has `data-testid="cell-item-status-[itemId]"`

### Review Cycles
- [ ] Reviews panel has `data-testid="project-workspace-v2-reviews"`
- [ ] Review row has `data-testid="project-workspace-v2-review-row-[reviewId]"`
- [ ] Blocker badge has `data-testid="blocker-badge-[reviewId]"`
- [ ] Linked issues has `data-testid="project-workspace-v2-review-linked-issues"`

### Forms & Dialogs
- [ ] Dialog has `data-testid="form-dialog-[feature]-[action]"`
- [ ] Submit button has `data-testid="form-[feature]-submit"`
- [ ] Cancel button has `data-testid="form-[feature]-cancel"`

**Component Template:**
```tsx
<AppDialog
  data-testid="form-dialog-service-create"
  open={isOpen}
  title="Create Service"
>
  <form>
    <AppInput 
      data-testid="form-service-create-name"
      placeholder="Service name"
    />
    <div className="actions">
      <AppButton data-testid="form-service-create-submit">
        Create
      </AppButton>
      <AppButton data-testid="form-service-create-cancel">
        Cancel
      </AppButton>
    </div>
  </form>
</AppDialog>
```

---

## Audit Commands

### Find components without test IDs
```bash
# Find all AppButton without data-testid
grep -r '<AppButton' frontend/src/components/ | grep -v 'data-testid'

# Find all AppInput without data-testid
grep -r '<AppInput' frontend/src/components/ | grep -v 'data-testid'

# Find all AppSelect without data-testid
grep -r '<AppSelect' frontend/src/components/ | grep -v 'data-testid'
```

### Find inconsistent test ID patterns
```bash
# Find all status badge test IDs
grep -r 'data-testid="status-' frontend/src/

# Check for inconsistencies (should be status-badge-[id])
grep -r 'data-testid="badge-status' frontend/src/

# Find all cell test IDs
grep -r 'data-testid="cell-' frontend/src/
```

### Check for hardcoded strings vs. test IDs
```bash
# Components using getByTestId in tests but lacking test IDs in components
grep -r 'getByTestId(' frontend/tests/ | cut -d':' -f2 | sort | uniq > test_ids_used.txt
grep -r 'data-testid=' frontend/src/components/ | cut -d'"' -f2 | sort | uniq > test_ids_defined.txt
comm -23 test_ids_used.txt test_ids_defined.txt
```

---

## Implementation Steps

1. **Week 1: Audit Primitives**
   - [ ] Run audit commands on primitives folder
   - [ ] Document missing test IDs
   - [ ] Create tickets for each missing test ID

2. **Week 2: Add Primitive Test IDs**
   - [ ] Update AppButton
   - [ ] Update AppInput
   - [ ] Update AppSelect
   - [ ] Update AppBadge / AppChip
   - [ ] Update AppCard / AppPanel

3. **Week 3: Add Pattern Test IDs**
   - [ ] Update RightPanel components
   - [ ] Update LinearListRow implementations
   - [ ] Update InlineEditableCell implementations
   - [ ] Update EmptyState implementations

4. **Week 4: Add Feature-Specific Test IDs**
   - [ ] Projects home page components
   - [ ] Workspace tab components
   - [ ] Service/deliverable list components
   - [ ] Review components
   - [ ] Form/dialog components

5. **Week 5: Validate & Update Tests**
   - [ ] Run test suite
   - [ ] Fix any broken selectors
   - [ ] Update tests to use helpers
   - [ ] Add new tests for status validation

---

## Validation Checklist Before Committing

For each test ID added:
- [ ] Test ID follows naming convention
- [ ] Test ID is unique (no duplicates)
- [ ] Test ID is semantic (describes element, not appearance)
- [ ] Test ID is stable (won't change with styling updates)
- [ ] Tests can find the element using the test ID
- [ ] Documentation is updated

---

## Testing the Test IDs

Use this script to verify all expected test IDs exist:

```typescript
// scripts/verify-test-ids.ts

import fs from 'fs';
import path from 'path';

const EXPECTED_TEST_IDS = {
  // Primitives
  'btn-save-primary': 'AppButton[variant=primary]',
  'btn-cancel-secondary': 'AppButton[variant=secondary]',
  'input-project-name': 'AppInput[name=projectName]',
  'select-status': 'AppSelect[name=status]',
  'checkbox-active': 'AppCheckbox',
  'switch-notifications': 'AppSwitch',
  'status-badge-\\d+': 'Status Badge',
  
  // Patterns
  'workspace-services-panel': 'Services Panel',
  'workspace-service-row-\\d+': 'Service Row',
  'deliverable-item-row-\\d+': 'Item Row',
  'cell-title-\\d+': 'Inline Editable Cell',
  
  // Features
  'projects-home-table': 'Projects Table',
  'project-workspace-v2-reviews': 'Reviews Panel',
  'form-dialog-service-create': 'Service Create Dialog',
};

const findTestId = (pattern: string, dir: string): string[] => {
  const results: string[] = [];
  const regex = new RegExp(`data-testid=['"]${pattern}['"]`);
  
  const walk = (filepath: string) => {
    if (fs.statSync(filepath).isDirectory()) {
      fs.readdirSync(filepath).forEach(f => 
        walk(path.join(filepath, f))
      );
    } else if (filepath.endsWith('.tsx') || filepath.endsWith('.ts')) {
      if (regex.test(fs.readFileSync(filepath, 'utf-8'))) {
        results.push(filepath);
      }
    }
  };
  
  walk(dir);
  return results;
};

console.log('Test ID Verification Report\n');
for (const [testId, description] of Object.entries(EXPECTED_TEST_IDS)) {
  const files = findTestId(testId, 'frontend/src/components');
  if (files.length === 0) {
    console.log(`❌ Missing: ${testId} (${description})`);
  } else {
    console.log(`✅ Found: ${testId} in ${files.length} file(s)`);
  }
}
```

Run it with:
```bash
npx ts-node scripts/verify-test-ids.ts
```

---

## Summary

A thorough test ID audit ensures:
- ✅ Tests are stable and maintainable
- ✅ Golden Set components are properly instrumented
- ✅ New patterns can be tested consistently
- ✅ Selectors won't break with UI changes
- ✅ Test code is readable and maintainable

**Next Steps:** Use the audit checklist above to systematically add test IDs to components, then update your test suite to use the new helpers.
