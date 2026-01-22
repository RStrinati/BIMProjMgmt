# Overlay and z-index audit

## Overlay components by source

MUI overlays
- Dialog: `frontend/src/components/ProjectFormDialog.tsx`, `frontend/src/pages/BidsListPage.tsx`, `frontend/src/pages/BidDetailPage.tsx`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/pages/workspace/ServicesTab.tsx`, `frontend/src/pages/workspace/ServiceEditView.tsx`, `frontend/src/pages/ProjectWorkspacePageV2.tsx`, `frontend/src/components/ui/LinkedIssuesList.tsx`.
- Drawer: `frontend/src/components/layout/MainLayout.tsx` (nav drawers), `frontend/src/components/ProjectServices/ServiceDetailDrawer.tsx`.
- Menu: `frontend/src/pages/workspace/ServicesTab.tsx` (Add Service menu).
- Popover: `frontend/src/features/projects/fields/ProjectColumnsPopover.tsx`.
- Tooltip: used across pages and components (`frontend/src/pages/ProjectsPage.tsx`, `frontend/src/components/ui/LinkedIssuesList.tsx`).
- Snackbar: `frontend/src/pages/ProjectWorkspacePageV2.tsx`.

Radix (shadcn/ui) overlays (present but not used in app flow)
- Dialog: `frontend/src/components/ui/dialog.tsx` (Radix Dialog + Tailwind, z-50).
- Sheet: `frontend/src/components/ui/sheet.tsx` (Radix Dialog + Tailwind, z-50).
- DropdownMenu: `frontend/src/components/ui/dropdown-menu.tsx` (Radix DropdownMenu + Tailwind, z-50).

## z-index and stacking notes
Evidence sources: `docs/ui-audit/_zindex_hits.txt`, `docs/ui-audit/_overlay_hits.txt`

- `frontend/src/pages/ProjectsPage.tsx` and `frontend/src/pages/ProjectsHomePageV2.tsx` set a Suspense fallback overlay with `zIndex: theme.zIndex.modal - 1`.
- `frontend/src/components/ui/LinearList/LinearListHeaderRow.tsx` uses `zIndex: 2` for sticky headers.
- `frontend/src/pages/ProjectsHomePageV2.tsx` uses `getStickyStyles` with explicit `zIndex` for pinned table columns.
- `frontend/src/components/DashboardTimelineChart.tsx` uses multiple `zIndex` values to layer chart overlays.
- Radix overlays use `z-50` classes in `dialog.tsx` and `sheet.tsx`.

## Focus and portal configuration
- `frontend/src/components/layout/MainLayout.tsx` uses MUI Drawer with `ModalProps={{ keepMounted: true }}` for mobile drawers.
- `frontend/src/pages/ProjectWorkspacePageV2.tsx` uses MUI Dialog with `keepMounted` for the linked issues modal.
- No `disableEnforceFocus`, `disablePortal`, or `disableAutoFocus` found (`docs/ui-audit/_focus_portal_hits.txt`).

## Risk notes
- Moving Dialog/Drawer primitives off MUI will impact tests referencing `.MuiDialog` or `.MuiDrawer` class names.
- Sticky table z-index logic in ProjectsHomeV2 is tied to MUI Table layout; a new table implementation will need equivalent z-index layering for pinned columns.
