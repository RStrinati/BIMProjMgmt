// Project Updates API functions

import apiClient from './client';

export type ProjectUpdate = {
  update_id: number;
  project_id: number;
  body: string;
  created_by: number | null;
  created_at: string;
  updated_at: string;
  created_by_name?: string;
  created_by_full_name?: string;
  comment_count?: number;
};

export type UpdateComment = {
  comment_id: number;
  update_id: number;
  body: string;
  created_by: number | null;
  created_at: string;
  updated_at: string;
  created_by_name?: string;
  created_by_full_name?: string;
};

export type GetProjectUpdatesResponse = {
  updates: ProjectUpdate[];
  count: number;
};

export type GetUpdateCommentsResponse = {
  comments: UpdateComment[];
  count: number;
};

export const updatesApi = {
  // Get project updates (newest first)
  getProjectUpdates: async (
    projectId: number,
    params?: { limit?: number; offset?: number }
  ): Promise<GetProjectUpdatesResponse> => {
    const response = await apiClient.get<GetProjectUpdatesResponse>(
      `/projects/${projectId}/updates`,
      { params },
    );
    return response.data;
  },

  // Create a new project update
  createProjectUpdate: async (
    projectId: number,
    body: string,
    createdBy?: number
  ): Promise<ProjectUpdate> => {
    const response = await apiClient.post<ProjectUpdate>(`/projects/${projectId}/updates`, {
      body,
      created_by: createdBy,
    });
    return response.data;
  },

  // Get a single update by ID
  getUpdate: async (updateId: number): Promise<ProjectUpdate> => {
    const response = await apiClient.get<ProjectUpdate>(`/updates/${updateId}`);
    return response.data;
  },

  // Get comments for an update
  getUpdateComments: async (updateId: number): Promise<GetUpdateCommentsResponse> => {
    const response = await apiClient.get<GetUpdateCommentsResponse>(`/updates/${updateId}/comments`);
    return response.data;
  },

  // Create a new comment on an update
  createUpdateComment: async (
    updateId: number,
    body: string,
    createdBy?: number
  ): Promise<UpdateComment> => {
    const response = await apiClient.post<UpdateComment>(`/updates/${updateId}/comments`, {
      body,
      created_by: createdBy,
    });
    return response.data;
  },
};
