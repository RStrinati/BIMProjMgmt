import type { ReactNode } from 'react';
import type { MasterUser } from '@/types/api';
import { Chip, Typography } from '@mui/material';

export type UserFieldFormat = 'text' | 'number' | 'date' | 'boolean';
export type UserFieldView = 'list';

export type UserFieldDefinition = {
  id: string;
  label: string;
  format: UserFieldFormat;
  defaultVisibility: Record<UserFieldView, boolean>;
  accessor: (user: MasterUser) => unknown;
  width?: number;
  align?: 'left' | 'right' | 'center';
  renderListCell?: (user: MasterUser) => ReactNode;
};

const numberFormatter = new Intl.NumberFormat('en-US');

const formatDate = (value?: string | null) => {
  if (!value) return '--';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '--';
  return parsed.toLocaleDateString();
};

const formatBoolean = (value?: boolean | null) => {
  if (value === true) return 'Yes';
  if (value === false) return 'No';
  return '--';
};

const formatValue = (format: UserFieldFormat, value: unknown) => {
  if (format === 'number') {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numberFormatter.format(numeric) : '--';
  }
  if (format === 'date') {
    return formatDate(value as string | null);
  }
  if (format === 'boolean') {
    return formatBoolean(value as boolean | null);
  }
  const stringValue = value == null ? '' : String(value);
  return stringValue.trim() ? stringValue : '--';
};

const renderBooleanChip = (value?: boolean | null) => (
  <Chip
    size="small"
    label={formatBoolean(value)}
    color={value ? 'success' : value === false ? 'default' : 'warning'}
    variant="outlined"
  />
);

export const USER_FIELD_REGISTRY: UserFieldDefinition[] = [
  {
    id: 'name',
    label: 'Name',
    format: 'text',
    defaultVisibility: { list: true },
    accessor: (user) => user.name,
    width: 200,
  },
  {
    id: 'email',
    label: 'Email',
    format: 'text',
    defaultVisibility: { list: true },
    accessor: (user) => user.email,
    width: 240,
  },
  {
    id: 'company',
    label: 'Company',
    format: 'text',
    defaultVisibility: { list: true },
    accessor: (user) => user.company,
    width: 180,
  },
  {
    id: 'role',
    label: 'Role/Position',
    format: 'text',
    defaultVisibility: { list: true },
    accessor: (user) => user.role,
    width: 180,
  },
  {
    id: 'source_system',
    label: 'Source',
    format: 'text',
    defaultVisibility: { list: true },
    accessor: (user) => user.source_system,
    width: 120,
    renderListCell: (user) => (
      <Chip size="small" label={formatValue('text', user.source_system)} variant="outlined" />
    ),
  },
  {
    id: 'license_type',
    label: 'License',
    format: 'text',
    defaultVisibility: { list: true },
    accessor: (user) => user.license_type,
    width: 180,
  },
  {
    id: 'last_active',
    label: 'Last Active',
    format: 'date',
    defaultVisibility: { list: true },
    accessor: (user) => user.last_active,
    width: 130,
  },
  {
    id: 'last_active_source',
    label: 'Last Active Source',
    format: 'text',
    defaultVisibility: { list: false },
    accessor: (user) => user.last_active_source,
    width: 140,
  },
  {
    id: 'invited_to_bim_meetings',
    label: 'BIM Meetings',
    format: 'boolean',
    defaultVisibility: { list: true },
    accessor: (user) => user.invited_to_bim_meetings,
    width: 140,
    renderListCell: (user) => renderBooleanChip(user.invited_to_bim_meetings),
  },
  {
    id: 'is_watcher',
    label: 'Watcher',
    format: 'boolean',
    defaultVisibility: { list: false },
    accessor: (user) => user.is_watcher,
    width: 120,
    renderListCell: (user) => renderBooleanChip(user.is_watcher),
  },
  {
    id: 'is_assignee',
    label: 'Assignee',
    format: 'boolean',
    defaultVisibility: { list: false },
    accessor: (user) => user.is_assignee,
    width: 120,
    renderListCell: (user) => renderBooleanChip(user.is_assignee),
  },
  {
    id: 'status',
    label: 'Status',
    format: 'text',
    defaultVisibility: { list: false },
    accessor: (user) => user.status,
    width: 120,
    renderListCell: (user) => (
      <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
        {formatValue('text', user.status)}
      </Typography>
    ),
  },
  {
    id: 'phone',
    label: 'Phone',
    format: 'text',
    defaultVisibility: { list: false },
    accessor: (user) => user.phone,
    width: 140,
  },
  {
    id: 'project_count',
    label: 'Projects',
    format: 'number',
    defaultVisibility: { list: false },
    accessor: (user) => user.project_count,
    align: 'right',
    width: 110,
  },
  {
    id: 'acc_project_count',
    label: 'ACC Projects',
    format: 'number',
    defaultVisibility: { list: false },
    accessor: (user) => user.acc_project_count,
    align: 'right',
    width: 120,
  },
  {
    id: 'revizto_project_count',
    label: 'Revizto Projects',
    format: 'number',
    defaultVisibility: { list: false },
    accessor: (user) => user.revizto_project_count,
    align: 'right',
    width: 140,
  },
  {
    id: 'access_level',
    label: 'Access Level',
    format: 'text',
    defaultVisibility: { list: false },
    accessor: (user) => user.access_level,
    width: 140,
  },
];

export const USER_FIELD_MAP = new Map(USER_FIELD_REGISTRY.map((field) => [field.id, field]));

export const getDefaultVisibleFieldIds = (view: UserFieldView) =>
  USER_FIELD_REGISTRY.filter((field) => field.defaultVisibility[view]).map((field) => field.id);

export const getDefaultOrderedFieldIds = () => USER_FIELD_REGISTRY.map((field) => field.id);

export const renderFieldValue = (field: UserFieldDefinition, user: MasterUser) => {
  if (field.renderListCell) {
    return field.renderListCell(user);
  }
  return formatValue(field.format, field.accessor(user));
};

export const getFieldValue = (field: UserFieldDefinition, user: MasterUser) =>
  field.accessor(user);
