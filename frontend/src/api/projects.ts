import apiClient from './client';
import type {
  Project,
  ProjectFilters,
  DashboardTimelineResponse,
  ProjectFinanceGrid,
  ProjectFinanceSummary,
  ProjectSummary,
  ProjectAggregates,
  FinanceLineItemsResponse,
  FinanceReconciliationResponse,
  ProjectsFinanceSummaryResponse,
} from '@/types/api';

export const projectsApi = {
  // Get all projects
  getAll: async (filters?: ProjectFilters): Promise<Project[]> => {
    const response = await apiClient.get<Project[]>('/projects', { params: filters });
    return response.data;
  },

  // Get all projects with health metrics
  getAllWithHealth: async (): Promise<Project[]> => {
    const response = await apiClient.get<Project[]>('/projects/overview');
    return response.data;
  },

  // Get projects summary for V2 list/board
  getSummary: async (params?: {
    viewId?: string;
    searchTerm?: string;
    currentUserId?: number | null;
  }): Promise<ProjectSummary[]> => {
    const response = await apiClient.get<ProjectSummary[]>('/projects/summary', {
      params: {
        viewId: params?.viewId,
        searchTerm: params?.searchTerm,
        current_user_id: params?.currentUserId ?? undefined,
      },
    });
    return response.data;
  },

  // Get aggregates for V2 list footer
  getAggregates: async (params?: {
    viewId?: string;
    searchTerm?: string;
    currentUserId?: number | null;
  }): Promise<ProjectAggregates> => {
    const response = await apiClient.get<ProjectAggregates>('/projects/aggregates', {
      params: {
        viewId: params?.viewId,
        searchTerm: params?.searchTerm,
        current_user_id: params?.currentUserId ?? undefined,
      },
    });
    return response.data;
  },

  // Get project by ID
  getById: async (id: number): Promise<Project> => {
    const response = await apiClient.get<Project>(`/projects/${id}`);
    return response.data;
  },

  // Create new project
  create: async (project: Partial<Project>): Promise<Project> => {
    const response = await apiClient.post<Project>('/projects', project);
    return response.data;
  },

  // Update project
  update: async (id: number, project: Partial<Project>): Promise<Project> => {
    const response = await apiClient.put<Project>(`/projects/${id}`, project);
    return response.data;
  },

  // Patch project (partial update)
  patch: async (id: number, patch: Partial<Project>): Promise<{ success: boolean }> => {
    const response = await apiClient.patch<{ success: boolean }>(`/projects/${id}`, patch);
    return response.data;
  },

  // Delete project
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/projects/${id}`);
  },

  // Get project statistics
  getStats: async (options?: { projectIds?: number[] }): Promise<{
    total: number;
    active: number;
    completed: number;
    on_hold: number;
  }> => {
    const response = await apiClient.get('/projects/stats', {
      params: options?.projectIds?.length ? { project_ids: options.projectIds.join(',') } : undefined,
    });
    return response.data;
  },

  // Get review statistics for all projects
  getReviewStats: async (options?: { projectIds?: number[] }): Promise<Record<number, {
    total_reviews: number;
    completed_reviews: number;
    planned_reviews: number;
    in_progress_reviews: number;
    overdue_reviews: number;
    earliest_review_date: string | null;
    latest_review_date: string | null;
    upcoming_reviews_30_days: number;
  }>> => {
    const response = await apiClient.get('/project_review_statistics', {
      params: options?.projectIds?.length ? { project_ids: options.projectIds.join(',') } : undefined,
    });
    return response.data;
  },

  // Get timeline data for dashboard
  getTimeline: async (options?: {
    months?: number;
    projectIds?: number[];
    clientIds?: number[];
    typeIds?: number[];
    manager?: string;
  }): Promise<DashboardTimelineResponse> => {
    const params: Record<string, string> = {};
    if (options?.months != null) params.months = String(options.months);
    if (options?.projectIds?.length) params.project_ids = options.projectIds.join(',');
    if (options?.clientIds?.length) params.client_ids = options.clientIds.join(',');
    if (options?.typeIds?.length) params.type_ids = options.typeIds.join(',');
    if (options?.manager) params.manager = options.manager;
    const response = await apiClient.get<DashboardTimelineResponse>('/dashboard/timeline', {
      params: Object.keys(params).length ? params : undefined,
    });
    return response.data;
  },

  getFinanceGrid: async (projectId: number): Promise<ProjectFinanceGrid> => {
    const response = await apiClient.get<ProjectFinanceGrid>('/projects/finance_grid', {
      params: { project_id: projectId },
    });
    return response.data;
  },

  getFinanceSummary: async (projectId: number): Promise<ProjectFinanceSummary> => {
    const response = await apiClient.get<ProjectFinanceSummary>(`/projects/${projectId}/finance-summary`);
    return response.data;
  },

  getFinanceLineItems: async (
    projectId: number,
    options?: { serviceId?: number; invoiceStatus?: string }
  ): Promise<FinanceLineItemsResponse> => {
    const response = await apiClient.get<FinanceLineItemsResponse>(`/projects/${projectId}/finance/line-items`, {
      params: {
        service_id: options?.serviceId,
        invoice_status: options?.invoiceStatus,
      },
    });
    return response.data;
  },

  getFinanceReconciliation: async (projectId: number): Promise<FinanceReconciliationResponse> => {
    const response = await apiClient.get<FinanceReconciliationResponse>(`/projects/${projectId}/finance/reconciliation`);
    return response.data;
  },

  // Get batch finance summary for all projects (deterministic fee model)
  getProjectsFinanceSummary: async (options?: { status?: string }): Promise<ProjectsFinanceSummaryResponse> => {
    const response = await apiClient.get<ProjectsFinanceSummaryResponse>('/projects/finance/summary', {
      params: options?.status ? { status: options.status } : undefined,
    });
    return response.data;
  },
};
