# Golden Set UI Standard

This document defines the P0/P1/P2 golden set for the UI Playground at `/ui`.
The goal is a stable, reusable set of primitives and patterns that Workspace
tabs adopt first.

## P0 - Golden Primitives

- AppButton (primary, secondary, outline, ghost, link, destructive)
- AppInput (text, search, number with helper and error messaging)
- AppSelect (single select with placeholder, disabled, error)
- AppTextarea
- AppCheckbox and AppSwitch
- AppBadge / AppChip
- AppCard / AppPanel (standard padding, radius, shadow, header slot)
- AppDivider
- AppIconButton

## P0 - Golden Patterns

- RightPanel (fixed width, scroll behavior, empty state)
- RightPanelSection (collapsible, title + optional action button)
- LinearListRow (left title/subtitle, middle chips, right status + actions)
- InlineEditableCell (text, select, toggle with dirty indicator)
- EmptyState (lists and right panel)
- KpiStrip and KpiCard

## P1 - Overlays and Navigation

- AppDialog (confirm and form dialogs)
- AppMenu / AppDropdown (kebab actions: Edit, Delete, Archive)
- AppTabs (workspace tab styling)
- Toast / Notification (optional)

## P2 - Form Patterns and Admin Pages

- Form section blocks (accordion-like layout)
- Autocomplete wrapper (keep MUI)
- Date picker wrapper (keep MUI)

## Status Mapping

| Status   | Visual intent | Notes |
| -------- | ------------- | ----- |
| Draft    | neutral       | muted / secondary |
| Active   | primary       | strong emphasis |
| Blocked  | destructive   | warning or error tone |
| Done     | success       | positive completion |
| Overdue  | destructive   | urgent and visible |
| On Hold  | muted         | de-emphasized |

## Density Rules

- Comfortable
  - LinearListRow vertical padding: ~10-12px
  - Card/panel padding: ~24px
  - Metadata line font size: 14px
- Compact
  - LinearListRow vertical padding: ~6-8px
  - Card/panel padding: ~16px
  - Metadata line font size: 12px

## Adoption Rule

When a primitive or pattern exists under `frontend/src/components/primitives`,
production pages should import from that wrapper before using raw MUI or shadcn
components. The wrappers are the stability layer for gradual migration.
