// Project Updates API functions

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
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append('limit', String(params.limit));
    if (params?.offset) searchParams.append('offset', String(params.offset));

    const queryString = searchParams.toString();
    const url = `/api/projects/${projectId}/updates${queryString ? `?${queryString}` : ''}`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error('Failed to fetch project updates');
    }
    return response.json();
  },

  // Create a new project update
  createProjectUpdate: async (
    projectId: number,
    body: string,
    createdBy?: number
  ): Promise<ProjectUpdate> => {
    const response = await fetch(`/api/projects/${projectId}/updates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body, created_by: createdBy }),
    });

    if (!response.ok) {
      throw new Error('Failed to create project update');
    }
    return response.json();
  },

  // Get a single update by ID
  getUpdate: async (updateId: number): Promise<ProjectUpdate> => {
    const response = await fetch(`/api/updates/${updateId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch update');
    }
    return response.json();
  },

  // Get comments for an update
  getUpdateComments: async (updateId: number): Promise<GetUpdateCommentsResponse> => {
    const response = await fetch(`/api/updates/${updateId}/comments`);
    if (!response.ok) {
      throw new Error('Failed to fetch update comments');
    }
    return response.json();
  },

  // Create a new comment on an update
  createUpdateComment: async (
    updateId: number,
    body: string,
    createdBy?: number
  ): Promise<UpdateComment> => {
    const response = await fetch(`/api/updates/${updateId}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body, created_by: createdBy }),
    });

    if (!response.ok) {
      throw new Error('Failed to create comment');
    }
    return response.json();
  },
};
