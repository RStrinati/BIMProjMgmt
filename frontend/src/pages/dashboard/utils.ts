export const ISSUE_STATUS_GROUPS = {
  active: ['open', 'in_progress', 'reopened', 'pending', 'on_hold'],
  closed: ['closed', 'completed', 'resolved'],
};

export const normalizeIssueStatus = (value?: string | null) =>
  (value ?? '').trim().toLowerCase();

export const groupIssueStatus = (value?: string | null) => {
  const normalized = normalizeIssueStatus(value);
  if (ISSUE_STATUS_GROUPS.active.includes(normalized)) return 'Active';
  if (ISSUE_STATUS_GROUPS.closed.includes(normalized)) return 'Closed';
  return 'Other';
};

export const formatNumber = (value?: number | null) => {
  if (value == null) return '0';
  return value.toLocaleString();
};

export const formatDateTime = (value?: string | null) => {
  if (!value) return '--';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
};

export const formatDate = (value?: string | null) => {
  if (!value) return '--';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
};

export const isZeroCoordinate = (value?: number | null) => value != null && Math.abs(value) < 0.0001;
