const SERVICE_STATUS_OPTIONS = [
  { label: 'Planned', value: 'planned' },
  { label: 'In progress', value: 'in_progress' },
  { label: 'Completed', value: 'completed' },
  { label: 'Overdue', value: 'overdue' },
  { label: 'Cancelled', value: 'cancelled' },
];

const warnedStatuses = new Set<string>();

const normaliseStatus = (value: string) => value.trim().toLowerCase().replace(/\s+/g, '_');

const findStatusOption = (value: string) => {
  const normalised = normaliseStatus(value);
  return SERVICE_STATUS_OPTIONS.find(
    (option) => normaliseStatus(option.value) === normalised || normaliseStatus(option.label) === normalised,
  );
};

const warnUnknownStatus = (value: string) => {
  if (warnedStatuses.has(value)) {
    return;
  }
  warnedStatuses.add(value);
  console.warn(`[ServiceStatus] Unknown status: ${value}`);
};

const fromApiServiceStatus = (value?: string | null) => {
  if (!value) {
    return null;
  }
  const match = findStatusOption(value);
  if (!match) {
    warnUnknownStatus(value);
    return null;
  }
  return match;
};

const toApiServiceStatus = (value?: string | null) => {
  if (!value) {
    return null;
  }
  const match = findStatusOption(value);
  return match?.value ?? value;
};

const formatServiceStatusLabel = (value?: string | null) => {
  if (!value) {
    return '--';
  }
  const match = findStatusOption(value);
  if (!match) {
    warnUnknownStatus(value);
    return `Unknown (${value})`;
  }
  return match.label;
};

export {
  SERVICE_STATUS_OPTIONS,
  fromApiServiceStatus,
  toApiServiceStatus,
  formatServiceStatusLabel,
};
