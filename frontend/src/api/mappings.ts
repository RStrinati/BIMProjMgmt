import apiClient from './client';

export type ReviztoProjectMapping = {
  revizto_project_uuid: string;
  pm_project_id: number | null;
  project_name_override?: string | null;
  is_active?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
  pm_project_name?: string | null;
};

export type IssueAttributeMapping = {
  map_id: number;
  project_id?: string | null;
  source_system: string;
  raw_attribute_name: string;
  mapped_field_name: string;
  data_type?: string | null;
  priority?: number | null;
  is_active?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

export const mappingsApi = {
  getReviztoProjectMappings: async (activeOnly = true): Promise<ReviztoProjectMapping[]> => {
    const response = await apiClient.get<ReviztoProjectMapping[]>('/mappings/revizto-projects', {
      params: { active_only: activeOnly },
    });
    return response.data;
  },
  upsertReviztoProjectMapping: async (
    payload: Pick<ReviztoProjectMapping, 'revizto_project_uuid' | 'pm_project_id' | 'project_name_override'>,
  ): Promise<void> => {
    await apiClient.post('/mappings/revizto-projects', payload);
  },
  deleteReviztoProjectMapping: async (revizto_project_uuid: string): Promise<void> => {
    await apiClient.delete(`/mappings/revizto-projects/${encodeURIComponent(revizto_project_uuid)}`);
  },
  getIssueAttributeMappings: async (activeOnly = true): Promise<IssueAttributeMapping[]> => {
    const response = await apiClient.get<IssueAttributeMapping[]>('/mappings/issue-attributes', {
      params: { active_only: activeOnly },
    });
    return response.data;
  },
  createIssueAttributeMapping: async (payload: Omit<IssueAttributeMapping, 'map_id'>): Promise<{ map_id: number }> => {
    const response = await apiClient.post<{ map_id: number }>('/mappings/issue-attributes', payload);
    return response.data;
  },
  updateIssueAttributeMapping: async (map_id: number, payload: Partial<IssueAttributeMapping>): Promise<void> => {
    await apiClient.patch(`/mappings/issue-attributes/${map_id}`, payload);
  },
  deleteIssueAttributeMapping: async (map_id: number): Promise<void> => {
    await apiClient.delete(`/mappings/issue-attributes/${map_id}`);
  },
};
