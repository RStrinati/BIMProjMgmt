# Custom components catalog

Notes:
- Usage lists show top call sites (first 3-5). Full import references were collected in `docs/ui-audit/_component_import_usage.json`.
- shadcn-style components live under `frontend/src/components/ui/*` and are mostly unused outside the playground.

## Primitive-like and pattern components
| Component | File path | Props surface (brief) | Wraps | Where used (top call sites) |
| --- | --- | --- | --- | --- |
| DetailsPanel | `frontend/src/components/ui/DetailsPanel.tsx` | title, subtitle, actions, children, emptyState | MUI Box/Stack/Typography | `frontend/src/pages/ProjectsPanelPage.tsx`, `frontend/src/pages/BidsPanelPage.tsx` |
| ListView | `frontend/src/components/ui/ListView.tsx` | items, getItemId, renderPrimary/Secondary, selectedId, onSelect/onHover, header, emptyState | MUI List/ListItemButton | `frontend/src/pages/ProjectsPanelPage.tsx`, `frontend/src/pages/BidsPanelPage.tsx`, `frontend/src/features/projects/services/ProjectServicesList.tsx`, `frontend/src/features/projects/services/ProjectServiceReviewsPanel.tsx` |
| InlineField | `frontend/src/components/ui/InlineField.tsx` | label, value, fallback, editor, isEditing | MUI Box/Typography | `frontend/src/pages/ProjectsPanelPage.tsx`, `frontend/src/components/workspace/RightPanel.tsx`, `frontend/src/components/workspace/ServiceDetailPanel.tsx`, `frontend/src/features/projects/services/ProjectServiceDetails.tsx`, `frontend/src/components/projects/ProjectStatusInline.tsx` |
| LinearListContainer | `frontend/src/components/ui/LinearList/LinearListContainer.tsx` | children, sx, variant, elevation | MUI Paper/Box | `frontend/src/pages/workspace/ServicesTab.tsx`, `frontend/src/pages/workspace/DeliverablesTab.tsx`, `frontend/src/pages/ProjectWorkspacePageV2.tsx`, `frontend/src/components/ProjectManagement/ProjectQualityRegisterTab.tsx` |
| LinearListHeaderRow | `frontend/src/components/ui/LinearList/LinearListHeaderRow.tsx` | columns, sx, sticky | MUI Box | `frontend/src/pages/workspace/ServicesTab.tsx`, `frontend/src/pages/workspace/DeliverablesTab.tsx`, `frontend/src/pages/ProjectWorkspacePageV2.tsx`, `frontend/src/components/ProjectManagement/ProjectQualityRegisterTab.tsx` |
| LinearListRow | `frontend/src/components/ui/LinearList/LinearListRow.tsx` | children, columns, sx, testId, onClick, hoverable | MUI Box | `frontend/src/pages/workspace/ServicesTab.tsx`, `frontend/src/pages/workspace/DeliverablesTab.tsx`, `frontend/src/pages/ProjectWorkspacePageV2.tsx`, `frontend/src/components/ProjectManagement/ProjectQualityRegisterTab.tsx` |
| LinearListCell | `frontend/src/components/ui/LinearList/LinearListCell.tsx` | children, variant, align, sx, testId | MUI Typography | `frontend/src/pages/workspace/ServicesTab.tsx`, `frontend/src/pages/workspace/DeliverablesTab.tsx`, `frontend/src/pages/ProjectWorkspacePageV2.tsx`, `frontend/src/components/ProjectManagement/ProjectQualityRegisterTab.tsx` |
| EditableCell | `frontend/src/components/projects/EditableCells.tsx` | value, onSave, isSaving, type, placeholder, testId, onClick | MUI TextField/IconButton | `frontend/src/pages/workspace/DeliverablesTab.tsx`, `frontend/src/pages/ProjectWorkspacePageV2.tsx` |
| ToggleCell | `frontend/src/components/projects/EditableCells.tsx` | value, onSave, isSaving, testId | MUI Typography | `frontend/src/pages/workspace/DeliverablesTab.tsx`, `frontend/src/pages/ProjectWorkspacePageV2.tsx` |
| ProjectFormDialog | `frontend/src/components/ProjectFormDialog.tsx` | open, onClose, project, mode, onSuccess | MUI Dialog | `frontend/src/pages/ProjectsPage.tsx` (lazy), `frontend/src/pages/ProjectsHomePageV2.tsx` (lazy) |
| ServiceDetailDrawer | `frontend/src/components/ProjectServices/ServiceDetailDrawer.tsx` | open, service, projectId, callbacks, formatters | MUI Drawer | `frontend/src/components/ProjectServicesTab_Linear.tsx` |
| RightPanel | `frontend/src/components/workspace/RightPanel.tsx` | project, currentTab, selection, children | MUI Paper/Stack | `frontend/src/pages/WorkspaceShell.tsx` |
| ProjectStatusInline | `frontend/src/components/projects/ProjectStatusInline.tsx` | value, onChange, isSaving, disabled | MUI Select | `frontend/src/pages/ProjectsPanelPage.tsx` |
| ProjectLeadInline | `frontend/src/components/projects/ProjectLeadInline.tsx` | value, users, onChange, isSaving, disabled | MUI Select | `frontend/src/pages/ProjectsPanelPage.tsx` |
| ReviewStatusInline | `frontend/src/components/projects/ReviewStatusInline.tsx` | value, onChange, isSaving, disabled | MUI Select | `frontend/src/features/projects/services/ProjectServiceReviewsPanel.tsx`, `frontend/src/pages/ProjectWorkspacePageV2.tsx` |
| ServiceStatusInline | `frontend/src/components/projects/ServiceStatusInline.tsx` | value, onChange, isSaving, disabled | MUI Select | `frontend/src/features/projects/services/ProjectServiceDetails.tsx` |
| BlockerBadge | `frontend/src/components/ui/BlockerBadge.tsx` | projectId, anchorType, anchorId, enabled, onClick, size, variant | MUI Chip/Tooltip | `frontend/src/components/ProjectServicesTab.tsx`, `frontend/src/pages/ProjectWorkspacePageV2.tsx` |
| LinkedIssuesList | `frontend/src/components/ui/LinkedIssuesList.tsx` | projectId, anchorType, anchorId, enabled, readonly, linkRole | MUI Table + Dialog | `frontend/src/components/ProjectServicesTab.tsx`, `frontend/src/pages/ProjectWorkspacePageV2.tsx` |
| IssuesTabContent | `frontend/src/components/ProjectManagement/IssuesTabContent.tsx` | projectId, selection | MUI Table | `frontend/src/pages/workspace/IssuesTab.tsx`, `frontend/src/pages/ProjectWorkspacePageV2.tsx` |
| TasksNotesView | `frontend/src/components/ProjectManagement/TasksNotesView.jsx` | initialProjectId, hideFilters, hideHeader, onTaskCreated | MUI + DatePicker | `frontend/src/pages/TasksNotesPage.tsx`, `frontend/src/pages/workspace/TasksTab.tsx`, `frontend/src/pages/ProjectWorkspacePageV2.tsx` |

