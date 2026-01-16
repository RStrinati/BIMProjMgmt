/**
 * LinearList Component Library
 * ============================
 *
 * A reusable set of presentational components for building consistent,
 * linear (table-like) list interfaces across the application.
 *
 * COMPONENT CONTRACT:
 * - LinearListContainer: Wrapper with consistent padding, borders, and shadow
 * - LinearListHeaderRow: Grid-aligned header with caption styling and divider
 * - LinearListRow: Grid-aligned data row with hover effects and dividers
 * - LinearListCell: Typography-aware cell wrapper for consistent text rendering
 *
 * STYLING RULES (CONSISTENT ACROSS ALL SCREENS):
 * - Row height: py ~1 (compact)
 * - Dividers: 1px solid theme.palette.divider
 * - Hover: theme.palette.action.hover (background change only, no shadow)
 * - Padding: px 2, py 1 (horizontal 16px, vertical 8px)
 * - Border radius: 1 (4px)
 * - Typography hierarchy:
 *   * Header: caption, fontWeight 600, color text.secondary
 *   * Primary cell: body2, fontWeight 500
 *   * Secondary cell: body2, color text.secondary
 *   * Caption cell: caption, color text.secondary
 *   * Number cell: body2, textAlign right
 *
 * USAGE EXAMPLE:
 *
 * <LinearListContainer>
 *   <LinearListHeaderRow columns={['Name', 'Status', 'Amount']} sticky />
 *   {items.map((item) => (
 *     <LinearListRow key={item.id} columns={3}>
 *       <LinearListCell variant="primary">{item.name}</LinearListCell>
 *       <LinearListCell variant="secondary">{item.status}</LinearListCell>
 *       <LinearListCell variant="number">{item.amount}</LinearListCell>
 *     </LinearListRow>
 *   ))}
 * </LinearListContainer>
 *
 * APPLIES TO:
 * - Projects list (ProjectsHomePageV2)
 * - Services list (ProjectServicesTab_Linear)
 * - Issues list (IssuesPage)
 * - Deliverables list (ProjectWorkspacePageV2)
 */

export { LinearListContainer } from './LinearListContainer';
export { LinearListHeaderRow } from './LinearListHeaderRow';
export { LinearListRow } from './LinearListRow';
export { LinearListCell } from './LinearListCell';
