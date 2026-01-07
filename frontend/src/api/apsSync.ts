import apiClient from './client';
import type { 
  ApsHubsResponse, 
  ApsProjectsResponse, 
  ApsLoginInfo,
  ApsProjectDetails,
  ApsProjectFiles,
  ApsProjectIssues,
  ApsProjectUsers 
} from '@/types/apsSync';

export const apsSyncApi = {
  /** Retrieve the APS login URL exposed by the auth demo service */
  getLoginUrl: async (): Promise<ApsLoginInfo> => {
    const response = await apiClient.get<ApsLoginInfo>('/aps-sync/login-url');
    return response.data;
  },

  /** List hubs available to the currently authenticated APS user */
  getHubs: async (): Promise<ApsHubsResponse> => {
    const response = await apiClient.get<ApsHubsResponse>('/aps-sync/hubs');
    return response.data;
  },

  /** List projects for a given hub */
  getProjects: async (hubId: string): Promise<ApsProjectsResponse> => {
    const response = await apiClient.get<ApsProjectsResponse>(
      `/aps-sync/hubs/${encodeURIComponent(hubId)}/projects`
    );
    return response.data;
  },

  /** Get detailed project information including folders and files summary */
  getProjectDetails: async (hubId: string, projectId: string): Promise<ApsProjectDetails> => {
    const response = await apiClient.get<ApsProjectDetails>(
      `/aps-sync/hubs/${encodeURIComponent(hubId)}/projects/${encodeURIComponent(projectId)}/details`
    );
    return response.data;
  },

  /** Get project folders and model files */
  getProjectFolders: async (hubId: string, projectId: string): Promise<ApsProjectFiles> => {
    const response = await apiClient.get<ApsProjectFiles>(
      `/aps-sync/hubs/${encodeURIComponent(hubId)}/projects/${encodeURIComponent(projectId)}/folders`
    );
    return response.data;
  },

  /** Get project issues with optional filters */
  getProjectIssues: async (
    hubId: string,
    projectId: string,
    filters?: {
      status?: string;
      priority?: string;
      assigned_to?: string;
      page?: number;
      limit?: number;
    }
  ): Promise<ApsProjectIssues> => {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.priority) params.append('priority', filters.priority);
    if (filters?.assigned_to) params.append('assigned_to', filters.assigned_to);
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const queryString = params.toString();
    const url = `/aps-sync/hubs/${encodeURIComponent(hubId)}/projects/${encodeURIComponent(projectId)}/issues${queryString ? `?${queryString}` : ''}`;
    
    const response = await apiClient.get<ApsProjectIssues>(url);
    return response.data;
  },

  /** Get project users and team members */
  getProjectUsers: async (hubId: string, projectId: string): Promise<ApsProjectUsers> => {
    const response = await apiClient.get<ApsProjectUsers>(
      `/aps-sync/hubs/${encodeURIComponent(hubId)}/projects/${encodeURIComponent(projectId)}/users`
    );
    return response.data;
  },
};

