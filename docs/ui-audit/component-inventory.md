# UI component inventory

## Sources
- Routes and layout: `frontend/src/App.tsx`, `frontend/src/components/layout/MainLayout.tsx`
- Workspace tabs: `frontend/src/pages/WorkspaceShell.tsx`, `frontend/src/pages/workspace/*.tsx`
- Pages: `frontend/src/pages/*.tsx`
- MUI counts: `docs/ui-audit/_mui_usage_by_page.json`, `docs/ui-audit/_mui_usage_by_page.md`

## Route and page inventory
| Route | Page component | Major child components / patterns | Notes |
| --- | --- | --- | --- |
| / | DashboardPage | MUI Card, Table, TablePagination, Tabs, Recharts charts, `TimelinePanel` | Data-heavy dashboard; keep table-heavy widgets in MUI. |
| /projects | ProjectsPage | Conditional: `ProjectsHomePageV2`, `ProjectsPanelPage`, legacy card grid, `ProjectFormDialog` | Core projects entry point; feature flags switch layouts. |
| /projects/:id/workspace | WorkspaceShell | Tabs, `RightPanel`, detail panels | Core workspace shell with nested routes. |
| /projects/:id/workspace/overview | OverviewTab | Paper cards, update composer, task preview list | Core workspace tab. |
| /projects/:id/workspace/services | ServicesTab | `LinearList*`, MUI Menu, Dialog | Core workspace tab; row selection updates right panel. |
| /projects/:id/workspace/services/new | ServiceCreateView | Accordion form, selects, checkboxes | Service creation flow. |
| /projects/:id/workspace/services/:serviceId | ServiceEditView | Accordion form, Dialogs, Autocomplete | Service edit flow; data-heavy form. |
| /projects/:id/workspace/deliverables | DeliverablesTab | `LinearList*`, `EditableCell`, `ToggleCell`, TextField select | Core workspace tab. |
| /projects/:id/workspace/updates | UpdatesTab | Paper list, chips | Core workspace tab. |
| /projects/:id/workspace/issues | IssuesTab | `IssuesTabContent` (MUI Table) | Core workspace tab. |
| /projects/:id/workspace/tasks | TasksTab | `TasksNotesView` (MUI + DatePicker) | Core workspace tab. |
| /projects/:id/workspace/quality | QualityTab | `QualityTab` wrapper | Core workspace tab. |
| /projects/:id | Navigate | Redirects to `/projects/:id/workspace/overview` | Legacy route. |
| /projects/:id/data-imports | DataImportsPage | MUI Tabs, ACC panels, lists | Admin-style flow per project. |
| /data-imports | DataImportsPage | Same as above | Project selector controls content. |
| /bids | BidsListPage | Table, Dialog form; optional `BidsPanelPage` | Feature flag `bidsPanel` swaps layout. |
| /bids/:id | BidDetailPage | Tabs, Accordions, Tables, Dialogs | Data-heavy bid workspace. |
| /issues | IssuesPage | MUI Table, filters, pagination | Feature flag `issuesHub`. |
| /tasks | TasksNotesPage | `TasksNotesView` | Legacy tasks page. |
| /settings | SettingsPage | Tabs, Tables, Dialogs | Admin/settings screens. |
| /ui | UiPlaygroundPage | shadcn Button examples | Shadcn playground only. |
| /reviews | Navigate | Redirects to `/projects` | Legacy route. |
| * | Navigate | Redirects to `/` | Catch-all. |

## Core flows (explicit)
- Projects list/board/timeline: `frontend/src/pages/ProjectsHomePageV2.tsx` (feature-flagged via `ProjectsPage`)
- Project workspace tabs: `frontend/src/pages/WorkspaceShell.tsx` with `frontend/src/pages/workspace/{OverviewTab,ServicesTab,DeliverablesTab,IssuesTab,TasksTab,QualityTab,UpdatesTab}.tsx`
- Settings/admin screens: `frontend/src/pages/SettingsPage.tsx`, `frontend/src/pages/DataImportsPage.tsx`

## MUI usage inventory (by page)
Full per-page component counts (exact occurrences) are in:
- `docs/ui-audit/_mui_usage_by_page.md`
- `docs/ui-audit/_mui_usage_by_page.json`

Heavy widget notes (page -> widgets):
| Page | Heavy widgets / notes |
| --- | --- |
| `frontend/src/pages/DashboardPage.tsx` | Table, TablePagination, Tabs, Recharts charts, TimelinePanel |
| `frontend/src/pages/ProjectsHomePageV2.tsx` | Table, TableSortLabel, ToggleButtonGroup, `ProjectColumnsPopover` (MUI Popover) |
| `frontend/src/pages/ProjectsPage.tsx` | Dialog (ProjectFormDialog), card grid, filter chips |
| `frontend/src/pages/ProjectsPanelPage.tsx` | Tabs + side panel layout using `ListView` + `DetailsPanel` |
| `frontend/src/pages/WorkspaceShell.tsx` | Tabs + sticky right panel |
| `frontend/src/pages/workspace/ServicesTab.tsx` | Dialog + Menu overlays; `LinearList*` |
| `frontend/src/pages/workspace/DeliverablesTab.tsx` | Editable rows with TextField selects; `LinearList*` |
| `frontend/src/pages/workspace/TasksTab.tsx` | TasksNotesView (DatePicker inside `TasksNotesView.jsx`) |
| `frontend/src/pages/workspace/IssuesTab.tsx` | IssuesTabContent (Table) |
| `frontend/src/pages/workspace/QualityTab.tsx` | Wrapper around `QualityTab` |
| `frontend/src/pages/DataImportsPage.tsx` | Tabs + select-heavy filters |
| `frontend/src/pages/IssuesPage.tsx` | Table + TablePagination |
| `frontend/src/pages/BidsListPage.tsx` | Dialog + Table |
| `frontend/src/pages/BidDetailPage.tsx` | Tabs + Accordions + Dialogs + Tables |
| `frontend/src/pages/SettingsPage.tsx` | Tabs + Dialogs + Tables |
| `frontend/src/pages/UiPlaygroundPage.tsx` | shadcn Button demo only |

## Non-routed/legacy pages (in repo)
- `frontend/src/pages/ProjectWorkspacePageV2.tsx` (legacy workspace view, not wired in `App.tsx`)
- `frontend/src/pages/ProjectDetailPage.tsx` (legacy detail page, not routed)
- `frontend/src/pages/AnalyticsPage.tsx` (not routed)
- `frontend/src/pages/ServiceTemplatesPage.tsx` (not routed; settings feature likely moved into tabs)
