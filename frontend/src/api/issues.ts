// Issues API functions
export const issuesApi = {
  // Get overall issues overview for all projects
  getOverview: async () => {
    const response = await fetch('/api/issues/overview');
    if (!response.ok) {
      throw new Error('Failed to fetch issues overview');
    }
    return response.json();
  },

  // Get issues overview for a specific project
  getProjectOverview: async (projectId: number) => {
    const response = await fetch(`/api/projects/${projectId}/issues/overview`);
    if (!response.ok) {
      throw new Error('Failed to fetch project issues overview');
    }
    return response.json();
  },

  // Get paginated issues table from normalized vw_Issues_Reconciled
  getIssuesTable: async (params?: {
    project_id?: string;
    source_system?: 'ACC' | 'Revizto';
    status_normalized?: string;
    priority_normalized?: string;
    discipline_normalized?: string;
    assignee_user_key?: string;
    search?: string;
    page?: number;
    page_size?: number;
    sort_by?: string;
    sort_dir?: 'asc' | 'desc';
  }) => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
    }
    
    const queryString = searchParams.toString();
    const url = `/api/issues/table${queryString ? `?${queryString}` : ''}`;
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error('Failed to fetch issues table');
    }
    return response.json();
  },
};