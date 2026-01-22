import type { ReactNode } from 'react';
import type { ProjectSummary } from '@/types/api';
import { Chip, Typography } from '@mui/material';

export type ProjectFieldFormat = 'text' | 'number' | 'date' | 'currency' | 'percent' | 'user';
export type ProjectFieldAggregate = 'none' | 'sum' | 'avg' | 'weighted_ev_pct';
export type ProjectFieldView = 'list' | 'board' | 'timeline';

export type ProjectFieldDefinition = {
  id: string;
  label: string;
  format: ProjectFieldFormat;
  aggregatable: ProjectFieldAggregate;
  editable: boolean;
  defaultVisibility: Record<ProjectFieldView, boolean>;
  accessor: (project: ProjectSummary) => unknown;
  width?: number;
  align?: 'left' | 'right' | 'center';
  renderListCell?: (project: ProjectSummary) => ReactNode;
  renderBoardSnippet?: (project: ProjectSummary) => ReactNode;
  renderTimelineMeta?: (project: ProjectSummary) => ReactNode;
};

const currencyFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const numberFormatter = new Intl.NumberFormat('en-US');

const formatPercent = (value?: number | null) => {
  if (value == null || Number.isNaN(Number(value))) {
    return '--';
  }
  return `${Math.round(Number(value))}%`;
};

const formatDate = (value?: string | null) => {
  if (!value) {
    return '--';
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return '--';
  }
  return parsed.toLocaleDateString();
};

const resolvePriorityLabel = (value: ProjectSummary['priority'], fallback?: ProjectSummary['priority_label']) => {
  if (fallback) {
    return fallback;
  }
  if (value == null) {
    return '--';
  }
  if (typeof value === 'number') {
    return value === 4 ? 'Critical' : value === 3 ? 'High' : value === 2 ? 'Medium' : 'Low';
  }
  const trimmed = value.toString().trim();
  if (!trimmed) {
    return '--';
  }
  if (/^\d+$/.test(trimmed)) {
    return resolvePriorityLabel(Number(trimmed));
  }
  return trimmed;
};

const resolveUserLabel = (project: ProjectSummary) => {
  if (project.internal_lead_name && project.internal_lead_name.trim()) {
    return project.internal_lead_name;
  }
  if (project.internal_lead != null) {
    return `User ${project.internal_lead}`;
  }
  return '--';
};

const formatValue = (format: ProjectFieldFormat, value: unknown, project?: ProjectSummary) => {
  if (format === 'currency') {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? currencyFormatter.format(numeric) : '--';
  }
  if (format === 'number') {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numberFormatter.format(numeric) : '--';
  }
  if (format === 'percent') {
    return formatPercent(value as number);
  }
  if (format === 'date') {
    return formatDate(value as string | null);
  }
  if (format === 'user') {
    return resolveUserLabel(project ?? ({} as ProjectSummary));
  }
  const stringValue = value == null ? '' : String(value);
  return stringValue.trim() ? stringValue : '--';
};

const getStatusColor = (status?: string | null) => {
  switch ((status || '').toLowerCase()) {
    case 'active':
      return 'success';
    case 'on hold':
    case 'on_hold':
      return 'warning';
    case 'completed':
      return 'default';
    default:
      return 'default';
  }
};

