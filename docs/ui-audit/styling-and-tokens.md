# Styling and tokens audit

## MUI theme configuration
Source: `frontend/src/theme/theme.ts`, `frontend/src/theme/theme-factory.ts`

- Theme provider: `frontend/src/App.tsx` uses `ThemeProvider` and `CssBaseline`.
- Default theme: `professionalLightTheme` from `frontend/src/theme/theme-factory.ts`.

Palette (professional light):
- primary: main `#0066CC`, light `#66A3FF`, dark `#003D7A`
- secondary: main `#9E9E9E`, light `#BDBDBD`, dark `#757575`
- background: default `#FFFFFF`, paper `#FFFFFF`
- text: primary `#1F2937`, secondary `#6B7280`, disabled `#D1D5DB`
- status: success `#16A34A`, warning `#D97706`, error `#DC2626`, info `#0284C7`

Typography:
- fontFamily: `Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, ...`
- sizes: h1 2rem, h2 1.5rem, h3 1.25rem, h4 1rem, body1 0.95rem, body2 0.85rem, caption 0.75rem, button 0.9rem
- button: textTransform none, fontWeight 600

Shape and component overrides:
- global borderRadius: 3px (`shape.borderRadius`)
- Button: radius 3px, padding `8px 12px`, minimal shadows
- Card: radius 3px, 1px border, minimal shadow
- Paper: border + minimal elevation shadows
- Chip: radius 3px, 1px border
- TextField/OutlinedInput: radius 3px, border hover uses accent color
- AppBar: minimal shadow + border bottom
- Tab: textTransform none, selected bottom border

## Tailwind and CSS variables
Sources: `frontend/tailwind.config.js`, `frontend/postcss.config.js`, `frontend/src/index.css`, `frontend/components.json`

Tailwind:
- Config includes CSS variables for `background`, `foreground`, `primary`, `secondary`, `destructive`, `accent`, `border`, `input`, `ring`.
- Border radius tokens: `lg 0.5rem`, `md calc(0.5rem - 2px)`, `sm calc(0.5rem - 4px)`.
- PostCSS uses `@tailwindcss/postcss` + autoprefixer.

CSS variables in `frontend/src/index.css`:
- light: `--background 0 0% 100%`, `--foreground 222.2 84% 4.9%`, `--primary 221.2 83.2% 53.3%`, `--primary-foreground 210 40% 98%`, `--secondary 210 40% 96.1%`, `--secondary-foreground 222.2 47.4% 11.2%`, `--destructive 0 84.2% 60.2%`, `--accent 210 40% 96.1%`, `--border 214.3 31.8% 91.4%`, `--input 214.3 31.8% 91.4%`, `--ring 221.2 83.2% 53.3%`.
- dark: corresponding dark HSL values defined under `.dark`.

## Styling patterns and duplication hotspots
Evidence:
- `sx` usage count: 1228 occurrences (from `docs/ui-audit/_sx_hits.txt`).
- `className` usage count: 47 occurrences, mostly in `frontend/src/components/ui/*` (Tailwind) and `frontend/src/pages/UiPlaygroundPage.tsx`.
- `styled()` usage: none found (`docs/ui-audit/_styled_hits.txt`).
- CSS modules: none found (`docs/ui-audit/_css_module_hits.txt`).

Common repeated patterns (top hotspots):
1) `Paper` + `variant="outlined"` + `sx={{ p: 2 }}` repeated across workspace tabs and panels (`frontend/src/pages/workspace/OverviewTab.tsx`, `frontend/src/pages/workspace/UpdatesTab.tsx`, `frontend/src/components/workspace/RightPanel.tsx`).
2) Table headers with grey backgrounds (`TableRow sx={{ backgroundColor: 'grey.100' }}` or `#f5f5f5`) across issues and project tables (`frontend/src/pages/IssuesPage.tsx`, `frontend/src/components/ProjectManagement/IssuesTabContent.tsx`).
3) Section headings using `Typography` with `fontWeight: 600` in cards/panels across pages (`frontend/src/pages/ProjectsPage.tsx`, `frontend/src/pages/DashboardPage.tsx`).
4) Repeated filter chip rows (Stack + Chip) on Projects and Deliverables (`frontend/src/pages/ProjectsPage.tsx`, `frontend/src/pages/workspace/DeliverablesTab.tsx`).
5) Repeated card grid layouts using `Grid` and `Card` with `sx={{ mb: ... }}` in dashboards (`frontend/src/pages/DashboardPage.tsx`).
6) Repeated inline label/value pairs via `InlineField` and ad hoc `Box` + `Typography` pairs (`frontend/src/components/workspace/RightPanel.tsx`, `frontend/src/pages/ProjectsPage.tsx`).
7) Repeated text field filters with `size="small"` and `sx={{ minWidth: ... }}` (ProjectsHomeV2, IssuesPage, DataImportsPage).
8) Repeated dialog layout (DialogTitle, DialogContent, DialogActions) across pages (Projects, Bids, Settings).
9) Sticky table columns in ProjectsHomeV2 (`getStickyStyles`), likely to be duplicated if more tables are added.
10) LinearList row styles (grid + divider + hover) reused across services/deliverables/quality (`frontend/src/components/ui/LinearList/*.tsx`).

## Token alignment notes (MUI vs Tailwind)
- Primary color mismatch: MUI `#0066CC` vs Tailwind `--primary` HSL (221.2 83.2% 53.3%) yields a different blue.
- Radius mismatch: MUI uses 3px radius; Tailwind uses 8px (`0.5rem`) as `lg` and derived values.
- Typography mismatch: MUI forces Inter/Segoe/Roboto stack; Tailwind does not set a font family in `index.css` so shadcn components fall back to browser defaults unless overridden.
- Spacing scale mismatch: MUI uses an 8px spacing scale via `sx` (e.g., `p: 2` => 16px), while Tailwind defaults to its own scale.
