import { useMutation, useQueryClient } from '@tanstack/react-query';
import { projectServicesApi, type ProjectService, type ProjectServicesListResponse } from '@/api/services';
import { toApiServiceStatus } from '@/utils/serviceStatus';

const updateServiceList = (
  data: ProjectServicesListResponse | undefined,
  serviceId: number,
  patch: Partial<ProjectService>,
): ProjectServicesListResponse | undefined => {
  if (!data) {
    return data;
  }

  const updateArray = (items: ProjectService[]) =>
    items.map((service) => (service.service_id === serviceId ? { ...service, ...patch } : service));

  if (Array.isArray(data)) {
    return updateArray(data);
  }

  const next = { ...data } as Record<string, unknown>;
  const keys = ['items', 'services', 'results'] as const;
  keys.forEach((key) => {
    const value = data[key];
    if (Array.isArray(value)) {
      next[key] = updateArray(value);
    }
  });

  return next as ProjectServicesListResponse;
};

type UpdateServiceStatusArgs = {
  projectId: number;
  serviceId: number;
  status: string | null;
  params?: Record<string, unknown>;
};

type UpdateServiceStatusResult = Awaited<ReturnType<typeof projectServicesApi.update>>;

type UpdateServiceStatusContext = {
  previousServiceLists?: Array<[unknown, ProjectServicesListResponse | undefined]>;
};

export function useUpdateServiceStatus() {
  const queryClient = useQueryClient();

  return useMutation<UpdateServiceStatusResult, Error, UpdateServiceStatusArgs, UpdateServiceStatusContext>({
    mutationFn: ({ projectId, serviceId, status }) =>
      projectServicesApi.update(projectId, serviceId, { status: toApiServiceStatus(status) }),
    onMutate: async ({ projectId, serviceId, status }) => {
      const nextStatus = toApiServiceStatus(status);
      await queryClient.cancelQueries({ queryKey: ['projectServices', projectId] });

      const previousServiceLists = queryClient.getQueriesData<ProjectServicesListResponse>({
        queryKey: ['projectServices', projectId],
      });

      queryClient.setQueriesData<ProjectServicesListResponse>(
        { queryKey: ['projectServices', projectId] },
        (existing) => updateServiceList(existing, serviceId, { status: nextStatus }),
      );

      return { previousServiceLists };
    },
    onError: (_err, _vars, context) => {
      if (context?.previousServiceLists) {
        context.previousServiceLists.forEach(([key, data]) => {
          queryClient.setQueryData(key, data);
        });
      }
    },
    onSettled: (_data, _error, { projectId, params }) => {
      if (params) {
        queryClient.invalidateQueries({ queryKey: ['projectServices', projectId, params] });
      }
      queryClient.invalidateQueries({ queryKey: ['projectServices', projectId] });
    },
  });
}