export const PROJECT_FIELD_REGISTRY: ProjectFieldDefinition[] = [
  {
    id: 'project_name',
    label: 'Project',
    format: 'text',
    aggregatable: 'none',
    editable: true,
    defaultVisibility: { list: true, board: true, timeline: true },
    accessor: (project) => project.project_name,
    width: 240,
    renderBoardSnippet: (project) => (
      <Typography variant="body2" fontWeight={600}>
        {formatValue('text', project.project_name)}
      </Typography>
    ),
  },
  {
    id: 'project_number',
    label: 'Project #',
    format: 'text',
    aggregatable: 'none',
    editable: true,
    defaultVisibility: { list: true, board: false, timeline: false },
    accessor: (project) => project.project_number ?? project.contract_number,
    width: 140,
  },
  {
    id: 'client_name',
    label: 'Client',
    format: 'text',
    aggregatable: 'none',
    editable: false,
    defaultVisibility: { list: false, board: true, timeline: true },
    accessor: (project) => project.client_name,
  },
  {
    id: 'status',
    label: 'Status',
    format: 'text',
    aggregatable: 'none',
    editable: true,
    defaultVisibility: { list: true, board: false, timeline: false },
    accessor: (project) => project.status,
    renderListCell: (project) => (
      <Typography
        variant="body2"
        sx={{
          color:
            getStatusColor(project.status) === 'success'
              ? 'success.main'
              : getStatusColor(project.status) === 'warning'
                ? 'warning.main'
                : 'text.primary',
        }}
      >
        {formatValue('text', project.status)}
      </Typography>
    ),
  },
  {
    id: 'priority',
    label: 'Priority',
    format: 'text',
    aggregatable: 'none',
    editable: true,
    defaultVisibility: { list: true, board: false, timeline: true },
    accessor: (project) => project.priority_label ?? project.priority,
    renderListCell: (project) => formatValue('text', resolvePriorityLabel(project.priority, project.priority_label)),
  },
  {
    id: 'internal_lead',
    label: 'Lead',
    format: 'user',
    aggregatable: 'none',
    editable: true,
    defaultVisibility: { list: true, board: false, timeline: true },
    accessor: (project) => resolveUserLabel(project),
  },
  {
    id: 'project_manager',
    label: 'Manager',
    format: 'text',
    aggregatable: 'none',
    editable: true,
    defaultVisibility: { list: false, board: false, timeline: false },
    accessor: (project) => project.project_manager,
  },
  {
    id: 'start_date',
    label: 'Start',
    format: 'date',
    aggregatable: 'none',
    editable: true,
    defaultVisibility: { list: false, board: false, timeline: true },
    accessor: (project) => project.start_date,
  },
  {
    id: 'end_date',
    label: 'Target',
    format: 'date',
    aggregatable: 'none',
    editable: true,
    defaultVisibility: { list: true, board: true, timeline: true },
    accessor: (project) => project.end_date,
  },
  {
    id: 'health_pct',
    label: 'Health %',
    format: 'percent',
    aggregatable: 'none',
    editable: false,
    defaultVisibility: { list: true, board: true, timeline: false },
    accessor: (project) => project.health_pct,
    renderBoardSnippet: (project) => (
      <Chip
        size="small"
        color="primary"
        variant="outlined"
        label={`Health: ${formatValue('percent', project.health_pct)}`}
      />
    ),
  },
  {
    id: 'agreed_fee',
    label: 'Agreed Fee',
    format: 'currency',
    aggregatable: 'sum',
    editable: false,
    defaultVisibility: { list: false, board: false, timeline: false },
    accessor: (project) => project.agreed_fee,
    align: 'right',
  },
  {
    id: 'billed_to_date',
    label: 'Billed',
    format: 'currency',
    aggregatable: 'sum',
    editable: false,
    defaultVisibility: { list: false, board: false, timeline: false },
    accessor: (project) => project.billed_to_date,
    align: 'right',
  },
  {
    id: 'unbilled_amount',
    label: 'Unbilled',
    format: 'currency',
    aggregatable: 'sum',
    editable: false,
    defaultVisibility: { list: false, board: false, timeline: false },
    accessor: (project) => project.unbilled_amount,
    align: 'right',
  },
  {
    id: 'earned_value',
    label: 'Earned Value',
    format: 'currency',
    aggregatable: 'sum',
    editable: false,
    defaultVisibility: { list: false, board: false, timeline: false },
    accessor: (project) => project.earned_value,
    align: 'right',
  },
  {
    id: 'earned_value_pct',
    label: 'EV %',
    format: 'percent',
    aggregatable: 'weighted_ev_pct',
    editable: false,
    defaultVisibility: { list: false, board: false, timeline: false },
    accessor: (project) => project.earned_value_pct,
    align: 'right',
  },
  {
    id: 'invoice_pipeline_this_month',
    label: 'Pipeline (This Month)',
    format: 'currency',
    aggregatable: 'sum',
    editable: false,
    defaultVisibility: { list: false, board: false, timeline: false },
    accessor: (project) => project.invoice_pipeline_this_month,
    align: 'right',
  },
  {
    id: 'ready_to_invoice_this_month',
    label: 'Ready to Invoice (This Month)',
    format: 'currency',
    aggregatable: 'sum',
    editable: false,
    defaultVisibility: { list: false, board: false, timeline: false },
    accessor: (project) => project.ready_to_invoice_this_month,
    align: 'right',
  },
];

export const PROJECT_FIELD_MAP = new Map(PROJECT_FIELD_REGISTRY.map((field) => [field.id, field]));

export const getDefaultVisibleFieldIds = (view: ProjectFieldView) =>
  PROJECT_FIELD_REGISTRY.filter((field) => field.defaultVisibility[view]).map((field) => field.id);

export const getDefaultOrderedFieldIds = () => PROJECT_FIELD_REGISTRY.map((field) => field.id);

export const renderFieldValue = (field: ProjectFieldDefinition, project: ProjectSummary) => {
  if (field.renderListCell) {
    return field.renderListCell(project);
  }
  return formatValue(field.format, field.accessor(project), project);
};

export const getFieldValue = (field: ProjectFieldDefinition, project: ProjectSummary) =>
  field.accessor(project);

export const formatProjectValue = (field: ProjectFieldDefinition, project: ProjectSummary) =>
  formatValue(field.format, field.accessor(project), project);

export const renderBoardSnippet = (field: ProjectFieldDefinition, project: ProjectSummary) => {
  if (field.renderBoardSnippet) {
    return field.renderBoardSnippet(project);
  }
  const value = formatValue(field.format, field.accessor(project), project);
  return (
    <Typography variant="caption" color="text.secondary">
      {field.label}: {value}
    </Typography>
  );
};

export const renderTimelineMeta = (field: ProjectFieldDefinition, project: ProjectSummary) => {
  if (field.renderTimelineMeta) {
    return field.renderTimelineMeta(project);
  }
  const value = formatValue(field.format, field.accessor(project), project);
  return (
    <Typography variant="caption" color="text.secondary">
      {field.label}: {value}
    </Typography>
  );
};
