import apiClient from './client';
import type {
  WarehouseDashboardMetrics,
  RevitHealthDashboardMetrics,
  NamingComplianceMetrics,
  DashboardIssuesKpis,
  DashboardIssuesCharts,
  DashboardIssuesTable,
  CoordinateAlignmentDashboard,
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
      timeout: 30000,
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

  getIssuesKpis: async (options?: { projectIds?: number[] }): Promise<DashboardIssuesKpis> => {
    const params: Record<string, string> = {};
    if (options?.projectIds?.length) params.project_ids = options.projectIds.join(',');
    const response = await apiClient.get<DashboardIssuesKpis>('/dashboard/issues-kpis', {
      params: Object.keys(params).length ? params : undefined,
    });
    return response.data;
  },

  getIssuesCharts: async (options?: { projectIds?: number[] }): Promise<DashboardIssuesCharts> => {
    const params: Record<string, string> = {};
    if (options?.projectIds?.length) params.project_ids = options.projectIds.join(',');
    const response = await apiClient.get<DashboardIssuesCharts>('/dashboard/issues-charts', {
      params: Object.keys(params).length ? params : undefined,
    });
    return response.data;
  },

  getIssuesTable: async (options?: {
    projectIds?: number[];
    status?: string;
    priority?: string;
    discipline?: string;
    zone?: string;
    page?: number;
    pageSize?: number;
    sortBy?: string;
    sortDir?: 'asc' | 'desc';
  }): Promise<DashboardIssuesTable> => {
    const params: Record<string, string> = {};
    if (options?.projectIds?.length) params.project_ids = options.projectIds.join(',');
    if (options?.status) params.status = options.status;
    if (options?.priority) params.priority = options.priority;
    if (options?.discipline) params.discipline = options.discipline;
    if (options?.zone) params.zone = options.zone;
    if (options?.page) params.page = String(options.page);
    if (options?.pageSize) params.page_size = String(options.pageSize);
    if (options?.sortBy) params.sort_by = options.sortBy;
    if (options?.sortDir) params.sort_dir = options.sortDir;

    const response = await apiClient.get<DashboardIssuesTable>('/dashboard/issues-table', {
      params: Object.keys(params).length ? params : undefined,
    });
    return response.data;
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

  getCoordinateAlignment: async (options?: {
    projectIds?: number[];
    discipline?: string;
    page?: number;
    pageSize?: number;
    sortBy?: string;
    sortDir?: 'asc' | 'desc';
  }): Promise<CoordinateAlignmentDashboard> => {
    const params: Record<string, string> = {};
    if (options?.projectIds?.length) params.project_ids = options.projectIds.join(',');
    if (options?.discipline) params.discipline = options.discipline;
    if (options?.page) params.page = String(options.page);
    if (options?.pageSize) params.page_size = String(options.pageSize);
    if (options?.sortBy) params.sort_by = options.sortBy;
    if (options?.sortDir) params.sort_dir = options.sortDir;

    const response = await apiClient.get<CoordinateAlignmentDashboard>('/dashboard/coordinate-alignment', {
      params: Object.keys(params).length ? params : undefined,
      timeout: 30000,
    });
    return response.data;
  },
};