## shadcn/ui components present
These live under `frontend/src/components/ui/*` and use Radix + Tailwind classes. Only the Button is currently imported by app code outside the folder.

| Component | File path | Wraps | Where used |
| --- | --- | --- | --- |
| Button | `frontend/src/components/ui/button.tsx` | Radix Slot + Tailwind | `frontend/src/pages/UiPlaygroundPage.tsx` |
| Badge | `frontend/src/components/ui/badge.tsx` | Tailwind | Unused in app code (no imports found) |
| Card | `frontend/src/components/ui/card.tsx` | Tailwind | Unused in app code (no imports found) |
| Dialog | `frontend/src/components/ui/dialog.tsx` | Radix Dialog + Tailwind | Unused in app code (no imports found) |
| DropdownMenu | `frontend/src/components/ui/dropdown-menu.tsx` | Radix DropdownMenu + Tailwind | Unused in app code (no imports found) |
| Input | `frontend/src/components/ui/input.tsx` | Tailwind | Unused in app code (no imports found) |
| Textarea | `frontend/src/components/ui/textarea.tsx` | Tailwind | Unused in app code (no imports found) |
| Tabs | `frontend/src/components/ui/tabs.tsx` | Radix Tabs + Tailwind | Unused in app code (no imports found) |
| Sheet | `frontend/src/components/ui/sheet.tsx` | Radix Dialog + Tailwind | Unused in app code (no imports found) |
