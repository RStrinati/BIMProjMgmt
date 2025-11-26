import apiClient from './client';
import type { ApsHubsResponse, ApsProjectsResponse, ApsLoginInfo } from '@/types/apsSync';

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
};
