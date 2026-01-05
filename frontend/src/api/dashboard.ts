import apiClient from './client';
import type {
  WarehouseDashboardMetrics,
  RevitHealthDashboardMetrics,
  NamingComplianceMetrics,
} from '@/types/api';

export const dashboardApi = {
  getWarehouseMetrics: async (options?: {
    projectIds?: number[];
    clientIds?: number[];
    typeIds?: number[];
  }): Promise<WarehouseDashboardMetrics> => {
    const params: Record<string, string> = {};
    if (options?.projectIds?.length) params.project_ids = options.projectIds.join(',');
    if (options?.clientIds?.length) params.client_ids = options.clientIds.join(',');
    if (options?.typeIds?.length) params.type_ids = options.typeIds.join(',');

    const response = await apiClient.get<WarehouseDashboardMetrics>('/dashboard/warehouse-metrics', {
      params: Object.keys(params).length ? params : undefined,
    });
    return response.data;
  },

  getIssuesHistory: async (options?: { projectIds?: number[] }) => {
    const params: Record<string, string> = {};
    if (options?.projectIds?.length) params.project_ids = options.projectIds.join(',');
    const response = await apiClient.get('/dashboard/issues-history', {
      params: Object.keys(params).length ? params : undefined,
    });
    return response.data as {
      week_start: string | null;
      status: string;
      count: number;
    }[];
  },

  getRevitHealthMetrics: async (options?: { projectIds?: number[]; discipline?: string }): Promise<RevitHealthDashboardMetrics> => {
    const params: Record<string, string> = {};
    if (options?.projectIds?.length) params.project_ids = options.projectIds.join(',');
    if (options?.discipline) params.discipline = options.discipline;
    const response = await apiClient.get<RevitHealthDashboardMetrics>('/dashboard/revit-health', {
      params: Object.keys(params).length ? params : undefined,
    });
    return response.data;
  },

  getNamingCompliance: async (options?: { projectIds?: number[]; discipline?: string }): Promise<NamingComplianceMetrics> => {
    const params: Record<string, string> = {};
    if (options?.projectIds?.length) params.project_ids = options.projectIds.join(',');
    if (options?.discipline) params.discipline = options.discipline;
    const response = await apiClient.get<NamingComplianceMetrics>('/dashboard/naming-compliance', {
      params: Object.keys(params).length ? params : undefined,
    });
    return response.data;
  },
};
