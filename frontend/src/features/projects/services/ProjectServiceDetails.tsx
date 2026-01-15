import { Alert, Box, Stack, Typography } from '@mui/material';
import type { ReactNode } from 'react';
import { InlineField } from '@/components/ui/InlineField';
import { ServiceStatusInline } from '@/components/projects/ServiceStatusInline';
import type { ProjectService } from '@/api/services';

type ProjectServiceDetailsProps = {
  service: ProjectService | null;
  onStatusChange: (value: string | null) => void;
  isSaving?: boolean;
  disabled?: boolean;
  saveError?: string | null;
  testIdPrefix?: string;
  extraDetails?: ReactNode;
};

const formatCurrency = (value?: number | null) => {
  if (value == null || Number.isNaN(Number(value))) {
    return '--';
  }
  return new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(Number(value));
};

const formatNumber = (value?: number | null, suffix?: string) => {
  if (value == null || Number.isNaN(Number(value))) {
    return '--';
  }
  const formatted = Number(value).toLocaleString();
  return suffix ? `${formatted} ${suffix}` : formatted;
};

export function ProjectServiceDetails({
  service,
  onStatusChange,
  isSaving = false,
  disabled = false,
  saveError,
  testIdPrefix = 'projects-panel',
  extraDetails,
}: ProjectServiceDetailsProps) {
  if (!service) {
    return (
      <Typography color="text.secondary">
        Select a service to view details.
      </Typography>
    );
  }

  return (
    <Stack spacing={2}>
      {saveError && (
        <Alert severity="error" data-testid={`${testIdPrefix}-service-save-error`}>
          {saveError}
        </Alert>
      )}
      <InlineField label="Service code" value={service.service_code} />
      <InlineField label="Service name" value={service.service_name} />
      <InlineField label="Phase" value={service.phase} />
      <ServiceStatusInline
        value={service.status ?? null}
        onChange={onStatusChange}
        isSaving={isSaving}
        disabled={disabled}
      />
      <InlineField label="Progress" value={formatNumber(service.progress_pct, '%')} />
      <InlineField label="Agreed fee" value={formatCurrency(service.agreed_fee)} />
      <InlineField
        label="Billed"
        value={formatCurrency(service.billed_amount ?? service.claimed_to_date)}
      />
      {extraDetails ? <Box>{extraDetails}</Box> : null}
    </Stack>
  );
}
