# Test coverage impact (markup changes)

## Test types present
- Playwright e2e: `frontend/tests/e2e/*.spec.ts` (configured in `frontend/playwright.config.ts`).
- No Jest/RTL unit tests or snapshot tests found in `frontend`.

## Selectors and assertions likely to churn
- MUI class name selectors:
  - `frontend/tests/e2e/workspace-issues-panel.spec.ts` asserts `.MuiDrawer-root` absence and `Mui-selected` class on rows.
  - `frontend/tests/e2e/anchor-linking.spec.ts` inspects `.MuiDialog` and `.MuiPortal` elements.
- Table DOM structure assumptions:
  - `frontend/tests/e2e/projects-home-v2-columns.spec.ts` reads `thead th` and `tfoot` content under `[data-testid="projects-list-table"]`.
  - `frontend/tests/e2e/issues-hub.spec.ts` assumes table rows via `[data-testid^="issues-row-"]`.
- Data-testid coverage is good but still coupled to MUI-driven layouts:
  - Workspace tabs and panels rely on `data-testid` from MUI render trees (`workspace-issues-panel.spec.ts`, `workspace-services-panel.spec.ts`, `workspace-updates.spec.ts`).

## Files most likely to break if swapping primitives
- `frontend/tests/e2e/workspace-issues-panel.spec.ts` (relies on `.Mui` classes + row selection behavior).
- `frontend/tests/e2e/anchor-linking.spec.ts` (explicit MUI Dialog/Portal checks).
- `frontend/tests/e2e/projects-home-v2-columns.spec.ts` (table header/footer structure).
- `frontend/tests/e2e/workspace-services-panel.spec.ts` (LinearList data-testid and row structure).

## Mitigation recommendations
- Introduce wrapper primitives with stable `data-testid` attributes for tables, dialogs, and panels.
- Replace `.Mui*` class assertions with role-based selectors or `data-testid` for stability.
- Add explicit `data-testid` for row selection state (e.g., `data-selected`) to avoid class coupling.
- For table-heavy pages, keep MUI table structure during initial migration stages to reduce e2e churn.
