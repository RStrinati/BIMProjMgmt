import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { Alert, Stack, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { projectServicesApi, type ProjectService, type ProjectServicesListResponse } from '@/api/services';
import { useUpdateServiceStatus } from '@/hooks/useUpdateServiceStatus';
import { ListView } from '@/components/ui/ListView';
import { formatServiceStatusLabel } from '@/utils/serviceStatus';
import { ProjectServiceDetails } from './ProjectServiceDetails';
import { ServicePlanningPanel } from './ServicePlanningPanel';

type ProjectServicesListProps = {
  projectId: number;
  initialSelectedServiceId?: number | null;
  onSelect?: (service: ProjectService | null) => void;
  params?: { page?: number; limit?: number };
  testIdPrefix?: string;
  renderExtraDetails?: (service: ProjectService | null) => ReactNode;
};

const stableSerialize = (value: Record<string, unknown>) =>
  JSON.stringify(value, Object.keys(value).sort());

const formatCurrency = (value?: number | null) => {
  if (value == null || Number.isNaN(Number(value))) {
    return '--';
  }
  return new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(Number(value));
};

export function ProjectServicesList({
  projectId,
  initialSelectedServiceId = null,
  onSelect,
  params,
  testIdPrefix = 'projects-panel',
  renderExtraDetails,
}: ProjectServicesListProps) {
  const queryClient = useQueryClient();
  const updateServiceStatus = useUpdateServiceStatus();
  const [selectedServiceId, setSelectedServiceId] = useState<number | null>(initialSelectedServiceId);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [planningError, setPlanningError] = useState<string | null>(null);

  // Mutation for updating execution intent
  const updateExecutionIntent = useMutation({
    mutationFn: async ({
      serviceId,
      intent,
      reason,
    }: {
      serviceId: number;
      intent: 'planned' | 'optional' | 'not_proceeding';
      reason?: string | null;
    }) => {
      const response = await fetch(
        `/api/projects/${projectId}/services/${serviceId}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            executionIntent: intent,
            decisionReason: reason || null,
          }),
        }
      );
      if (!response.ok) {
        throw new Error('Failed to update service plan');
      }
      return response.json();
    },
    onSuccess: () => {
      // Invalidate services query to refetch updated data
      queryClient.invalidateQueries({ queryKey: ['projectServices', projectId] });
      setPlanningError(null);
    },
    onError: (error: Error) => {
      setPlanningError(error.message || 'Failed to update plan');
    },
  });

  useEffect(() => {
    if (initialSelectedServiceId != null) {
      setSelectedServiceId(initialSelectedServiceId);
    }
  }, [initialSelectedServiceId]);

  const paramsKey = useMemo(() => stableSerialize(params ?? {}), [params]);
  const paramsStable = useMemo(() => params ?? {}, [paramsKey]);
  const { data: servicesPayload, isLoading, isError } = useQuery<ProjectServicesListResponse>({
    queryKey: ['projectServices', projectId, paramsStable],
    queryFn: () => projectServicesApi.getAll(projectId, paramsStable),
    staleTime: 60_000,
    retry: 1,
    refetchOnWindowFocus: false,
    keepPreviousData: true,
  });

  const services = useMemo<ProjectService[]>(() => {
    if (!servicesPayload) {
      return [];
    }
    if (Array.isArray(servicesPayload)) {
      return servicesPayload;
    }
    const items = servicesPayload.items ?? servicesPayload.services ?? servicesPayload.results;
    return Array.isArray(items) ? items : [];
  }, [servicesPayload]);

  useEffect(() => {
    if (!services.length) {
      if (selectedServiceId !== null) {
        setSelectedServiceId(null);
        onSelect?.(null);
      }
      return;
    }
    const exists = selectedServiceId != null && services.some((service) => service.service_id === selectedServiceId);
    if (!exists) {
      setSelectedServiceId(services[0].service_id);
    }
  }, [services, selectedServiceId, onSelect]);

  useEffect(() => {
    if (!onSelect) {
      return;
    }
    if (selectedServiceId == null) {
      onSelect(null);
      return;
    }
    const selected = services.find((service) => service.service_id === selectedServiceId) ?? null;
    if (selected) {
      onSelect(selected);
    }
  }, [selectedServiceId, services, onSelect]);

  const selectedService = useMemo(
    () => services.find((service) => service.service_id === selectedServiceId) ?? null,
    [services, selectedServiceId],
  );

  const handleStatusChange = (nextStatus: string | null) => {
    if (!selectedService) {
      return;
    }
    setSaveError(null);
    updateServiceStatus.mutate(
      {
        projectId,
        serviceId: selectedService.service_id,
        status: nextStatus,
        params: paramsStable,
      },
      {
        onError: (error) => {
          setSaveError(error.message || 'Failed to update service status.');
        },
      },
    );
  };

  const handleExecutionIntentChange = async (
    intent: 'planned' | 'optional' | 'not_proceeding',
    reason?: string | null
  ) => {
    if (!selectedService) {
      return;
    }
    await updateExecutionIntent.mutateAsync({
      serviceId: selectedService.service_id,
      intent,
      reason: reason || null,
    });
  };

  const isSaving =
    updateServiceStatus.isPending &&
    updateServiceStatus.variables?.serviceId === selectedService?.service_id;

  return (
    <Stack spacing={2}>
      {isError && (
        <Alert severity="error">
          Failed to load services.
        </Alert>
      )}
      <ListView<ProjectService>
        items={services}
        getItemId={(service) => service.service_id}
        getItemTestId={(service) => `${testIdPrefix}-service-row-${service.service_id}`}
        selectedId={selectedService?.service_id ?? null}
        onSelect={(service) => setSelectedServiceId(service.service_id)}
        renderPrimary={(service) => `${service.service_code} - ${service.service_name}`}
        renderSecondary={(service) =>
          [
            service.phase ? `Phase: ${service.phase}` : null,
            service.status ? `Status: ${formatServiceStatusLabel(service.status)}` : null,
            service.progress_pct != null ? `Progress: ${service.progress_pct}%` : null,
            service.agreed_fee != null ? `Fee: ${formatCurrency(service.agreed_fee)}` : null,
          ]
            .filter(Boolean)
            .join(' | ')
        }
        emptyState={
          <Typography color="text.secondary" sx={{ px: 2 }}>
            {isLoading ? 'Loading services...' : 'No services for this project yet.'}
          </Typography>
        }
      />
      <ProjectServiceDetails
        service={selectedService}
        onStatusChange={handleStatusChange}
        isSaving={isSaving}
        disabled={updateServiceStatus.isPending}
        saveError={saveError}
        testIdPrefix={testIdPrefix}
        extraDetails={
          renderExtraDetails ? (
            renderExtraDetails(selectedService)
          ) : (
            <ServicePlanningPanel
              service={selectedService}
              onExecutionIntentChange={handleExecutionIntentChange}
              isSaving={updateExecutionIntent.isPending}
              saveError={planningError}
            />
          )
        }
      />
    </Stack>
  );
}
