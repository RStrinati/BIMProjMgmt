import apiClient from './client';

export type ProjectResource = {
  resource_id: number;
  project_id: number;
  title: string;
  url: string;
  created_at?: string;
  updated_at?: string;
};

export const resourcesApi = {
  getAll: async (projectId: number): Promise<ProjectResource[]> => {
    const response = await apiClient.get<ProjectResource[]>(`/projects/${projectId}/resources`);
    return response.data;
  },

  create: async (projectId: number, payload: { title: string; url: string }): Promise<void> => {
    await apiClient.post(`/projects/${projectId}/resources`, payload);
  },

  update: async (
    resourceId: number,
    payload: { title?: string; url?: string },
  ): Promise<void> => {
    await apiClient.patch(`/resources/${resourceId}`, payload);
  },

  remove: async (resourceId: number): Promise<void> => {
    await apiClient.delete(`/resources/${resourceId}`);
  },
};
